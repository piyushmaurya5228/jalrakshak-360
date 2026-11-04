import unittest
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from src.anomaly_model import FEATURES
from src.model_validation import _anomaly_percentile, evaluate_independent_model


def make_data(prefix, n, labelled=False):
    rows = []
    for i in range(n):
        y = i % 2
        row = {
            "site_id": f"{prefix}_SITE_{i}",
            "group_id": f"{prefix}_GROUP_{i}",
            "data_source": "unit-test-fixture",
            "is_synthetic": False,
            "feature_as_of_date": "2024-01-31",
            "water_contamination_rate": 0.15 + 0.55 * y + (i % 5) * 0.01,
            "rainfall_7d": 20 + 100 * y + i,
            "rainfall_normal": 70 + i,
            "groundwater_stress": 0.20 + 0.60 * y,
            "previous_contamination": 0.10 + 0.70 * y,
        }
        if labelled:
            row.update({
                "population": 1000 + i * 100,
                "water_tests": 10,
                "contaminated_tests": 1 + 7 * y,
                "ground_truth_label": y,
                "label_review_status": "EXPERT_VERIFIED",
                "label_source": "unit-test-fixture",
                "historical_window_end": "2024-01-31",
                "label_window_start": "2024-02-01",
                "label_window_end": "2024-03-01",
                "label_reviewed_at": "2024-03-05",
                "label_evidence_id": f"{prefix}_EVIDENCE_{i}",
                "label_protocol_version": "unit-test-v1",
                "reviewer_code": "reviewer-fixture",
            })
        rows.append(row)
    return pd.DataFrame(rows)


class TestIndependentModelValidation(unittest.TestCase):
    def test_training_reference_percentiles_are_bounded(self):
        train = make_data("TRAIN", 20)
        model = IsolationForest(n_estimators=50, contamination=0.2, random_state=42)
        model.fit(train[FEATURES])
        scores = _anomaly_percentile(model, train, train)
        self.assertTrue(np.isfinite(scores).all())
        self.assertTrue(((scores >= 0) & (scores <= 100)).all())

    def test_independent_evaluation_reports_three_comparators(self):
        report, predictions = evaluate_independent_model(
            make_data("TRAIN", 24),
            make_data("CAL", 12, labelled=True),
            make_data("TEST", 12, labelled=True),
        )
        self.assertEqual(report["status"], "INDEPENDENT_HOLDOUT_EVALUATED")
        self.assertEqual(set(report["holdout_metrics"]), {
            "rule_only", "anomaly_only", "calibrated_fusion"
        })
        self.assertEqual(len(predictions), 12)

    def test_synthetic_rows_are_rejected(self):
        train = make_data("TRAIN", 12)
        train.loc[0, "is_synthetic"] = True
        with self.assertRaisesRegex(ValueError, "synthetic rows"):
            evaluate_independent_model(
                train, make_data("CAL", 8, True), make_data("TEST", 8, True)
            )

    def test_unreviewed_labels_are_rejected(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_review_status"] = "PENDING"
        with self.assertRaisesRegex(ValueError, "EXPERT_VERIFIED"):
            evaluate_independent_model(make_data("TRAIN", 12), cal, make_data("TEST", 8, True))

    def test_missing_label_review_status_is_rejected(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_review_status"] = None
        with self.assertRaisesRegex(ValueError, "EXPERT_VERIFIED"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_training_requires_ten_unique_sites(self):
        train = make_data("TRAIN", 12)
        train["site_id"] = "ONE_SITE"
        train["group_id"] = "ONE_GROUP"
        with self.assertRaisesRegex(ValueError, "10 unique sites"):
            evaluate_independent_model(
                train, make_data("CAL", 8, True), make_data("TEST", 8, True)
            )

    def test_geographic_overlap_is_rejected(self):
        train, cal, test = make_data("TRAIN", 12), make_data("CAL", 8, True), make_data("TEST", 8, True)
        cal.loc[0, "group_id"] = train.loc[0, "group_id"]
        with self.assertRaisesRegex(ValueError, "leakage"):
            evaluate_independent_model(train, cal, test)

    def test_feature_date_must_be_valid(self):
        train = make_data("TRAIN", 12)
        train.loc[0, "feature_as_of_date"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "feature_as_of_date"):
            evaluate_independent_model(
                train, make_data("CAL", 8, True), make_data("TEST", 8, True)
            )

    def test_historical_inputs_must_end_before_feature_cutoff(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "historical_window_end"] = "2024-02-02"
        with self.assertRaisesRegex(ValueError, "historical_window_end"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_outcome_window_must_follow_feature_cutoff(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_window_start"] = "2024-01-31"
        with self.assertRaisesRegex(ValueError, "label_window_start"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_outcome_window_end_cannot_precede_start(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_window_end"] = "2024-01-30"
        with self.assertRaisesRegex(ValueError, "label_window_end"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_labels_cannot_be_reviewed_before_outcome_window_ends(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_reviewed_at"] = "2024-02-20"
        with self.assertRaisesRegex(ValueError, "reviewed before"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_label_evidence_metadata_is_required(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "label_evidence_id"] = " "
        with self.assertRaisesRegex(ValueError, "label_evidence_id"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_zero_rainfall_baseline_is_rejected(self):
        train = make_data("TRAIN", 12)
        train.loc[0, "rainfall_normal"] = 0
        with self.assertRaisesRegex(ValueError, "rainfall_normal must be greater than zero"):
            evaluate_independent_model(
                train, make_data("CAL", 8, True), make_data("TEST", 8, True)
            )

    def test_zero_water_tests_are_rejected(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "water_tests"] = 0
        with self.assertRaisesRegex(ValueError, "water_tests must be greater than zero"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_fractional_water_test_counts_are_rejected(self):
        cal = make_data("CAL", 8, True)
        cal["contaminated_tests"] = cal["contaminated_tests"].astype(float)
        cal.loc[0, "contaminated_tests"] = 1.5
        with self.assertRaisesRegex(ValueError, "whole numbers"):
            evaluate_independent_model(
                make_data("TRAIN", 12), cal, make_data("TEST", 8, True)
            )

    def test_contaminated_tests_cannot_exceed_total(self):
        cal = make_data("CAL", 8, True)
        cal.loc[0, "contaminated_tests"] = 11
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            evaluate_independent_model(make_data("TRAIN", 12), cal, make_data("TEST", 8, True))


if __name__ == "__main__":
    unittest.main()
