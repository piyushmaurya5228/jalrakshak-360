"""JalRakshak 360 risk-score explainability utilities."""

import math
import pandas as pd

RISK_WEIGHTS = {
    "water_risk": 0.35,
    "rainfall_risk": 0.25,
    "groundwater_risk": 0.20,
    "historical_risk": 0.10,
    "exposure_risk": 0.10,
}

def _read_score(row, column):
    try:
        value = float(row[column])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid score: {column}") from exc

    if not math.isfinite(value):
        raise ValueError(f"Non-finite score: {column}")

    return value


def explain_risk_row(row):
    """Explain factor contributions and final risk fusion."""

    components = {
        name: _read_score(row, name)
        for name in RISK_WEIGHTS
    }

    rule_score = _read_score(row, "risk_score")
    anomaly_score = _read_score(row, "anomaly_score")

    if not 0 <= rule_score <= 100:
        raise ValueError("Rule score must be between 0 and 100.")

    if not 0 <= anomaly_score <= 100:
        raise ValueError("Anomaly score must be between 0 and 100.")

    contributions = {
        f"{name}_contribution": round(
            value * RISK_WEIGHTS[name], 2
        )
        for name, value in components.items()
    }

    reconstructed = round(
        sum(
            components[name] * weight
            for name, weight in RISK_WEIGHTS.items()
        ), 2
    )

    rounding_difference = round(rule_score - reconstructed, 2)

    weighted_rule = 0.70 * rule_score
    weighted_anomaly = 0.30 * anomaly_score
    fusion_candidate = weighted_rule + weighted_anomaly

    floor_applied = fusion_candidate < rule_score
    floor_adjustment = max(0.0, rule_score - fusion_candidate)

    final_score = round(max(rule_score, fusion_candidate), 2)

    return {
        **contributions,
        "rule_score_reconstructed": reconstructed,
        "rule_score_rounding_difference": rounding_difference,
        "weighted_rule_term": round(weighted_rule, 2),
        "weighted_anomaly_term": round(weighted_anomaly, 2),
        "fusion_candidate_score": round(fusion_candidate, 2),
        "rule_floor_applied": floor_applied,
        "rule_floor_adjustment": round(floor_adjustment, 2),
        "explained_final_risk_score": final_score,
        "anomaly_score_interpretation": (
            "RELATIVE_DATASET_NORMALIZED_NOT_PROBABILITY"
        ),
    }


def add_risk_explanations(df):
    """Append explanations without modifying original columns."""

    explanation_rows = [
        explain_risk_row(row)
        for _, row in df.iterrows()
    ]

    explanations = pd.DataFrame(
        explanation_rows, index=df.index
    )

    result = df.copy()

    for column in explanations.columns:
        result[column] = explanations[column]

    return result
