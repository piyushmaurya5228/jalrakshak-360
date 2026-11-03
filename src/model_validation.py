"""Independent, label-based validation utilities for JalRakshak 360."""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from src.anomaly_model import FEATURES, train_anomaly_model
from src.risk_engine import calculate_location_risk

META = ("site_id", "group_id", "data_source", "is_synthetic", "feature_as_of_date")
LABELS = (
    "ground_truth_label", "label_review_status", "label_source",
    "historical_window_end", "label_window_start", "label_window_end",
    "label_reviewed_at", "label_evidence_id", "label_protocol_version",
    "reviewer_code",
)
RISK_INPUTS = (
    "water_contamination_rate", "rainfall_7d", "rainfall_normal",
    "groundwater_stress", "population", "water_tests", "contaminated_tests",
)
WEIGHTS = tuple(float(round(x, 2)) for x in np.arange(0, 0.51, 0.05))
CUTOFFS = (30.0, 60.0, 80.0)


def _require(frame, columns, name):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _prepare(frame, name, labelled):
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError(f"{name} must be a non-empty DataFrame.")
    required = list(META) + list(FEATURES)
    if labelled:
        required += list(LABELS) + list(RISK_INPUTS)
    _require(frame, required, name)
    result = frame.copy()

    for col in ("site_id", "group_id"):
        result[col] = result[col].astype("string").str.strip()
        if result[col].isna().any() or result[col].eq("").any():
            raise ValueError(f"{name} contains blank {col} values.")

    source = result["data_source"].astype("string").str.strip()
    if source.isna().any() or source.eq("").any():
        raise ValueError(f"{name} contains blank data_source values.")

    feature_dates = pd.to_datetime(result["feature_as_of_date"], errors="coerce", utc=True)
    if feature_dates.isna().any():
        raise ValueError(f"{name} has missing or invalid feature_as_of_date values.")
    result["feature_as_of_date"] = feature_dates

    flags = result["is_synthetic"].astype("string").str.strip().str.casefold()
    false_flags, true_flags = {"false", "0", "no", "n"}, {"true", "1", "yes", "y"}
    if (~flags.isin(false_flags | true_flags)).any():
        raise ValueError(f"{name} has unrecognised is_synthetic values.")
    if flags.isin(true_flags).any():
        raise ValueError(f"{name} contains synthetic rows; real-data validation refused.")

    numeric = list(FEATURES) + (list(RISK_INPUTS) if labelled else [])
    for col in numeric:
        result[col] = pd.to_numeric(result[col], errors="coerce")
        if not np.isfinite(result[col].to_numpy(dtype=float)).all():
            raise ValueError(f"{name} has missing/non-finite values in {col}.")

    if result.groupby("site_id")["group_id"].nunique().gt(1).any():
        raise ValueError(f"{name} maps one site_id to multiple group_id values.")

    for col in ("water_contamination_rate", "groundwater_stress", "previous_contamination"):
        if (result[col] < 0).any() or (result[col] > 1).any():
            raise ValueError(f"{name} {col} must be between 0 and 1.")
    if (result[["rainfall_7d", "rainfall_normal"]] < 0).any().any():
        raise ValueError(f"{name} contains negative rainfall values.")

    if labelled:
        status = result["label_review_status"].astype("string").str.strip().str.upper()
        if status.isna().any() or not status.eq("EXPERT_VERIFIED").all():
            raise ValueError(f"{name} labels must have label_review_status=EXPERT_VERIFIED.")
        text_fields = (
            "label_source", "label_evidence_id",
            "label_protocol_version", "reviewer_code",
        )
        for col in text_fields:
            values = result[col].astype("string").str.strip()
            if values.isna().any() or values.eq("").any():
                raise ValueError(f"{name} has blank {col} values.")
            result[col] = values

        date_fields = (
            "historical_window_end", "label_window_start",
            "label_window_end", "label_reviewed_at",
        )
        for col in date_fields:
            parsed = pd.to_datetime(result[col], errors="coerce", utc=True)
            if parsed.isna().any():
                raise ValueError(f"{name} has missing or invalid {col} values.")
            result[col] = parsed

        if (result["historical_window_end"] > result["feature_as_of_date"]).any():
            raise ValueError(
                f"{name} historical_window_end must be on or before feature_as_of_date."
            )
        if (result["label_window_start"] <= result["feature_as_of_date"]).any():
            raise ValueError(
                f"{name} label_window_start must be after feature_as_of_date."
            )
        if (result["label_window_end"] < result["label_window_start"]).any():
            raise ValueError(f"{name} label_window_end cannot precede label_window_start.")
        if (result["label_reviewed_at"] < result["label_window_end"]).any():
            raise ValueError(f"{name} labels cannot be reviewed before the outcome window ends.")

        labels = pd.to_numeric(result["ground_truth_label"], errors="coerce")
        if labels.isna().any() or not labels.isin([0, 1]).all() or labels.nunique() != 2:
            raise ValueError(f"{name} ground_truth_label must contain both 0 and 1 only.")
        result["ground_truth_label"] = labels.astype(int)
        counts = ["population", "water_tests", "contaminated_tests"]
        if (result[counts] < 0).any().any():
            raise ValueError(f"{name} has negative population or test counts.")
        if (result["contaminated_tests"] > result["water_tests"]).any():
            raise ValueError(f"{name} contaminated_tests cannot exceed water_tests.")
    return result


