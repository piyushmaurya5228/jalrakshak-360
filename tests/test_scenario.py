import unittest
import pandas as pd

from src.scenario import simulate_rainfall


class TestScenario(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv(
            "data/sample/water_risk_sample.csv"
        )

    def test_rainfall_increase_changes_simulation(self):
        result = simulate_rainfall(
            self.df.iloc[1],
            50,
        )

        self.assertEqual(result["original_rainfall"], 82.0)
        self.assertEqual(result["simulated_rainfall"], 123.0)
        self.assertEqual(result["rainfall_risk"], 75.0)

    def test_zero_change_keeps_rainfall(self):
        result = simulate_rainfall(
            self.df.iloc[1],
            0,
        )

        self.assertEqual(
            result["original_rainfall"],
            result["simulated_rainfall"],
        )


if __name__ == "__main__":
    unittest.main()
