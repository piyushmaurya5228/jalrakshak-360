import unittest

import pandas as pd

from src.scoring_validation import validate_scoring_inputs


class TestScoringValidation(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame([{
            "population": 2000,
            "water_contamination_rate": 0.25,
            "rainfall_7d": 80.0,
            "rainfall_normal": 90.0,
            "groundwater_stress": 0.4,
            "previous_contamination": 0.2,
            "water_tests": 10,
            "contaminated_tests": 2,
        }])

    def test_valid_scoring_inputs_pass(self):
        validate_scoring_inputs(self.df)

    def test_missing_scoring_column_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            validate_scoring_inputs(self.df.drop(columns=["rainfall_7d"]))

    def test_non_finite_scoring_value_is_rejected(self):
        df = self.df.copy()
        df.loc[0, "groundwater_stress"] = float("inf")

        with self.assertRaisesRegex(ValueError, "finite numeric"):
            validate_scoring_inputs(df)

    def test_normalized_rate_outside_range_is_rejected(self):
        df = self.df.copy()
        df.loc[0, "water_contamination_rate"] = 1.2

        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            validate_scoring_inputs(df)

    def test_zero_water_tests_are_not_treated_as_zero_historical_risk(self):
        df = self.df.copy()
        df.loc[0, "water_tests"] = 0
        df.loc[0, "contaminated_tests"] = 0

        with self.assertRaisesRegex(ValueError, "at least one water test"):
            validate_scoring_inputs(df)

    def test_contaminated_tests_cannot_exceed_total(self):
        df = self.df.copy()
        df.loc[0, "contaminated_tests"] = 11

        with self.assertRaisesRegex(ValueError, "between zero and total"):
            validate_scoring_inputs(df)

    def test_zero_rainfall_baseline_is_rejected(self):
        df = self.df.copy()
        df.loc[0, "rainfall_normal"] = 0

        with self.assertRaisesRegex(ValueError, "greater than zero"):
            validate_scoring_inputs(df)

    def test_empty_dataset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            validate_scoring_inputs(self.df.iloc[0:0])


if __name__ == "__main__":
    unittest.main()
