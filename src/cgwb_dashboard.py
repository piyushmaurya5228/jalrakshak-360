import pandas as pd

from src.cgwb_screening import (
    BIS_LIMITS,
    classify_parameter,
    classify_ph,
)


PARAMETER_COLUMNS = {
    "ph": ("ph_latest_value", "ph_sample_date"),
    "tds": ("tds_latest_value", "tds_sample_date"),
    "chloride": ("chloride_latest_value", "chloride_sample_date"),
    "sulphate": ("sulphate_latest_value", "sulphate_sample_date"),
    "hardness": ("hardness_latest_value", "hardness_sample_date"),
}

STATUS_LABELS = {
    "WITHIN_ACCEPTABLE": "Within acceptable limit",
    "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE": (
        "Above acceptable; within permissible"
    ),
    "ABOVE_PERMISSIBLE": "Above permissible limit",
    "WITHIN_REFERENCE_RANGE": "Within pH reference range",
    "BELOW_REFERENCE_RANGE": "Below pH reference range",
    "ABOVE_REFERENCE_RANGE": "Above pH reference range",
    "ZERO_REVIEW": "Zero value — source review required",
    "MISSING": "Not reported",
    "INVALID_NEGATIVE": "Invalid negative value",
    "INVALID_VALUE": "Invalid value",
}


def prepare_cgwb_location_history(history_df):
    """Validate historical-only mapping and add BIS reference statuses."""
    result = history_df.copy()

    required = {
        "location_id",
        "village",
        "sample_district",
        "station",
        "station_district",
        "distance_km",
        "match_status",
        "data_usage",
        "risk_fusion_eligible",
        "ph_latest_value",
        "ph_sample_date",
    }
    for value_column, date_column in PARAMETER_COLUMNS.values():
        required.update({value_column, date_column})

    missing = required - set(result.columns)
    if missing:
        raise ValueError(
            f"CGWB location history is missing columns: {sorted(missing)}"
        )

    if not result["data_usage"].eq("HISTORICAL_CONTEXT_ONLY").all():
        raise ValueError(
            "CGWB dashboard accepts historical-context records only."
        )

    eligible = (
        result["risk_fusion_eligible"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .isin({"true", "1", "yes"})
    )
    if eligible.any():
        raise ValueError(
            "CGWB historical records must not be eligible for risk fusion."
        )

    cross_district = result["match_status"].eq("CROSS_DISTRICT_REVIEW")
    for value_column, date_column in PARAMETER_COLUMNS.values():
        if result.loc[cross_district, value_column].notna().any():
            raise ValueError(
                "Cross-district chemical values must not be assigned."
            )
        if result.loc[cross_district, date_column].notna().any():
            raise ValueError(
                "Cross-district chemical sampling dates must not be assigned."
            )

    for name, (value_column, _) in PARAMETER_COLUMNS.items():
        if name == "ph":
            result["ph_screening_status"] = result[value_column].map(
                classify_ph
            )
        else:
            _, acceptable, permissible = BIS_LIMITS[name]
            result[f"{name}_screening_status"] = result[value_column].map(
                lambda value: classify_parameter(
                    value, acceptable, permissible
                )
            )

    return result



def summarize_cgwb_screening(record):
    """Count selected-location screening outcomes without combining pH with chemical limits."""
    statuses = {
        name: record[f"{name}_screening_status"]
        for name in PARAMETER_COLUMNS
    }
    values = list(statuses.values())

    return {
        "within_acceptable_or_ph_range": sum(
            value in {"WITHIN_ACCEPTABLE", "WITHIN_REFERENCE_RANGE"}
            for value in values
        ),
        "above_acceptable_within_permissible": values.count(
            "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE"
        ),
        "above_permissible": values.count("ABOVE_PERMISSIBLE"),
        "ph_outside_reference_range": sum(
            statuses["ph"] == value
            for value in {"BELOW_REFERENCE_RANGE", "ABOVE_REFERENCE_RANGE"}
        ),
        "review_required": sum(
            value in {"ZERO_REVIEW", "INVALID_NEGATIVE", "INVALID_VALUE"}
            for value in values
        ),
        "not_reported": values.count("MISSING"),
    }


def build_cgwb_parameter_table(record):
    """Build a display-ready table for one mapped prototype location."""
    rows = []

    ph_value = record["ph_latest_value"]
    ph_status = record["ph_screening_status"]
    rows.append({
        "Parameter": "pH",
        "Latest Value": ph_value,
        "Unit": "—",
        "Sampling Date": record["ph_sample_date"],
        "BIS Reference Screening": STATUS_LABELS[ph_status],
        "Acceptable Limit": "6.5–8.5",
        "Permissible Limit": "No relaxation",
    })

    units = {
        "tds": "mg/L",
        "chloride": "mg/L",
        "sulphate": "mg/L",
        "hardness": "mg/L as CaCO₃",
    }
    labels = {
        "tds": "Total Dissolved Solids",
        "chloride": "Chloride",
        "sulphate": "Sulphate",
        "hardness": "Total Hardness",
    }

    for name, (value_column, date_column) in PARAMETER_COLUMNS.items():
        if name == "ph":
            continue

        _, acceptable, permissible = BIS_LIMITS[name]
        status = record[f"{name}_screening_status"]
        rows.append({
            "Parameter": labels[name],
            "Latest Value": record[value_column],
            "Unit": units[name],
            "Sampling Date": record[date_column],
            "BIS Reference Screening": STATUS_LABELS[status],
            "Acceptable Limit": acceptable,
            "Permissible Limit": permissible,
        })

    return pd.DataFrame(rows)



def build_cgwb_export_table(record):
    """Build a CSV-ready parameter table with its station and mapping context."""
    parameter_table = build_cgwb_parameter_table(record)

    metadata = {
        "Location": record["village"],
        "Location District": record["sample_district"],
        "Matched CGWB Station": record["station"],
        "Station District": record["station_district"],
        "Station Distance (km)": record["distance_km"],
        "Geographic Match Status": record["match_status"],
        "Station First Observation": record["first_observation"],
        "Station Latest Observation": record["latest_observation"],
        "Station Historical Records": record["historical_record_count"],
        "Data Usage": record["data_usage"],
        "Risk Fusion Eligible": record["risk_fusion_eligible"],
    }
    metadata_table = pd.DataFrame(
        {column: [value] * len(parameter_table)
         for column, value in metadata.items()}
    )

    return pd.concat(
        [metadata_table, parameter_table.reset_index(drop=True)],
        axis=1,
    )
