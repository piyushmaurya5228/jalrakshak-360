"""Audit groundwater telemetry quality without changing source data."""

from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw/groundwater_telemetry_uttarakhand.csv")
OUTPUT_PATH = Path("data/processed/groundwater_station_quality_audit.csv")

DATE_COL = "Data Acquisition Time"
LEVEL_COL = "Groundwater Level Telemetry 6 Hourly (meter)"
JUMP_THRESHOLD_M = 10.0
MAX_GAP_HOURS = 12.0

def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Source file not found: {RAW_PATH}")

    df = pd.read_csv(
        RAW_PATH,
        usecols=["Station", "District", "RL_MSL", DATE_COL, LEVEL_COL],
        low_memory=False,
    )

    df[DATE_COL] = pd.to_datetime(
        df[DATE_COL], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    df[LEVEL_COL] = pd.to_numeric(df[LEVEL_COL], errors="coerce")
    df["RL_MSL"] = pd.to_numeric(df["RL_MSL"], errors="coerce")
    df = df.dropna(subset=["Station", "District", DATE_COL, LEVEL_COL])
    keys = ["District", "Station"]
    df = df.sort_values(keys + [DATE_COL])

    summary = (
        df.groupby(keys)
        .agg(
            records=(LEVEL_COL, "count"),
            negative_readings=(LEVEL_COL, lambda s: int((s < 0).sum())),
            zero_readings=(LEVEL_COL, lambda s: int((s == 0).sum())),
            positive_readings=(LEVEL_COL, lambda s: int((s > 0).sum())),
            minimum_reading_m=(LEVEL_COL, "min"),
            median_reading_m=(LEVEL_COL, "median"),
            maximum_reading_m=(LEVEL_COL, "max"),
            rl_msl_missing_records=("RL_MSL", lambda s: int(s.isna().sum())),
        )
        .reset_index()
    )

    grouped = df.groupby(keys, sort=False)
    df["previous_reading_m"] = grouped[LEVEL_COL].shift(1)
    df["previous_time"] = grouped[DATE_COL].shift(1)
    df["gap_hours"] = (
        df[DATE_COL] - df["previous_time"]
    ).dt.total_seconds() / 3600
    df["absolute_change_m"] = (
        df[LEVEL_COL] - df["previous_reading_m"]
    ).abs()

    pairs = df[
        (df["gap_hours"] > 0) & (df["gap_hours"] <= MAX_GAP_HOURS)
    ]

    jumps = (
        pairs.assign(
            large_jump=pairs["absolute_change_m"] > JUMP_THRESHOLD_M
        )
        .groupby(keys)
        .agg(
            consecutive_pairs=("absolute_change_m", "size"),
            changes_over_threshold=("large_jump", "sum"),
            largest_absolute_change_m=("absolute_change_m", "max"),
        )
        .reset_index()
    )

    report = summary.merge(jumps, on=keys, how="left")
    report["consecutive_pairs"] = report["consecutive_pairs"].fillna(0).astype(int)
    report["changes_over_threshold"] = (
        report["changes_over_threshold"].fillna(0).astype(int)
    )

    report["sign_review_status"] = report.apply(
        lambda r: (
            "MIXED_SIGN_REVIEW"
            if r["negative_readings"] > 0 and r["positive_readings"] > 0
            else "NEGATIVE_VALUES_REVIEW"
            if r["negative_readings"] > 0
            else "NO_NEGATIVE_VALUES"
        ),
        axis=1,
    )
    report["rl_msl_status"] = report.apply(
        lambda r: (
            "ALL_MISSING"
            if r["rl_msl_missing_records"] == r["records"]
            else "PARTIALLY_MISSING"
            if r["rl_msl_missing_records"] > 0
            else "AVAILABLE"
        ),
        axis=1,
    )
    report["rapid_change_status"] = report[
        "changes_over_threshold"
    ].map(
        lambda n: "LARGE_CHANGE_REVIEW" if n > 0 else "NO_LARGE_CHANGE_FLAG"
    )
    report["exploratory_jump_threshold_m"] = JUMP_THRESHOLD_M
    report["exploratory_max_gap_hours"] = MAX_GAP_HOURS

    report = report.sort_values(
        ["changes_over_threshold", "District", "Station"],
        ascending=[False, True, True],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_PATH, index=False)

    print("Groundwater quality audit completed.")
    print("Stations audited:", len(report))
    print(
        "Stations with large-change flags:",
        int((report["changes_over_threshold"] > 0).sum()),
    )
    print(
        "Total large-change flags:",
        int(report["changes_over_threshold"].sum()),
    )
    print("RL_MSL missing in all source records:", bool(
        report["rl_msl_status"].eq("ALL_MISSING").all()
    ))
    print("Audit report:", OUTPUT_PATH)
    print("\nTop flagged stations:")
    columns = [
        "District", "Station", "changes_over_threshold",
        "largest_absolute_change_m", "sign_review_status", "rl_msl_status",
    ]
    print(report[columns].head(15).to_string(index=False))
    print(
        "\nNOTE: The 10 m threshold is exploratory, not an official standard. "
        "The report flags observations for review; it does not correct them."
    )

if __name__ == "__main__":
    main()
