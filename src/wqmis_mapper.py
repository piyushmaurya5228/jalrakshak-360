"""Map official JJM WQ6 contamination counts to JalRakshak risk features."""

from pathlib import Path

import pandas as pd


WQ6_COLUMNS = [
    "PH",
    "TDS",
    "Turbidity",
    "Chloride",
    "Total_Alkalinity",
    "Total_Hardness",
    "Sulphate",
    "Iron",
    "Total_Arsenic",
    "Fluoride",
    "Nitrate",
    "Residual_Chlorine",
    "Others",
    "Bacteriologial_Contamination",
    "TotalColiform",
    "TotalEcoil",
]


def build_wqmis_risk_data(input_file, output_file):
    """Create a relative contamination-burden dataset from WQ6 counts."""

    df = pd.read_csv(input_file)

    df["contamination_burden"] = df[WQ6_COLUMNS].sum(axis=1)

    max_burden = df["contamination_burden"].max()

    if max_burden > 0:
        df["water_contamination_rate"] = (
            df["contamination_burden"] / max_burden
        )
    else:
        df["water_contamination_rate"] = 0.0

    df["water_contamination_rate"] = (
        df["water_contamination_rate"].clip(0, 1)
    )

    # These fields are intentionally marked unavailable.
    # They must be joined from other verified sources later.
    df["rainfall_7d"] = 0.0
    df["rainfall_normal"] = 0.0
    df["groundwater_stress"] = 0.0
    df["population"] = 0

    df["water_tests"] = 0
    df["contaminated_tests"] = 0

    result = df[
        [
            "State",
            "water_contamination_rate",
            "contamination_burden",
            *WQ6_COLUMNS,
            "rainfall_7d",
            "rainfall_normal",
            "groundwater_stress",
            "population",
            "water_tests",
            "contaminated_tests",
        ]
    ].copy()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)

    return result


if __name__ == "__main__":
    input_file = "data/raw/wqmis_up_2026_2027.csv"
    output_file = "data/processed/wqmis_up_2026_2027_risk.csv"

    result = build_wqmis_risk_data(input_file, output_file)

    print("Rows:", len(result))
    print("Output:", output_file)
    print(
        "Non-zero contamination:",
        int((result["contamination_burden"] > 0).sum()),
    )
    print(
        "Maximum contamination burden:",
        int(result["contamination_burden"].max()),
    )
