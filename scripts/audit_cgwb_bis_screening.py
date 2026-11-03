import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cgwb_screening import screen_cgwb_records


SOURCE = ROOT / "data/raw/cgwb_uttarakhand_groundwater_quality_1961_2025.csv"
OUTPUT = ROOT / "data/processed/cgwb_bis_historical_screening.csv"


def main():
    df = pd.read_csv(SOURCE, low_memory=False)
    report = screen_cgwb_records(df)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT, index=False)

    columns = [
        "tds_screening_status",
        "chloride_screening_status",
        "sulphate_screening_status",
        "hardness_screening_status",
        "ph_screening_status",
    ]

    print("CGWB HISTORICAL BIS SCREENING")
    print("=" * 55)
    print("Observations:", len(report))

    for column in columns:
        print(f"\n{column}:")
        print(report[column].value_counts(dropna=False).to_string())

    print("\nOutput:", OUTPUT)
    print("Original source dataset unchanged.")
    print("Screening is historical reference analysis only.")


if __name__ == "__main__":
    main()
