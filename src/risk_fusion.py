"""JalRakshak 360 AI + explainable risk fusion."""

import math


def _validated_score(value, name):
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite numeric score.") from exc
    if not math.isfinite(score):
        raise ValueError(f"{name} must be a finite numeric score.")
    if not 0 <= score <= 100:
        raise ValueError(f"{name} must be between 0 and 100.")
    return score


def fuse_risk_scores(rule_risk_score, anomaly_score):
    """Combine explainable risk and AI anomaly signals."""
    rule_score = _validated_score(rule_risk_score, "Rule risk score")
    anomaly_value = _validated_score(anomaly_score, "Anomaly score")

    weighted_score = 0.70 * rule_score + 0.30 * anomaly_value
    final_score = round(max(rule_score, weighted_score), 2)

    if final_score >= 80:
        level, priority = "CRITICAL", "P1"
    elif final_score >= 60:
        level, priority = "HIGH", "P1"
    elif final_score >= 30:
        level, priority = "WATCH", "P2"
    else:
        level, priority = "LOW", "P3"

    return {
        "final_risk_score": final_score,
        "final_risk_level": level,
        "final_priority": priority,
    }


def add_fused_risk(df):
    """Add final fused risk values to a dataframe."""
    result = df.copy()
    fused = result.apply(
        lambda row: fuse_risk_scores(row["risk_score"], row["anomaly_score"]),
        axis=1,
        result_type="expand",
    )
    return result.join(fused)
