import unittest

from src.risk_fusion import fuse_risk_scores


class TestRiskFusion(unittest.TestCase):

    def test_critical_fused_risk(self):
        result = fuse_risk_scores(73.38, 100)

        self.assertEqual(result["final_risk_score"], 81.37)
        self.assertEqual(result["final_risk_level"], "CRITICAL")
        self.assertEqual(result["final_priority"], "P1")

    def test_low_anomaly_does_not_suppress_rule_risk(self):
        result = fuse_risk_scores(40.02, 0)

        self.assertEqual(result["final_risk_score"], 40.02)
        self.assertEqual(result["final_risk_level"], "WATCH")
        self.assertEqual(result["final_priority"], "P2")

    def test_high_anomaly_can_escalate_rule_risk(self):
        result = fuse_risk_scores(50, 100)

        self.assertEqual(result["final_risk_score"], 65.0)
        self.assertEqual(result["final_risk_level"], "HIGH")
        self.assertEqual(result["final_priority"], "P1")

    def test_low_fused_risk(self):
        result = fuse_risk_scores(0, 0)

        self.assertEqual(result["final_risk_score"], 0.0)
        self.assertEqual(result["final_risk_level"], "LOW")
        self.assertEqual(result["final_priority"], "P3")


if __name__ == "__main__":
    unittest.main()
