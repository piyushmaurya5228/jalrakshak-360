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

    def test_rainfall_increase_changes_risk_below_normal(self):
        row = pd.Series({
            "rainfall_7d": 2.0,
            "rainfall_normal": 10.0,
            "water_contamination_rate": 0.1,
            "groundwater_stress": 0.2,
            "water_tests": 10,
            "contaminated_tests": 2,
            "population": 1000,
        })

        baseline = simulate_rainfall(row, 0)
        increased = simulate_rainfall(row, 100)

        self.assertEqual(baseline["rainfall_risk"], 2.0)
        self.assertEqual(increased["rainfall_risk"], 4.0)
        self.assertGreater(
            increased["risk_score"], baseline["risk_score"]
        )

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
