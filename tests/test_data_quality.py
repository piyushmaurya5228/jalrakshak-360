import unittest
import pandas as pd

from src.data_quality import validate_dataset


class TestDataQuality(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame([{
            "location_id": 1,
            "state": "Uttarakhand",
            "district": "Dehradun",
            "village": "Village_A",
            "latitude": 30.0,
            "longitude": 78.0,
            "population": 2000,
            "water_contamination_rate": 0.25,
            "fluoride_level": 0.8,
            "nitrate_level": 15.0,
            "iron_level": 0.3,
            "rainfall_7d_original_sample": 80,
            "rainfall_normal_original_sample": 90,
            "groundwater_stress": 0.4,
            "previous_contamination": 0.2,
            "water_tests": 10,
            "contaminated_tests": 2,
            "rainfall_7d": 5.0,
            "rainfall_normal": 6.0,
            "rainfall_window_start": "2026-10-20",
            "rainfall_window_end": "2026-10-26",
            "normal_start_year": 1991,
            "normal_end_year": 2020,
            "valid_baseline_years": 30,
            "weather_grid_latitude": 30.0,
            "weather_grid_longitude": 78.0,
            "rainfall_source": "Test Source",
            "weather_model": "Test Model",
            "retrieved_at_ist": "2026-10-30 10:00:00",
        }])

    def failed_checks(self, report):
        return report.loc[~report["passed"], "check"].tolist()

    def test_valid_dataset_passes_all_checks(self):
        report = validate_dataset(self.df)

        self.assertTrue(
            report["passed"].all(),
            msg=str(self.failed_checks(report)),
        )

    def test_missing_required_column_is_detected(self):
        df = self.df.drop(columns=["district"])
        report = validate_dataset(df)

        self.assertIn(
            "Required columns present",
            self.failed_checks(report),
        )

    def test_duplicate_location_id_is_detected(self):
        df = pd.concat(
            [self.df, self.df.assign(village="Village_B")],
            ignore_index=True,
        )

        report = validate_dataset(df)

        self.assertIn(
            "Unique location IDs",
            self.failed_checks(report),
        )

    def test_contaminated_tests_cannot_exceed_total_tests(self):
        df = self.df.copy()
        df.loc[0, "contaminated_tests"] = 11

        report = validate_dataset(df)

        self.assertIn(
            "Contaminated tests do not exceed total tests",
            self.failed_checks(report),
        )

    def test_invalid_normalized_rate_is_detected(self):
        df = self.df.copy()
        df.loc[0, "water_contamination_rate"] = 1.5

        report = validate_dataset(df)

        self.assertIn(
            "Normalized risk rates within 0-1",
            self.failed_checks(report),
        )

    def test_invalid_rainfall_date_is_detected(self):
        df = self.df.copy()
        df.loc[0, "rainfall_window_start"] = "invalid-date"

        report = validate_dataset(df)

        self.assertIn(
            "Valid rainfall window start dates",
            self.failed_checks(report),
        )

    def test_reversed_rainfall_window_is_detected(self):
        df = self.df.copy()
        df.loc[0, "rainfall_window_start"] = "2026-10-28"
        df.loc[0, "rainfall_window_end"] = "2026-10-20"

        report = validate_dataset(df)

        self.assertIn(
            "Rainfall window dates are ordered",
            self.failed_checks(report),
        )


if __name__ == "__main__":
    unittest.main()
