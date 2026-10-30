import unittest

from src.intervention import recommend_actions


class TestIntervention(unittest.TestCase):

    def make_result(self, **overrides):
        result = {
            "risk_level": "LOW",
            "rainfall_risk": 0,
            "groundwater_risk": 0,
            "historical_risk": 0,
        }
        result.update(overrides)
        return result

    def test_watch_location_can_have_p1_historical_action(self):
        actions = recommend_actions(
            self.make_result(
                risk_level="WATCH",
                historical_risk=50,
            )
        )

        self.assertIn(
            ("P2", "Schedule follow-up water testing"), actions
        )
        self.assertIn(
            ("P1", "Investigate repeated contamination pattern"),
            actions,
        )

    def test_historical_threshold_is_inclusive(self):
        below = recommend_actions(
            self.make_result(historical_risk=49.99)
        )
        at_threshold = recommend_actions(
            self.make_result(historical_risk=50)
        )

        action = ("P1", "Investigate repeated contamination pattern")
        self.assertNotIn(action, below)
        self.assertIn(action, at_threshold)

    def test_groundwater_threshold_is_inclusive(self):
        below = recommend_actions(
            self.make_result(groundwater_risk=69.99)
        )
        at_threshold = recommend_actions(
            self.make_result(groundwater_risk=70)
        )

        action = ("P1", "Assess alternate water source availability")
        self.assertNotIn(action, below)
        self.assertIn(action, at_threshold)

    def test_rainfall_threshold_is_inclusive(self):
        below = recommend_actions(
            self.make_result(rainfall_risk=74.99)
        )
        at_threshold = recommend_actions(
            self.make_result(rainfall_risk=75)
        )

        post_rain = ("P1", "Conduct post-rainfall water sampling")
        drainage = (
            "P2",
            "Inspect drainage and contamination pathways",
        )

        self.assertNotIn(post_rain, below)
        self.assertNotIn(drainage, below)
        self.assertIn(post_rain, at_threshold)
        self.assertIn(drainage, at_threshold)

    def test_low_risk_returns_routine_monitoring(self):
        actions = recommend_actions(self.make_result())

        self.assertEqual(
            actions,
            [("P3", "Continue routine monitoring")],
        )

    def test_critical_risk_returns_immediate_actions(self):
        actions = recommend_actions(
            self.make_result(risk_level="CRITICAL")
        )

        self.assertIn(
            ("P1", "Immediate water quality testing"), actions
        )
        self.assertIn(
            ("P1", "Inspect the drinking-water source"), actions
        )


if __name__ == "__main__":
    unittest.main()