def _check_disjoint(train, calibration, test):
    partitions = {"training": train, "calibration": calibration, "holdout test": test}
    names = list(partitions)
    for i, left_name in enumerate(names):
        for right_name in names[i + 1:]:
            left, right = partitions[left_name], partitions[right_name]
            sites = set(left.site_id) & set(right.site_id)
            groups = set(left.group_id) & set(right.group_id)
            if sites or groups:
                raise ValueError(
                    f"Site/geographic group leakage between {left_name} and {right_name}: "
                    f"sites={sorted(sites)[:5]}, groups={sorted(groups)[:5]}"
                )


def _anomaly_percentile(model, train, scored):
    """Rank anomaly severity against training scores, not the scored batch."""
    reference = np.sort(-model.decision_function(train[FEATURES]))
    values = -model.decision_function(scored[FEATURES])
    return np.searchsorted(reference, values, side="right") / len(reference) * 100.0


def _rule_scores(frame):
    return np.asarray([calculate_location_risk(row)["risk_score"] for _, row in frame.iterrows()])


def _fuse(rule, anomaly, anomaly_weight):
    candidate = (1.0 - anomaly_weight) * rule + anomaly_weight * anomaly
    return np.maximum(rule, candidate)


def _metrics(labels, scores, cutoff):
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    predicted = (scores >= cutoff).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predicted, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
        "cutoff": float(cutoff),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "true_negatives": int(tn), "false_positives": int(fp),
        "false_negatives": int(fn), "true_positives": int(tp),
        "negative_support": int((labels == 0).sum()),
        "positive_support": int((labels == 1).sum()),
    }


def _calibrate(rule, anomaly, labels):
    candidates = []
    for weight in WEIGHTS:
        fused = _fuse(rule, anomaly, weight)
        for cutoff in CUTOFFS:
            pred = (fused >= cutoff).astype(int)
            candidates.append({
                "anomaly_weight": weight,
                "rule_weight": round(1.0 - weight, 2),
                "risk_cutoff": cutoff,
                "precision": float(precision_score(labels, pred, zero_division=0)),
                "recall": float(recall_score(labels, pred, zero_division=0)),
                "f1": float(f1_score(labels, pred, zero_division=0)),
            })
    best = max(candidates, key=lambda x: (x["f1"], x["recall"], -x["anomaly_weight"], x["risk_cutoff"]))
    return best, candidates


