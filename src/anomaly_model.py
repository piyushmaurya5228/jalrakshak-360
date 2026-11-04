"""JalRakshak 360 AI anomaly detection."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = [
    "water_contamination_rate",
    "rainfall_7d",
    "rainfall_normal",
    "groundwater_stress",
    "previous_contamination",
]


def _feature_matrix(df):
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Anomaly-model input must be a non-empty DataFrame.")
    missing = [column for column in FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Anomaly-model input is missing features: {missing}")
    features = df[FEATURES]
    try:
        values = features.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Anomaly-model features must be numeric.") from exc
    if not np.isfinite(values).all():
        raise ValueError("Anomaly-model features must contain only finite values.")
    return features


def train_anomaly_model(df, contamination=0.20, random_state=42):
    """Train Isolation Forest and retain its training-score reference."""
    features = _feature_matrix(df)
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    model.fit(features)
    training_severity = -model.decision_function(features)
    model.reference_anomaly_scores_ = np.sort(training_severity)
    return model


def add_anomaly_scores(df, model):
    """Score rows by empirical percentile against the training reference."""
    features = _feature_matrix(df)
    reference = getattr(model, "reference_anomaly_scores_", None)
    if reference is None or len(reference) == 0:
        raise ValueError(
            "Model has no training-score reference. "
            "Train it with train_anomaly_model() before scoring."
        )

    result = df.copy()
    result["anomaly_prediction"] = model.predict(features)
    severity = -model.decision_function(features)
    result["anomaly_score"] = (
        np.searchsorted(reference, severity, side="right")
        / len(reference)
        * 100.0
    ).round(2)
    return result
