import unittest
from pathlib import Path

import pandas as pd

from src.wqmis_mapper import build_wqmis_risk_data


class TestWQMISMapper(unittest.TestCase):

    def test_mapper_output(self):
        output = Path("data/processed/test_wqmis_risk.csv")

        df = build_wqmis_risk_data(
            "data/raw/wqmis_up_2025_2026.csv",
            output,
        )

        self.assertEqual(len(df), 75)
        self.assertEqual(
            int((df["contamination_burden"] > 0).sum()),
            40,
        )
        self.assertEqual(
            int(df["contamination_burden"].max()),
            91,
        )

        self.assertTrue(
            ((df["water_contamination_rate"] >= 0) &
             (df["water_contamination_rate"] <= 1)).all()
        )

        self.assertTrue(output.exists())

        output.unlink()


if __name__ == "__main__":
    unittest.main()
