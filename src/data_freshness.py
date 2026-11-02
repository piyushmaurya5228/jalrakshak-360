"""JalRakshak 360 data-source freshness monitoring."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


IST = ZoneInfo("Asia/Kolkata")


def _parse_ist(value):
    """Parse a timestamp and normalize it to Indian Standard Time."""
    if value is None:
        return None

    timestamp = pd.to_datetime(value, errors="coerce")

    if pd.isna(timestamp):
        return None

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(IST)
    else:
        timestamp = timestamp.tz_convert(IST)

    return timestamp.to_pydatetime()


def assess_retrieval_timestamp(
    retrieved_at,
    max_age_days=None,
    now=None,
):
    """Assess timestamp availability and age against an optional threshold."""

    fetched = _parse_ist(retrieved_at)
    current = _parse_ist(now) if now is not None else datetime.now(IST)

    if fetched is None:
        return {
            "status": "UNKNOWN",
            "retrieved_at_ist": None,
            "age_days": None,
        }

    age_days = (current - fetched).total_seconds() / 86400

    if age_days < 0:
        status = "INVALID_FUTURE_TIMESTAMP"
    elif max_age_days is None:
        status = "TIMESTAMP_RECORDED"
    elif age_days > max_age_days:
        status = "STALE"
    else:
        status = "RECENT"

    return {
        "status": status,
        "retrieved_at_ist": fetched.isoformat(),
        "age_days": round(max(0, age_days), 2),
    }


def build_data_freshness_report(
    rainfall_df,
    wqmis_metadata_path,
    now=None,
    rainfall_max_age_days=7,
    observation_max_age_days=14,
):
    """Build separate freshness records for rainfall and WQ6."""

    rows = []

    # Rainfall retrieval timestamp
    rainfall_timestamp = None

    if "retrieved_at_ist" in rainfall_df.columns:
        timestamps = pd.to_datetime(
            rainfall_df["retrieved_at_ist"],
            errors="coerce",
            utc=True,
        ).dropna()

        if not timestamps.empty:
            rainfall_timestamp = (
                timestamps.max().tz_convert(IST)
            )

    rainfall = assess_retrieval_timestamp(
        rainfall_timestamp,
        max_age_days=rainfall_max_age_days,
        now=now,
    )

    observation_date = None
    observation_age = None

    if "rainfall_window_end" in rainfall_df.columns:
        dates = pd.to_datetime(
            rainfall_df["rainfall_window_end"],
            errors="coerce",
        ).dropna()

        if not dates.empty:
            observation_date = dates.max().date().isoformat()

            parsed_observation = _parse_ist(observation_date)
            current = (
                _parse_ist(now)
                if now is not None
                else datetime.now(IST)
            )

            observation_age = round(
                max(
                    0,
                    (current - parsed_observation).total_seconds()
                    / 86400,
                ),
                2,
            )

    if observation_age is None:
        observation_status = "UNKNOWN"
    elif observation_age > observation_max_age_days:
        observation_status = "STALE"
    elif observation_age >= observation_max_age_days * 0.85:
        observation_status = "NEAR_LIMIT"
    else:
        observation_status = "RECENT"

    rows.append({
        "source": "Rainfall (ERA5)",
        "status": rainfall["status"],
        "retrieved_at_ist": rainfall["retrieved_at_ist"],
        "age_days": rainfall["age_days"],
        "latest_observation_date": observation_date,
        "observation_age_days": observation_age,
        "observation_status": observation_status,
        "detail": (
            f"Retrieval threshold: {rainfall_max_age_days} days. "
            f"Observation threshold: {observation_max_age_days} days."
        ),
    })

    # WQ6 retrieval metadata
    metadata_path = Path(wqmis_metadata_path)
    metadata = {}

    if metadata_path.exists():
        try:
            metadata = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            metadata = {}

    wqmis = assess_retrieval_timestamp(
        metadata.get("fetched_at_ist"),
        max_age_days=None,
        now=now,
    )

    rows.append({
        "source": "JJM/WQMIS WQ6",
        "status": wqmis["status"],
        "retrieved_at_ist": wqmis["retrieved_at_ist"],
        "age_days": wqmis["age_days"],
        "latest_observation_date": None,
        "observation_age_days": None,
        "observation_status": "NOT_APPLICABLE",
        "detail": (
            f"Financial year: {metadata.get('financial_year', 'Unknown')}. "
            "Refresh cadence not configured; age is informational."
            if metadata
            else "Verified retrieval timestamp unavailable. "
                 "Next successful WQ6 refresh will create metadata."
        ),
    })

    return pd.DataFrame(rows)
