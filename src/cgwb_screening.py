import math
import pandas as pd


BIS_LIMITS = {
    "tds": ("Total Dissolved Solids (mg/L)", 500, 2000),
    "chloride": ("Chloride (mg/L)", 250, 1000),
    "sulphate": ("Sulphate (mg/L)", 200, 400),
    "hardness": ("Total Hardness (mgCaCO3/L)", 200, 600),
}

PH_COLUMN = "Potential of Hydrogen (pH)"


def classify_parameter(value, acceptable, permissible):
    if pd.isna(value):
        return "MISSING"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "INVALID_VALUE"

    if not math.isfinite(number):
        return "INVALID_VALUE"
    if number < 0:
        return "INVALID_NEGATIVE"
    if number == 0:
        return "ZERO_REVIEW"
    if number <= acceptable:
        return "WITHIN_ACCEPTABLE"
    if number <= permissible:
        return "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE"

    return "ABOVE_PERMISSIBLE"


def classify_ph(value):
    if pd.isna(value):
        return "MISSING"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "INVALID_VALUE"

    if not math.isfinite(number):
        return "INVALID_VALUE"
    if number < 0:
        return "INVALID_NEGATIVE"
    if number == 0:
        return "ZERO_REVIEW"
    if number < 6.5:
        return "BELOW_REFERENCE_RANGE"
    if number > 8.5:
        return "ABOVE_REFERENCE_RANGE"

    return "WITHIN_REFERENCE_RANGE"


def screen_cgwb_records(df):
    result = df.copy()

    required = [PH_COLUMN] + [
        item[0] for item in BIS_LIMITS.values()
    ]

    missing = set(required) - set(result.columns)
    if missing:
        raise ValueError(f"Missing parameter columns: {sorted(missing)}")

    for name, (column, acceptable, permissible) in BIS_LIMITS.items():
        result[f"{name}_screening_status"] = (
            pd.to_numeric(result[column], errors="coerce")
            .map(
                lambda value: classify_parameter(
                    value, acceptable, permissible
                )
            )
        )

    result["ph_screening_status"] = (
        pd.to_numeric(result[PH_COLUMN], errors="coerce")
        .map(classify_ph)
    )

    result["screening_reference"] = "BIS IS 10500:2012"
    result["screening_usage"] = "HISTORICAL_REFERENCE_ONLY"

    return result
