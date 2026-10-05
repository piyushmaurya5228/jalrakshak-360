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

    def test_low_risk(self):
        score, level, priority = calculate_risk(
            0, 0, 0, 0, 0
        )

        self.assertEqual(score, 0.0)
        self.assertEqual(level, "LOW")
        self.assertEqual(priority, "P3")


if __name__ == "__main__":
    unittest.main()
