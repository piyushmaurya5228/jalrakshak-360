"""JalRakshak 360 AI + explainable risk fusion."""

def fuse_risk_scores(rule_risk_score, anomaly_score):
    """Combine explainable risk and AI anomaly signals."""
    # Keep the rule-based score as a safety floor:
    # absence of an anomaly must not make an existing risk look safer.
    rule_score = max(0.0, min(float(rule_risk_score), 100.0))
    anomaly_value = max(0.0, min(float(anomaly_score), 100.0))

    weighted_score = 0.70 * rule_score + 0.30 * anomaly_value
    final_score = round(max(rule_score, weighted_score), 2)

    if final_score >= 80:
        level = "CRITICAL"
        priority = "P1"
    elif final_score >= 60:
        level = "HIGH"
        priority = "P1"
    elif final_score >= 30:
        level = "WATCH"
        priority = "P2"
    else:
        level = "LOW"
        priority = "P3"

    return {
        "final_risk_score": final_score,
        "final_risk_level": level,
        "final_priority": priority,
    }


def add_fused_risk(df):
    """Add final fused risk values to a dataframe."""
    result = df.copy()

    fused = result.apply(
        lambda row: fuse_risk_scores(
            row["risk_score"],
            row["anomaly_score"],
        ),
        axis=1,
        result_type="expand",
    )

    return result.join(fused)


