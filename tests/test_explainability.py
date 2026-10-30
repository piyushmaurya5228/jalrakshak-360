import unittest

import pandas as pd

from src.explainability import (
    explain_risk_row,
    add_risk_explanations,
)
from src.risk_fusion import fuse_risk_scores


class TestExplainability(unittest.TestCase):

    def setUp(self):
        self.row = pd.Series({
            "water_risk": 42.0,
            "rainfall_risk": 8.68,
            "groundwater_risk": 65.0,
            "historical_risk": 40.0,
            "exposure_risk": 24.0,
            "risk_score": 36.27,
            "anomaly_score": 23.93,
        })

    def test_weighted_factor_contributions(self):
        result = explain_risk_row(self.row)

        self.assertEqual(result["water_risk_contribution"], 14.70)
        self.assertEqual(result["rainfall_risk_contribution"], 2.17)
        self.assertEqual(result["groundwater_risk_contribution"], 13.0)
        self.assertEqual(result["historical_risk_contribution"], 4.0)
        self.assertEqual(result["exposure_risk_contribution"], 2.4)
        self.assertEqual(result["rule_score_reconstructed"], 36.27)

    def test_explained_score_matches_actual_fusion(self):
        explanation = explain_risk_row(self.row)
        actual = fuse_risk_scores(
            self.row["risk_score"],
            self.row["anomaly_score"],
        )

        self.assertEqual(
            explanation["explained_final_risk_score"],
            actual["final_risk_score"],
        )

    def test_rule_floor_is_reported(self):
        result = explain_risk_row(self.row)

        self.assertTrue(result["rule_floor_applied"])
        self.assertEqual(result["rule_floor_adjustment"], 3.7)

    def test_high_anomaly_does_not_apply_rule_floor(self):
        row = self.row.copy()
        row["risk_score"] = 40.0
        row["anomaly_score"] = 100.0

        result = explain_risk_row(row)

        self.assertFalse(result["rule_floor_applied"])
        self.assertEqual(result["explained_final_risk_score"], 58.0)

    def test_dataframe_explanation_preserves_original_data(self):
        df = pd.DataFrame([self.row])
        result = add_risk_explanations(df)

        self.assertEqual(len(result), len(df))
        self.assertTrue(
            result["risk_score"].equals(df["risk_score"])
        )
        self.assertIn("rule_floor_applied", result.columns)
        self.assertIn("explained_final_risk_score", result.columns)
        self.assertNotIn("rule_floor_applied", df.columns)

    def test_invalid_anomaly_score_is_rejected(self):
        row = self.row.copy()
        row["anomaly_score"] = float("nan")

        with self.assertRaises(ValueError):
            explain_risk_row(row)


if __name__ == "__main__":
    unittest.main()
