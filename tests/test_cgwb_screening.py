import unittest
import pandas as pd

from src.cgwb_screening import (
    classify_parameter,
    classify_ph,
    screen_cgwb_records,
)


class TestCGWBScreening(unittest.TestCase):

    def test_within_acceptable_limit(self):
        self.assertEqual(
            classify_parameter(450, 500, 2000),
            "WITHIN_ACCEPTABLE",
        )

    def test_above_acceptable_within_permissible(self):
        self.assertEqual(
            classify_parameter(800, 500, 2000),
            "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE",
        )

    def test_above_permissible(self):
        self.assertEqual(
            classify_parameter(2500, 500, 2000),
            "ABOVE_PERMISSIBLE",
        )

    def test_zero_requires_review(self):
        self.assertEqual(
            classify_parameter(0, 500, 2000),
            "ZERO_REVIEW",
        )

    def test_missing_value(self):
        self.assertEqual(
            classify_parameter(float("nan"), 500, 2000),
            "MISSING",
        )

    def test_negative_value_is_invalid(self):
        self.assertEqual(
            classify_parameter(-5, 500, 2000),
            "INVALID_NEGATIVE",
        )

    def test_ph_limits_are_inclusive(self):
        self.assertEqual(classify_ph(6.5), "WITHIN_REFERENCE_RANGE")
        self.assertEqual(classify_ph(8.5), "WITHIN_REFERENCE_RANGE")
        self.assertEqual(classify_ph(6.4), "BELOW_REFERENCE_RANGE")
        self.assertEqual(classify_ph(8.6), "ABOVE_REFERENCE_RANGE")

    def test_screening_preserves_source_values(self):
        df = pd.DataFrame([{
            "Potential of Hydrogen (pH)": 7.5,
            "Total Dissolved Solids (mg/L)": 0,
            "Chloride (mg/L)": 300,
            "Sulphate (mg/L)": None,
            "Total Hardness (mgCaCO3/L)": 150,
        }])

        result = screen_cgwb_records(df)

        self.assertEqual(
            result.loc[0, "tds_screening_status"], "ZERO_REVIEW"
        )
        self.assertEqual(
            result.loc[0, "chloride_screening_status"],
            "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE",
        )
        self.assertEqual(
            result.loc[0, "sulphate_screening_status"], "MISSING"
        )
        self.assertEqual(df.loc[0, "Total Dissolved Solids (mg/L)"], 0)
        self.assertEqual(
            result.loc[0, "screening_usage"],
            "HISTORICAL_REFERENCE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
