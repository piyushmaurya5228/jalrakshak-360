"""Validation of inputs required by the live risk-scoring pipeline."""

import numpy as np
import pandas as pd


REQUIRED_SCORING_COLUMNS = [
    "population",
    "water_contamination_rate",
    "rainfall_7d",
    "rainfall_normal",
    "groundwater_stress",
    "previous_contamination",
    "water_tests",
    "contaminated_tests",
]


def validate_scoring_inputs(df):
    """Reject incomplete or invalid inputs before calculating risk scores.

    This is deliberately separate from the broader source-metadata audit:
    missing provenance can be reported as a warning, but invalid scoring
    values must never be silently converted into risk scores.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Scoring input must be a non-empty DataFrame.")

    missing = [column for column in REQUIRED_SCORING_COLUMNS
               if column not in df.columns]
    if missing:
        raise ValueError(f"Scoring input is missing required columns: {missing}")

    numeric = {}
    invalid = []
    for column in REQUIRED_SCORING_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            invalid.append(column)
        numeric[column] = values

    if invalid:
        raise ValueError(
            "Scoring inputs must contain finite numeric values. "
            f"Invalid columns: {invalid}"
        )

    bounded_rates = [
        "water_contamination_rate",
        "groundwater_stress",
        "previous_contamination",
    ]
    out_of_range = [
        column for column in bounded_rates
        if not numeric[column].between(0, 1).all()
    ]
    if out_of_range:
        raise ValueError(
            "Normalized scoring rates must be between 0 and 1. "
            f"Invalid columns: {out_of_range}"
        )

    if (numeric["population"] < 0).any():
        raise ValueError("Population values must be non-negative.")

    if (numeric["rainfall_7d"] < 0).any():
        raise ValueError("Seven-day rainfall values must be non-negative.")

    if (numeric["rainfall_normal"] <= 0).any():
        raise ValueError("Normal rainfall baseline must be greater than zero.")

    # Historical contamination is a weighted risk component. Do not treat
    # the absence of tests as evidence of zero historical contamination.
    if (numeric["water_tests"] <= 0).any():
        raise ValueError(
            "Every scored location must have at least one water test; "
            "missing historical evidence cannot be scored as zero risk."
        )

    invalid_counts = (
        (numeric["contaminated_tests"] < 0)
        | (numeric["contaminated_tests"] > numeric["water_tests"])
    )
    if invalid_counts.any():
        raise ValueError(
            "Contaminated test counts must be between zero and total tests."
        )
