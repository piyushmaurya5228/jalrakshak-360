
import unittest
import pandas as pd

from pathlib import Path

PATH = Path("data/processed/cgwb_uttarakhand_location_quality_history.csv")
PARAMETERS = [
    "ph", "ec", "tds", "chloride",
    "sulphate", "hardness", "iron", "arsenic",
]


class TestCGWBLocationHistory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(PATH)

    def test_all_prototype_locations_are_mapped(self):
        self.assertEqual(len(self.df), 12)
        self.assertTrue(self.df["location_id"].is_unique)

    def test_geographic_match_classification(self):
        counts = self.df["match_status"].value_counts().to_dict()
        self.assertEqual(counts.get("SAME_DISTRICT_WITHIN_15KM"), 8)
        self.assertEqual(counts.get("SAME_DISTRICT_DISTANT_REVIEW"), 2)
        self.assertEqual(counts.get("CROSS_DISTRICT_REVIEW"), 2)

    def test_all_records_are_historical_only(self):
        self.assertTrue(
            self.df["data_usage"].eq("HISTORICAL_CONTEXT_ONLY").all()
        )

    def test_no_record_is_eligible_for_risk_fusion(self):
        self.assertFalse(
            self.df["risk_fusion_eligible"].astype(bool).any()
        )

    def test_cross_district_chemical_values_are_not_assigned(self):
        cross = self.df[
            self.df["match_status"] == "CROSS_DISTRICT_REVIEW"
        ]

        for parameter in PARAMETERS:
            self.assertTrue(
                cross[f"{parameter}_latest_value"].isna().all()
            )
            self.assertTrue(
                cross[f"{parameter}_sample_date"].isna().all()
            )

    def test_parameter_values_have_sampling_dates(self):
        for parameter in PARAMETERS:
            available = self.df[
                self.df[f"{parameter}_latest_value"].notna()
            ]
            self.assertTrue(
                available[f"{parameter}_sample_date"].notna().all()
            )


if __name__ == "__main__":
    unittest.main()
