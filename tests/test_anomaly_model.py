import unittest
import pandas as pd

from src.anomaly_model import train_anomaly_model, add_anomaly_scores, FEATURES


class TestAnomalyModel(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv("data/sample/water_risk_sample.csv")

    def test_anomaly_columns(self):
        model = train_anomaly_model(self.df)
        result = add_anomaly_scores(self.df, model)
        self.assertIn("anomaly_prediction", result.columns)
        self.assertIn("anomaly_score", result.columns)

    def test_same_random_state_produces_reproducible_results(self):
        model1 = train_anomaly_model(self.df, contamination=0.20, random_state=42)
        model2 = train_anomaly_model(self.df, contamination=0.20, random_state=42)
        result1 = add_anomaly_scores(self.df, model1)
        result2 = add_anomaly_scores(self.df, model2)
        pd.testing.assert_series_equal(result1["anomaly_prediction"], result2["anomaly_prediction"])
        pd.testing.assert_series_equal(result1["anomaly_score"], result2["anomaly_score"])

    def test_anomaly_score_range(self):
        model = train_anomaly_model(self.df)
        result = add_anomaly_scores(self.df, model)
        self.assertTrue(((result["anomaly_score"] >= 0) & (result["anomaly_score"] <= 100)).all())

    def test_scores_do_not_depend_on_other_scored_rows(self):
        model = train_anomaly_model(self.df)
        baseline = add_anomaly_scores(self.df, model)["anomaly_score"]
        extreme = self.df.iloc[[0]].copy()
        extreme.loc[:, FEATURES] = [1.0, 10000.0, 0.1, 1.0, 1.0]
        expanded = pd.concat([self.df, extreme], ignore_index=True)
        expanded_scores = add_anomaly_scores(expanded, model)["anomaly_score"].iloc[:len(self.df)].reset_index(drop=True)
        pd.testing.assert_series_equal(baseline.reset_index(drop=True), expanded_scores)

    def test_empty_training_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            train_anomaly_model(self.df.iloc[0:0])

    def test_missing_model_feature_is_rejected(self):
        incomplete = self.df.drop(columns=[FEATURES[0]])
        with self.assertRaisesRegex(ValueError, "missing features"):
            train_anomaly_model(incomplete)

    def test_non_finite_model_feature_is_rejected(self):
        invalid = self.df.copy()
        invalid.loc[invalid.index[0], FEATURES[0]] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            train_anomaly_model(invalid)


if __name__ == "__main__":
    unittest.main()
