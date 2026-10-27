"""Build a location-level multi-source dataset for JalRakshak 360.

This script merges source datasets for analysis and traceability.
It does not change or calculate final risk scores.
"""

from pathlib import Path

import pandas as pd


BASE_PATH = Path("data/processed/water_risk_with_rainfall.csv")
POPULATION_PATH = Path("data/processed/population_exposure_features.csv")
GROUNDWATER_PATH = Path("data/processed/groundwater_station_mapping.csv")
OUTPUT_PATH = Path("data/processed/multi_source_fusion.csv")


def read_unique_locations(path, source_name):
    if not path.exists():
        raise FileNotFoundError(f"{source_name} not found: {path}")

    df = pd.read_csv(path)

    if "location_id" not in df.columns:
        raise ValueError(f"{source_name} has no location_id column.")

    df["location_id"] = df["location_id"].astype(str)

    if df["location_id"].duplicated().any():
        raise ValueError(f"{source_name} contains duplicate location IDs.")

    return df


def require_columns(df, columns, source_name):
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"{source_name} is missing columns: {sorted(missing)}"
        )


def main():
    print("Loading source datasets...")

    base = read_unique_locations(BASE_PATH, "Rainfall-integrated dataset")
    population = read_unique_locations(
        POPULATION_PATH, "Population dataset"
    )
    groundwater = read_unique_locations(
        GROUNDWATER_PATH, "Groundwater mapping dataset"
    )

    require_columns(
        base,
        [
            "state", "district", "latitude", "longitude",
            "rainfall_7d", "rainfall_normal",
            "rainfall_source", "weather_model",
        ],
        "Rainfall-integrated dataset",
    )

    require_columns(
        population,
        [
            "sample_district",
            "district_population_2011",
            "district_households_2011",
            "population_reference_year",
            "population_geography_level",
            "population_source",
            "population_is_village_level",
        ],
        "Population dataset",
    )

    require_columns(
        groundwater,
        [
            "nearest_station",
            "station_district",
            "distance_km",
            "latest_observation",
            "days_since_observation",
            "raw_reading_m",
            "distance_status",
            "freshness_status",
            "district_status",
            "reading_sign_status",
            "eligible_for_risk_fusion",
        ],
        "Groundwater dataset",
    )

    base_ids = set(base["location_id"])
    population_ids = set(population["location_id"])
    groundwater_ids = set(groundwater["location_id"])

    if base_ids != population_ids:
        raise ValueError(
            "Location IDs do not match between rainfall and population data."
        )

    if base_ids != groundwater_ids:
        raise ValueError(
            "Location IDs do not match between rainfall and groundwater data."
        )

    population_columns = [
        "location_id",
        "census_district_name_2011",
        "district_population_2011",
        "district_households_2011",
        "district_male_population_2011",
        "district_female_population_2011",
        "district_population_age_0_6_2011",
        "population_reference_year",
        "population_geography_level",
        "population_source",
        "population_is_village_level",
    ]

    groundwater_columns = [
        "location_id",
        "nearest_station",
        "station_district",
        "station_latitude",
        "station_longitude",
        "distance_km",
        "latest_observation",
        "days_since_observation",
        "raw_reading_m",
        "distance_status",
        "freshness_status",
        "district_status",
        "reading_sign_status",
        "eligible_for_risk_fusion",
    ]

    # Join one-to-one by prototype location ID.
    fused = base.merge(
        population[population_columns],
        on="location_id",
        how="left",
        validate="one_to_one",
    )

    fused = fused.merge(
        groundwater[groundwater_columns],
        on="location_id",
        how="left",
        validate="one_to_one",
    )

    # Explicitly record the meaning and eligibility of each source.
    fused["rainfall_data_status"] = "ERA5_REANALYSIS_ESTIMATE"
    fused["population_data_status"] = "HISTORICAL_DISTRICT_CONTEXT"
    fused["groundwater_data_status"] = "MONITORING_ONLY_NOT_FOR_RISK"

    fused["wq6_data_status"] = "NOT_MERGED_STATE_MISMATCH"
    fused["wq6_exclusion_reason"] = (
        "Current WQ6 integration covers Uttar Pradesh; "
        "prototype locations are in Uttarakhand."
    )

    fused["risk_fusion_status"] = (
        "EXISTING_PIPELINE_UNCHANGED"
    )

    if len(fused) != len(base):
        raise ValueError("Unexpected row count after source fusion.")

    if fused["rainfall_7d"].isna().any():
        raise ValueError("Merged dataset has missing rainfall values.")

    if fused["district_population_2011"].isna().any():
        raise ValueError("Merged dataset has missing census population.")

    if fused["eligible_for_risk_fusion"].fillna(False).astype(bool).any():
        raise ValueError(
            "Unexpected groundwater eligibility flag. Review before saving."
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fused.to_csv(OUTPUT_PATH, index=False)

    print("\nMulti-source fusion dataset created successfully.")
    print("Rows:", len(fused))
    print("Unique locations:", fused["location_id"].nunique())
    print("Rainfall source:", fused["rainfall_source"].nunique(), "source label(s)")
    print("Population reference year(s):",
          sorted(fused["population_reference_year"].dropna().unique().tolist()))
    print("Groundwater eligible for risk fusion:",
          int(fused["eligible_for_risk_fusion"].fillna(False).astype(bool).sum()))
    print("WQ6 merged:", "No — state mismatch explicitly recorded")
    print("Risk-scoring logic changed: No")
    print("Output:", OUTPUT_PATH)

    print("\nPreview:")
    preview_columns = [
        "location_id",
        "district",
        "rainfall_7d",
        "district_population_2011",
        "nearest_station",
        "distance_km",
        "groundwater_data_status",
        "wq6_data_status",
    ]
    print(fused[preview_columns].to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", type(exc).__name__, str(exc))
        raise
