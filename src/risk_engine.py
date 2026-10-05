"""JalRakshak 360 risk scoring engine."""

def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(float(value), maximum))


def rainfall_risk(rainfall_7d, rainfall_normal):
    """Convert rainfall anomaly into a 0-100 risk score."""
    if rainfall_normal <= 0:
        return 0.0

    anomaly = ((rainfall_7d - rainfall_normal) / rainfall_normal) * 100

    if anomaly <= 0:
        return 10.0
    if anomaly <= 25:
        return 30.0
    if anomaly <= 50:
        return 55.0
    if anomaly <= 75:
        return 75.0
    return 100.0


def exposure_risk(population):
    """Convert exposed population into a 0-100 score."""
    return clamp((population / 10000) * 100)


def calculate_risk(
    water_risk,
    rainfall_risk_score,
    groundwater_risk,
    historical_risk,
    exposure_risk_score,
):
    """Calculate the explainable weighted risk score."""
    score = (
        0.35 * water_risk
        + 0.25 * rainfall_risk_score
        + 0.20 * groundwater_risk
        + 0.10 * historical_risk
        + 0.10 * exposure_risk_score
    )

    score = round(clamp(score), 2)

    if score >= 80:
        level = "CRITICAL"
        priority = "P1"
    elif score >= 60:
        level = "HIGH"
        priority = "P1"
    elif score >= 30:
        level = "WATCH"
        priority = "P2"
    else:
        level = "LOW"
        priority = "P3"

    return score, level, priority


def calculate_location_risk(row):
    """Calculate risk for one dataframe row."""
    water = clamp(row["water_contamination_rate"] * 100)

    rain = rainfall_risk(
        row["rainfall_7d"],
        row["rainfall_normal"],
    )

    groundwater = clamp(row["groundwater_stress"] * 100)

    if row["water_tests"] > 0:
        historical = (
            row["contaminated_tests"] / row["water_tests"]
        ) * 100
    else:
        historical = 0.0

    historical = clamp(historical)

    exposure = exposure_risk(row["population"])

    score, level, priority = calculate_risk(
        water,
        rain,
        groundwater,
        historical,
        exposure,
    )

    return {
        "risk_score": score,
        "risk_level": level,
        "priority": priority,
        "water_risk": round(water, 2),
        "rainfall_risk": round(rain, 2),
        "groundwater_risk": round(groundwater, 2),
        "historical_risk": round(historical, 2),
        "exposure_risk": round(exposure, 2),
    }