def evaluate_independent_model(training_df, calibration_df, test_df, contamination=0.20, random_state=42):
    """Fit, calibrate and evaluate on three non-overlapping real-data partitions."""
    train = _prepare(training_df, "training", False)
    calibration = _prepare(calibration_df, "calibration", True)
    test = _prepare(test_df, "holdout test", True)
    _check_disjoint(train, calibration, test)
    if train["site_id"].nunique() < 10:
        raise ValueError("Training data must contain at least 10 unique sites.")
    for partition_name, partition in (
        ("training", train),
        ("calibration", calibration),
        ("holdout test", test),
    ):
        if partition["group_id"].nunique() < 2:
            raise ValueError(
                f"{partition_name} must contain at least 2 geographic groups."
            )

    model = train_anomaly_model(train, contamination=contamination, random_state=random_state)
    cal_anomaly = _anomaly_percentile(model, train, calibration)
    test_anomaly = _anomaly_percentile(model, train, test)
    cal_rule, test_rule = _rule_scores(calibration), _rule_scores(test)
    selected, candidates = _calibrate(cal_rule, cal_anomaly, calibration.ground_truth_label.to_numpy())
    test_fused = _fuse(test_rule, test_anomaly, selected["anomaly_weight"])
    labels, cutoff = test.ground_truth_label.to_numpy(), selected["risk_cutoff"]

    report = {
        "status": "INDEPENDENT_HOLDOUT_EVALUATED",
        "model": "IsolationForest",
        "contamination": float(contamination),
        "random_state": int(random_state),
        "anomaly_score_method": "Empirical percentile against training anomaly scores; separate from production batch min-max scores.",
        "label_definition": "1=elevated risk and 0=not elevated under one documented expert-approved protocol.",
        "label_requirement": "Calibration and holdout labels are declared EXPERT_VERIFIED in the supplied files.",
        "split_policy": "site_id and geographic group_id are disjoint across training, calibration and holdout test.",
        "temporal_policy": (
            "Features are frozen at feature_as_of_date; historical water-test inputs end "
            "on or before that date; outcome labels begin after that date; label review "
            "is recorded on or after the outcome-window end. Dates are declared metadata "
            "and are not independently authenticated by this script."
        ),
        "label_protocol_versions": sorted(
            set(calibration["label_protocol_version"].astype(str))
            | set(test["label_protocol_version"].astype(str))
        ),
        "datasets": {
            name: {
                "rows": int(len(frame)),
                "unique_sites": int(frame.site_id.nunique()),
                "unique_geographic_groups": int(frame.group_id.nunique()),
                "data_sources": sorted(frame.data_source.astype(str).unique().tolist()),
            }
            for name, frame in (
                ("training", train), ("calibration", calibration), ("holdout_test", test)
            )
        },
        "calibration": {
            "selection_objective": "Maximum F1 on calibration data",
            "selected": selected,
            "candidate_weights": list(WEIGHTS),
            "candidate_cutoffs": list(CUTOFFS),
            "candidates": candidates,
            "note": "Research suggestion only; domain experts must approve operating settings.",
        },
        "holdout_metrics": {
            "rule_only": _metrics(labels, test_rule, cutoff),
            "anomaly_only": _metrics(labels, test_anomaly, cutoff),
            "calibrated_fusion": _metrics(labels, test_fused, cutoff),
        },
        "limitations": [
            "Declared provenance and label status are checked but source files and reviewer qualifications are not authenticated by code.",
            "The holdout test set must never be used for tuning.",
            "This workflow does not change production weights, thresholds or scores.",
        ],
    }
    predictions = pd.DataFrame({
        "site_id": test.site_id.to_numpy(),
        "group_id": test.group_id.to_numpy(),
        "data_source": test.data_source.to_numpy(),
        "ground_truth_label": labels,
        "rule_risk_score": np.round(test_rule, 2),
        "anomaly_percentile_score": np.round(test_anomaly, 2),
        "calibrated_fused_score": np.round(test_fused, 2),
        "predicted_elevated_risk": (test_fused >= cutoff).astype(int),
    })
    return report, predictions
