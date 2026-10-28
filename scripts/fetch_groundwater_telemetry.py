"""Fetch and audit Uttarakhand groundwater telemetry."""

from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, asin, sqrt

import pandas as pd
import requests


URL = (
    "https://nwdp.nwic.gov.in/dataset/"
    "6b466bb3-6539-4880-bfeb-1863a393573f/resource/"
    "c5b266e7-a450-4a4d-8727-fc83f35c20c3/download/"
    "gwl_tel_6_hourly_uttarakhand_uk_2026_2030.csv"
)

SAMPLE = Path("data/sample/water_risk_sample.csv")
RAW = Path("data/raw/groundwater_telemetry_uttarakhand.csv")
OUTPUT = Path("data/processed/groundwater_station_mapping.csv")

DISTANCE_LIMIT_KM = 15
FRESHNESS_LIMIT_DAYS = 30


def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in kilometres."""
    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )
    return 6371 * 2 * asin(sqrt(value))


def find_nearest_same_district_station(candidates, sample_district):
    """Return the nearest station in the sample district, or None."""
    same_district = candidates.loc[
        candidates["District"].astype(str).str.strip().str.casefold()
        == str(sample_district).strip().casefold()
    ]

    if same_district.empty:
        return None

    return same_district.sort_values("distance_km").iloc[0]


def main(fetch_source=True):
    if fetch_source:
        print("Fetching official groundwater telemetry...")
        response = requests.get(URL, timeout=(10, 120))
        response.raise_for_status()

        RAW.parent.mkdir(parents=True, exist_ok=True)
        RAW.write_bytes(response.content)
    else:
        if not RAW.exists():
            raise FileNotFoundError(
                f"Cached groundwater source not found: {RAW}"
            )
        print("Using cached groundwater telemetry (no download).")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    gw = pd.read_csv(RAW)
    sample = pd.read_csv(SAMPLE)

    date_col = "Data Acquisition Time"
    level_col = "Groundwater Level Telemetry 6 Hourly (meter)"

    required = {
        "Station", "District", "Latitude", "Longitude",
        date_col, level_col,
    }

    missing = required - set(gw.columns)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")

    gw[date_col] = pd.to_datetime(
        gw[date_col],
        format="%d-%m-%Y %H:%M",
        errors="coerce",
    )
    gw[level_col] = pd.to_numeric(gw[level_col], errors="coerce")
    gw["Latitude"] = pd.to_numeric(gw["Latitude"], errors="coerce")
    gw["Longitude"] = pd.to_numeric(gw["Longitude"], errors="coerce")

    gw = gw.dropna(
        subset=["Station", "District", "Latitude", "Longitude", date_col]
    )

    # Keep each station's most recent observation.
    latest = (
        gw.sort_values(date_col)
        .groupby("Station", as_index=False)
        .tail(1)
        .copy()
    )

    run_date = datetime.now().date()
    rows = []

    for _, loc in sample.iterrows():
        candidates = latest.copy()

        candidates["distance_km"] = candidates.apply(
            lambda row: haversine(
                float(loc["latitude"]),
                float(loc["longitude"]),
                row["Latitude"],
                row["Longitude"],
            ),
            axis=1,
        )

        station = candidates.sort_values("distance_km").iloc[0]
        distance = float(station["distance_km"])
        days_old = (run_date - station[date_col].date()).days
        reading = station[level_col]

        # Keep the nearest same-district option separate from nearest overall.
        local_station = find_nearest_same_district_station(
            candidates, loc["district"]
        )

        if local_station is None:
            local_station_name = None
            local_station_district = None
            local_station_latitude = None
            local_station_longitude = None
            local_distance = None
            local_latest_observation = None
            local_days_old = None
            local_distance_status = "NO_SAME_DISTRICT_STATION"
            local_freshness_status = "NO_SAME_DISTRICT_STATION"
            local_reading_sign_status = "NO_SAME_DISTRICT_STATION"
        else:
            local_station_name = local_station["Station"]
            local_station_district = local_station["District"]
            local_station_latitude = local_station["Latitude"]
            local_station_longitude = local_station["Longitude"]
            local_distance = float(local_station["distance_km"])
            local_latest_observation = local_station[date_col]
            local_days_old = (
                run_date - local_latest_observation.date()
            ).days

            local_distance_status = (
                "WITHIN_LIMIT"
                if local_distance <= DISTANCE_LIMIT_KM
                else "DISTANT_REVIEW"
            )
            local_freshness_status = (
                "RECENT"
                if 0 <= local_days_old <= FRESHNESS_LIMIT_DAYS
                else "STALE_REVIEW"
            )

            # A positive value is not proof that the source convention is valid.
            local_reading_sign_status = "SIGN_CONVENTION_REVIEW"

        same_district = (
            str(loc["district"]).strip().casefold()
            == str(station["District"]).strip().casefold()
        )

        rows.append({
            "location_id": loc["location_id"],
            "sample_district": loc["district"],
            "sample_latitude": loc["latitude"],
            "sample_longitude": loc["longitude"],
            "nearest_same_district_station": local_station_name,
            "same_district_station_district": local_station_district,
            "same_district_station_latitude": local_station_latitude,
            "same_district_station_longitude": local_station_longitude,
            "same_district_distance_km": (
                round(local_distance, 2)
                if local_distance is not None else None
            ),
            "same_district_distance_status": local_distance_status,
            "same_district_latest_observation": local_latest_observation,
            "same_district_days_since_observation": local_days_old,
            "same_district_freshness_status": local_freshness_status,
            "same_district_reading_sign_status": (
                local_reading_sign_status
            ),
            "nearest_station": station["Station"],
            "station_district": station["District"],
            "station_latitude": station["Latitude"],
            "station_longitude": station["Longitude"],
            "distance_km": round(distance, 2),
            "latest_observation": station[date_col],
            "days_since_observation": days_old,
            "raw_reading_m": reading,
            "distance_status": (
                "WITHIN_LIMIT"
                if distance <= DISTANCE_LIMIT_KM
                else "DISTANT_REVIEW"
            ),
            "freshness_status": (
                "RECENT"
                if 0 <= days_old <= FRESHNESS_LIMIT_DAYS
                else "STALE_REVIEW"
            ),
            "district_status": (
                "SAME_DISTRICT" if same_district else "CROSS_DISTRICT"
            ),
            # Keep all readings under review until the source convention is verified.
            "reading_sign_status": "SIGN_CONVENTION_REVIEW",
            # No raw reading is approved for risk fusion yet.
            "eligible_for_risk_fusion": False,
        })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)

    print("Source records:", len(gw))
    print("Monitoring stations:", gw["Station"].nunique())
    print("Locations mapped:", len(result))
    print("Raw source:", RAW)
    print("Mapping report:", OUTPUT)
    print("\nMapping summary:")
    print(result[
        [
            "location_id",
            "nearest_station",
            "distance_km",
            "nearest_same_district_station",
            "same_district_distance_km",
            "same_district_distance_status",
            "same_district_freshness_status",
            "days_since_observation",
            "distance_status",
            "freshness_status",
            "district_status",
            "reading_sign_status",
        ]
    ].to_string(index=False))

    print("\nGroundwater stress scores were NOT generated.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the cached raw CSV without downloading new source data.",
    )
    args = parser.parse_args()
    main(fetch_source=not args.offline)
