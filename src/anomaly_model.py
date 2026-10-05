"""JalRakshak 360 AI anomaly detection."""

import pandas as pd
from sklearn.ensemble import IsolationForest


FEATURES = [
    "water_contamination_rate",
    "rainfall_7d",
    "rainfall_normal",
    "groundwater_stress",
    "previous_contamination",
]


def train_anomaly_model(df, contamination=0.20, random_state=42):
    """Train an Isolation Forest on environmental risk features."""
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )

    model.fit(df[FEATURES])

    return model


def add_anomaly_scores(df, model):
    """Add anomaly prediction and normalized anomaly score."""
    result = df.copy()

    result["anomaly_prediction"] = model.predict(result[FEATURES])

    raw_scores = model.decision_function(result[FEATURES])

    min_score = raw_scores.min()
    max_score = raw_scores.max()

    if max_score == min_score:
        result["anomaly_score"] = 50.0
    else:
        result["anomaly_score"] = (
            (max_score - raw_scores)
            / (max_score - min_score)
            * 100
        )

    result["anomaly_score"] = result["anomaly_score"].round(2)

    return result
