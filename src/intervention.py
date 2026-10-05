"""JalRakshak 360 intervention recommendation engine."""

def recommend_actions(result):
    """Return prioritized actions based on risk components."""
    actions = []

    if result["risk_level"] == "CRITICAL":
        actions.append(("P1", "Immediate water quality testing"))
        actions.append(("P1", "Inspect the drinking-water source"))

    elif result["risk_level"] == "HIGH":
        actions.append(("P1", "Priority water quality testing"))
        actions.append(("P1", "Inspect the vulnerable water source"))

    elif result["risk_level"] == "WATCH":
        actions.append(("P2", "Schedule follow-up water testing"))

    else:
        actions.append(("P3", "Continue routine monitoring"))

    if result["rainfall_risk"] >= 75:
        actions.append(("P1", "Conduct post-rainfall water sampling"))
        actions.append(("P2", "Inspect drainage and contamination pathways"))

    if result["groundwater_risk"] >= 70:
        actions.append(("P1", "Assess alternate water source availability"))

    if result["historical_risk"] >= 50:
        actions.append(("P1", "Investigate repeated contamination pattern"))

    return actions
