import unittest

from src.risk_engine import calculate_risk, calculate_location_risk, rainfall_risk


class TestRiskEngine(unittest.TestCase):

    def test_critical_risk(self):
        score, level, priority = calculate_risk(100, 100, 100, 100, 100)
        self.assertEqual(score, 100.0)
        self.assertEqual(level, "CRITICAL")
        self.assertEqual(priority, "P1")

    def test_risk_level_boundaries(self):
        cases = [
            (29.99, "LOW", "P3"),
            (30.00, "WATCH", "P2"),
            (59.99, "WATCH", "P2"),
            (60.00, "HIGH", "P1"),
            (79.99, "HIGH", "P1"),
            (80.00, "CRITICAL", "P1"),
        ]
        for value, expected_level, expected_priority in cases:
            with self.subTest(score=value):
                score, level, priority = calculate_risk(
                    value, value, value, value, value
                )
                self.assertEqual(score, value)
                self.assertEqual(level, expected_level)
                self.assertEqual(priority, expected_priority)

    def test_low_risk(self):
        score, level, priority = calculate_risk(0, 0, 0, 0, 0)
        self.assertEqual(score, 0.0)
        self.assertEqual(level, "LOW")
        self.assertEqual(priority, "P3")

    def test_zero_rainfall_baseline_is_rejected_directly(self):
        with self.assertRaisesRegex(ValueError, "baseline must be greater than zero"):
            rainfall_risk(10, 0)

    def test_non_finite_rainfall_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            rainfall_risk(float("nan"), 10)

    def test_zero_water_tests_are_rejected_by_location_scorer(self):
        row = {
            "water_contamination_rate": 0.1,
            "rainfall_7d": 10,
            "rainfall_normal": 20,
            "groundwater_stress": 0.2,
            "water_tests": 0,
            "contaminated_tests": 0,
            "population": 100,
        }
        with self.assertRaisesRegex(ValueError, "At least one water test"):
            calculate_location_risk(row)


if __name__ == "__main__":
    unittest.main()
