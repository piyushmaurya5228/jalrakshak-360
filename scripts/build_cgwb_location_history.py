from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

SAMPLE = ROOT / "data/processed/water_risk_with_rainfall.csv"
SOURCE = ROOT / "data/raw/cgwb_uttarakhand_groundwater_quality_1961_2025.csv"
OUTPUT = ROOT / "data/processed/cgwb_uttarakhand_location_quality_history.csv"

DISTANCE_LIMIT_KM = 15

PARAMETERS = {
    "ph": "Potential of Hydrogen (pH)",
    "ec": "Electric Conductivity (μS/cm)",
    "tds": "Total Dissolved Solids (mg/L)",
    "chloride": "Chloride (mg/L)",
    "sulphate": "Sulphate (mg/L)",
    "hardness": "Total Hardness (mgCaCO3/L)",
    "iron": "Iron(mg/L)",
    "arsenic": "Arsenic (mg/L)",
}


def normalize(value):
    return " ".join(str(value).strip().casefold().split())


def haversine(lat1, lon1, lat2, lon2):
    values = np.radians([lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = values

    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2)
        * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def main():
    sample = pd.read_csv(SAMPLE)
    source = pd.read_csv(SOURCE, low_memory=False)

    source["Data Acquisition Time"] = pd.to_datetime(
        source["Data Acquisition Time"],
        format="%d-%m-%Y %H:%M",
        errors="coerce",
    )

    for column in ["Latitude", "Longitude"]:
        source[column] = pd.to_numeric(
            source[column], errors="coerce"
        )

    for column in PARAMETERS.values():
        source[column] = pd.to_numeric(
            source[column], errors="coerce"
        )

    source = source.dropna(
        subset=[
            "District", "Station", "Latitude",
            "Longitude", "Data Acquisition Time",
        ]
    ).copy()

    source["_district_key"] = source["District"].map(normalize)
    source["_station_key"] = source["Station"].map(normalize)

    station_catalog = (
        source.sort_values("Data Acquisition Time")
        .drop_duplicates(
            ["_district_key", "_station_key"],
            keep="last",
        )
        .copy()
    )

    today = pd.Timestamp.now().normalize()
    results = []

    for _, location in sample.iterrows():
        district_key = normalize(location["district"])

        same_district = station_catalog[
            station_catalog["_district_key"] == district_key
        ].copy()

        candidates = (
            same_district
            if not same_district.empty
            else station_catalog.copy()
        )

        candidates["distance_km"] = candidates.apply(
            lambda station: haversine(
                location["latitude"],
                location["longitude"],
                station["Latitude"],
                station["Longitude"],
            ),
            axis=1,
        )

        selected = candidates.sort_values("distance_km").iloc[0]

        same_match = not same_district.empty
        distance = float(selected["distance_km"])

        if not same_match:
            match_status = "CROSS_DISTRICT_REVIEW"
        elif distance <= DISTANCE_LIMIT_KM:
            match_status = "SAME_DISTRICT_WITHIN_15KM"
        else:
            match_status = "SAME_DISTRICT_DISTANT_REVIEW"

        history = source[
            (source["_district_key"] == selected["_district_key"])
            & (source["_station_key"] == selected["_station_key"])
        ].sort_values("Data Acquisition Time").copy()

        first_date = history["Data Acquisition Time"].min()
        latest_date = history["Data Acquisition Time"].max()

        record = {
            "location_id": location["location_id"],
            "village": location["village"],
            "sample_district": location["district"],
            "station": selected["Station"],
            "station_district": selected["District"],
            "station_latitude": selected["Latitude"],
            "station_longitude": selected["Longitude"],
            "distance_km": round(distance, 2),
            "match_status": match_status,
            "historical_record_count": len(history),
            "first_observation": first_date.date().isoformat(),
            "latest_observation": latest_date.date().isoformat(),
            "latest_observation_age_days": (
                today - latest_date.normalize()
            ).days,
            "source": "CGWB Groundwater Quality Manual Chemical Parameters",
            "source_period": "1961-2025 dataset, observed records 2000-2023",
            "data_usage": "HISTORICAL_CONTEXT_ONLY",
            "risk_fusion_eligible": False,
        }

        # Cross-district chemistry is not attached to the target location.
        for short_name, parameter in PARAMETERS.items():
            value_key = f"{short_name}_latest_value"
            date_key = f"{short_name}_sample_date"
            age_key = f"{short_name}_age_days"

            record[value_key] = None
            record[date_key] = None
            record[age_key] = None

            if not same_match:
                continue

            available = history.dropna(subset=[parameter])

            if available.empty:
                continue

            observation = available.iloc[-1]
            observation_date = observation["Data Acquisition Time"]

            record[value_key] = observation[parameter]
            record[date_key] = observation_date.date().isoformat()
            record[age_key] = (
                today - observation_date.normalize()
            ).days

        results.append(record)

    report = pd.DataFrame(results)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT, index=False)

    print("CGWB HISTORICAL LOCATION MAPPING COMPLETE")
    print("=" * 55)
    print("Locations:", len(report))
    print("\nMatch classification:")
    print(report["match_status"].value_counts().to_string())
    print("\nRisk-fusion eligible:",
          int(report["risk_fusion_eligible"].sum()))
    print("Historical-only locations:", len(report))
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
