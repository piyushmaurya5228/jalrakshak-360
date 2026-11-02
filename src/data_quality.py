"""JalRakshak 360 dataset quality validation."""

import math
import pandas as pd


REQUIRED_COLUMNS = [
    "location_id", "state", "district", "village",
    "latitude", "longitude", "population",
    "water_contamination_rate", "groundwater_stress",
    "previous_contamination", "water_tests",
    "contaminated_tests", "rainfall_7d", "rainfall_normal",
    "rainfall_window_start", "rainfall_window_end",
    "normal_start_year", "normal_end_year",
    "valid_baseline_years", "weather_grid_latitude",
    "weather_grid_longitude", "rainfall_source",
    "weather_model", "retrieved_at_ist",
]

NUMERIC_COLUMNS = [
    "location_id", "latitude", "longitude", "population",
    "water_contamination_rate", "fluoride_level",
    "nitrate_level", "iron_level",
    "rainfall_7d_original_sample",
    "rainfall_normal_original_sample",
    "groundwater_stress", "previous_contamination",
    "water_tests", "contaminated_tests",
    "rainfall_7d", "rainfall_normal",
    "normal_start_year", "normal_end_year",
    "valid_baseline_years",
    "weather_grid_latitude", "weather_grid_longitude",
]

RATE_COLUMNS = [
    "water_contamination_rate",
    "groundwater_stress",
    "previous_contamination",
]

RAINFALL_COLUMNS = [
    "rainfall_7d",
    "rainfall_normal",
    "rainfall_7d_original_sample",
    "rainfall_normal_original_sample",
]


def _numeric(df, column):
    """Convert a column to numeric values for validation."""
    return pd.to_numeric(df[column], errors="coerce")


def _finite(series):
    """Check that all values are finite numbers."""
    values = pd.to_numeric(series, errors="coerce")

    return bool(
        values.notna().all()
        and values.map(lambda value: math.isfinite(float(value))).all()
    )


def validate_dataset(df):
    """Return a DataFrame containing dataset validation results."""

    checks = []

    def add(name, passed, details):
        checks.append({
            "check": name,
            "passed": bool(passed),
            "details": str(details),
        })

    add(
        "Dataset is non-empty",
        not df.empty,
        f"{len(df)} records found",
    )

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    add(
        "Required columns present",
        len(missing_columns) == 0,
        f"Missing columns: {missing_columns}"
        if missing_columns else "All required columns are present",
    )

    if df.empty or missing_columns:
        return pd.DataFrame(checks)

    missing_values = int(df.isna().sum().sum())

    add(
        "No missing values",
        missing_values == 0,
        f"{missing_values} missing cells",
    )

    duplicate_rows = int(df.duplicated().sum())

    add(
        "No duplicate rows",
        duplicate_rows == 0,
        f"{duplicate_rows} duplicate rows",
    )

    unique_ids = df["location_id"].is_unique

    add(
        "Unique location IDs",
        unique_ids,
        f"{df['location_id'].nunique()} unique IDs",
    )

    village_names = df["village"].astype(str).str.strip().str.casefold()

    add(
        "Unique non-empty village names",
        bool(village_names.ne("").all() and village_names.is_unique),
        f"{village_names.nunique()} unique names",
    )

    text_columns = [
        "state", "district", "rainfall_source", "weather_model",
    ]

    blank_metadata = sum(
        int(df[column].astype(str).str.strip().eq("").sum())
        for column in text_columns
    )

    add(
        "Non-empty source metadata",
        blank_metadata == 0,
        f"{blank_metadata} blank metadata cells",
    )

    numeric_missing = [
        column for column in NUMERIC_COLUMNS
        if column not in df.columns
    ]

    invalid_numeric = [
        column for column in NUMERIC_COLUMNS
        if column in df.columns and not _finite(df[column])
    ]

    add(
        "Numeric values are finite",
        not numeric_missing and not invalid_numeric,
        f"Invalid columns: {invalid_numeric + numeric_missing}",
    )

    latitude_ok = (
        _numeric(df, "latitude").between(-90, 90).all()
    )
    longitude_ok = (
        _numeric(df, "longitude").between(-180, 180).all()
    )

    add(
        "Valid location coordinates",
        latitude_ok and longitude_ok,
        "Latitude and longitude within geographic bounds",
    )

    grid_latitude_ok = (
        _numeric(df, "weather_grid_latitude").between(-90, 90).all()
    )
    grid_longitude_ok = (
        _numeric(df, "weather_grid_longitude").between(-180, 180).all()
    )

    add(
        "Valid weather-grid coordinates",
        grid_latitude_ok and grid_longitude_ok,
        "Weather-grid coordinates within geographic bounds",
    )

    add(
        "Positive population",
        (_numeric(df, "population") > 0).all(),
        "Population must be greater than zero",
    )

    rates_valid = all(
        _numeric(df, column).between(0, 1).all()
        for column in RATE_COLUMNS
    )

    add(
        "Normalized risk rates within 0-1",
        rates_valid,
        "Water contamination, groundwater stress and previous contamination",
    )

    tests_nonnegative = (_numeric(df, "water_tests") >= 0).all()

    add(
        "Non-negative water tests",
        tests_nonnegative,
        "Water test counts must be non-negative",
    )

    counts_valid = (
        (_numeric(df, "contaminated_tests") >= 0)
        & (
            _numeric(df, "contaminated_tests")
            <= _numeric(df, "water_tests")
        )
    ).all()

    add(
        "Contaminated tests do not exceed total tests",
        counts_valid,
        "Contaminated tests must be between zero and total tests",
    )

    rainfall_valid = all(
        (_numeric(df, column) >= 0).all()
        for column in RAINFALL_COLUMNS
    )

    add(
        "Non-negative rainfall",
        rainfall_valid,
        "Rainfall values must be non-negative",
    )

    add(
        "Positive rainfall baseline",
        (_numeric(df, "rainfall_normal") > 0).all(),
        "Normal rainfall must be greater than zero",
    )

    baseline_valid = (
        (_numeric(df, "normal_start_year") > 0)
        & (
            _numeric(df, "normal_end_year")
            >= _numeric(df, "normal_start_year")
        )
        & (
            _numeric(df, "valid_baseline_years")
            ==
            _numeric(df, "normal_end_year")
            - _numeric(df, "normal_start_year") + 1
        )
    ).all()

    add(
        "Valid rainfall baseline years",
        baseline_valid,
        "Baseline year count must match the inclusive year range",
    )

    start_dates = pd.to_datetime(
        df["rainfall_window_start"], errors="coerce", utc=True
    )
    end_dates = pd.to_datetime(
        df["rainfall_window_end"], errors="coerce", utc=True
    )
    retrieval_dates = pd.to_datetime(
        df["retrieved_at_ist"], errors="coerce", utc=True
    )

    add(
        "Valid rainfall window start dates",
        start_dates.notna().all(),
        f"{int(start_dates.isna().sum())} invalid dates",
    )

    add(
        "Valid rainfall window end dates",
        end_dates.notna().all(),
        f"{int(end_dates.isna().sum())} invalid dates",
    )

    add(
        "Valid retrieval timestamps",
        retrieval_dates.notna().all(),
        f"{int(retrieval_dates.isna().sum())} invalid timestamps",
    )

    add(
        "Rainfall window dates are ordered",
        (start_dates <= end_dates).all(),
        "Window start must not exceed window end",
    )

    return pd.DataFrame(checks)
