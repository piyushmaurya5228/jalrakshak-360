"""Fetch ERA5-based rainfall features for JalRakshak 360 sample locations."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
SAMPLE_FILE = Path("data/sample/water_risk_sample.csv")
RAW_DIR = Path("data/raw")
OUTPUT_FILE = Path("data/processed/rainfall_features.csv")

NORMAL_START_YEAR = 1991
NORMAL_END_YEAR = 2020
IST = timezone(timedelta(hours=5, minutes=30))


def parse_locations(data, expected_count):
    """Normalize Open-Meteo's single/multiple-location response."""
    if isinstance(data, dict) and expected_count == 1:
        return [data]

    if isinstance(data, list) and len(data) == expected_count:
        return data

    raise ValueError(
        f"Unexpected response format: expected {expected_count} locations."
    )


def get_daily_data(response_item):
    """Return daily date/value pairs from one API location result."""
    daily = response_item.get("daily", {})
    dates = daily.get("time", [])
    values = daily.get("precipitation_sum", [])

    if not dates or len(dates) != len(values):
        raise ValueError("Missing or mismatched daily rainfall records.")

    return dict(zip(dates, values))


def request_rainfall(latitudes, longitudes, start_date, end_date):
    """Retrieve ERA5 daily precipitation for one or more coordinates."""
    params = {
        "latitude": ",".join(str(x) for x in latitudes),
        "longitude": ",".join(str(x) for x in longitudes),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
        "models": "era5",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=(10, 120),
    )
    response.raise_for_status()

    data = response.json()
    return parse_locations(data, len(latitudes)), response.url


def complete_window_total(daily_values, window_start):
    """Return a 7-day sum, or None if any daily value is unavailable."""
    days = [
        (window_start + timedelta(days=i)).isoformat()
        for i in range(7)
    ]
    values = [daily_values.get(day) for day in days]

    if any(value is None for value in values):
        return None

    return sum(float(value) for value in values)


def main():
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {SAMPLE_FILE}")

    locations = pd.read_csv(SAMPLE_FILE)

    required = {
        "location_id", "state", "district", "village",
        "latitude", "longitude",
    }
    missing = required - set(locations.columns)

    if missing:
        raise ValueError(f"Input file is missing columns: {sorted(missing)}")

    if locations.empty:
        raise ValueError("No locations found in the sample dataset.")

    if locations[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Some locations have missing coordinates.")

    today = datetime.now(IST).date()
    window_end = today - timedelta(days=7)
    window_start = window_end - timedelta(days=6)

    latitudes = locations["latitude"].astype(float).tolist()
    longitudes = locations["longitude"].astype(float).tolist()

    print("Locations:", len(locations))
    print("Source: Open-Meteo Historical Weather API")
    print("Model: ERA5 reanalysis")
    print("Recent window:", window_start, "to", window_end)
    print(
        "Normal period:",
        f"{NORMAL_START_YEAR}-{NORMAL_END_YEAR}",
    )

    # Fetch the recent 7-day window for all locations.
    recent_results, recent_url = request_rainfall(
        latitudes,
        longitudes,
        window_start,
        window_end,
    )

    # Fetch daily rainfall for the 30-year baseline in one batch.
    normal_results, normal_url = request_rainfall(
        latitudes,
        longitudes,
        date(NORMAL_START_YEAR, 1, 1),
        date(NORMAL_END_YEAR, 12, 31),
    )

    output_rows = []

    for index, (_, location) in enumerate(locations.iterrows()):
        recent = recent_results[index]
        historical = normal_results[index]

        recent_daily = get_daily_data(recent)
        historical_daily = get_daily_data(historical)

        rainfall_7d = complete_window_total(
            recent_daily,
            window_start,
        )

        if rainfall_7d is None:
            raise ValueError(
                f"Incomplete recent rainfall window for "
                f"{location['location_id']}."
            )

        annual_totals = []

        for year in range(NORMAL_START_YEAR, NORMAL_END_YEAR + 1):
            try:
                annual_start = date(
                    year,
                    window_start.month,
                    window_start.day,
                )
            except ValueError:
                # For a Feb 29 window, skip non-leap years.
                continue

            annual_total = complete_window_total(
                historical_daily,
                annual_start,
            )

            if annual_total is not None:
                annual_totals.append(annual_total)

        if not annual_totals:
            raise ValueError(
                f"No valid historical baseline for {location['location_id']}."
            )

        rainfall_normal = sum(annual_totals) / len(annual_totals)

        output_rows.append({
            "location_id": location["location_id"],
            "state": location["state"],
            "district": location["district"],
            "village": location["village"],
            "latitude": float(location["latitude"]),
            "longitude": float(location["longitude"]),
            "rainfall_7d": round(rainfall_7d, 3),
            "rainfall_normal": round(rainfall_normal, 3),
            "rainfall_window_start": window_start.isoformat(),
            "rainfall_window_end": window_end.isoformat(),
            "normal_start_year": NORMAL_START_YEAR,
            "normal_end_year": NORMAL_END_YEAR,
            "valid_baseline_years": len(annual_totals),
            "weather_grid_latitude": recent.get("latitude"),
            "weather_grid_longitude": recent.get("longitude"),
            "rainfall_source": "Open-Meteo Historical Weather API",
            "weather_model": "ERA5",
            "retrieved_at_ist": datetime.now(IST).isoformat(),
        })

    output = pd.DataFrame(output_rows)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    (RAW_DIR / "open_meteo_rainfall_recent.json").write_text(
        json.dumps({
            "source": "Open-Meteo Historical Weather API",
            "model": "ERA5",
            "request_url": recent_url,
            "response": recent_results,
        }, indent=2),
        encoding="utf-8",
    )

    (RAW_DIR / "open_meteo_rainfall_normal_1991_2020.json").write_text(
        json.dumps({
            "source": "Open-Meteo Historical Weather API",
            "model": "ERA5",
            "request_url": normal_url,
            "response": normal_results,
        }, indent=2),
        encoding="utf-8",
    )

    output.to_csv(OUTPUT_FILE, index=False)

    print("\nRainfall fetch successful.")
    print("Rows saved:", len(output))
    print("Output:", OUTPUT_FILE)
    print("7-day rainfall column: rainfall_7d (mm)")
    print("Baseline column: rainfall_normal (mm)")
    print("\nPreview:")
    print(
        output[
            [
                "location_id",
                "district",
                "rainfall_7d",
                "rainfall_normal",
                "valid_baseline_years",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", type(exc).__name__, str(exc))
        raise
