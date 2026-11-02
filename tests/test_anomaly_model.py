import unittest
import pandas as pd

from src.anomaly_model import train_anomaly_model, add_anomaly_scores


class TestAnomalyModel(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv(
            "data/sample/water_risk_sample.csv"
        )

    def test_anomaly_columns(self):
        model = train_anomaly_model(self.df)
        result = add_anomaly_scores(self.df, model)

        self.assertIn("anomaly_prediction", result.columns)
        self.assertIn("anomaly_score", result.columns)

    def test_same_random_state_produces_reproducible_results(self):
        model1 = train_anomaly_model(
            self.df, contamination=0.20, random_state=42
        )
        model2 = train_anomaly_model(
            self.df, contamination=0.20, random_state=42
        )

        result1 = add_anomaly_scores(self.df, model1)
        result2 = add_anomaly_scores(self.df, model2)

        pd.testing.assert_series_equal(
            result1["anomaly_prediction"],
            result2["anomaly_prediction"],
        )
        pd.testing.assert_series_equal(
            result1["anomaly_score"],
            result2["anomaly_score"],
        )

    def test_anomaly_score_range(self):
        model = train_anomaly_model(self.df)
        result = add_anomaly_scores(self.df, model)

        self.assertTrue(
            ((result["anomaly_score"] >= 0) &
             (result["anomaly_score"] <= 100)).all()
        )


if __name__ == "__main__":
    unittest.main()
