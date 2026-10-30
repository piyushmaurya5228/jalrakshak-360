import unittest

from src.risk_engine import calculate_risk


class TestRiskEngine(unittest.TestCase):

    def test_critical_risk(self):
        score, level, priority = calculate_risk(
            100, 100, 100, 100, 100
        )

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
        score, level, priority = calculate_risk(
            0, 0, 0, 0, 0
        )

        self.assertEqual(score, 0.0)
        self.assertEqual(level, "LOW")
        self.assertEqual(priority, "P3")


if __name__ == "__main__":
    unittest.main()
