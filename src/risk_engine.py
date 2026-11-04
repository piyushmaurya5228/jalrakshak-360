"""JalRakshak 360 risk scoring engine."""

import math


def _finite_number(value, name):
    """Convert a scoring input to a finite float or reject it."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite numeric value.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite numeric value.")
    return number


def _score_component(value, name):
    """Validate a component already expressed on the 0-100 risk scale."""
    number = _finite_number(value, name)
    if not 0 <= number <= 100:
        raise ValueError(f"{name} must be between 0 and 100.")
    return number


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(_finite_number(value, "Risk component"), maximum))


def rainfall_risk(rainfall_7d, rainfall_normal):
    """Convert rainfall anomaly into a smoothly interpolated 0-100 score."""
    rainfall = _finite_number(rainfall_7d, "Seven-day rainfall")
    normal = _finite_number(rainfall_normal, "Normal rainfall baseline")
    if rainfall < 0:
        raise ValueError("Seven-day rainfall must be non-negative.")
    if normal <= 0:
        raise ValueError("Normal rainfall baseline must be greater than zero.")

    anomaly = ((rainfall - normal) / normal) * 100

    if anomaly <= 0:
        relative_rainfall = rainfall / normal
        return round(clamp(relative_rainfall * 10.0, 0.0, 10.0), 2)

    anchors = [
        (0.0, 10.0),
        (25.0, 30.0),
        (50.0, 55.0),
        (75.0, 75.0),
        (100.0, 100.0),
    ]

    for (left_x, left_score), (right_x, right_score) in zip(anchors, anchors[1:]):
        if anomaly <= right_x:
            fraction = (anomaly - left_x) / (right_x - left_x)
            score = left_score + fraction * (right_score - left_score)
            return round(clamp(score), 2)

    return 100.0


def exposure_risk(population):
    """Convert exposed population into a 0-100 score."""
    population = _finite_number(population, "Population")
    if population < 0:
        raise ValueError("Population values must be non-negative.")
    return clamp((population / 10000) * 100)


def calculate_risk(
    water_risk,
    rainfall_risk_score,
    groundwater_risk,
    historical_risk,
    exposure_risk_score,
):
    """Calculate the explainable weighted risk score."""
    water = _score_component(water_risk, "Water risk")
    rainfall = _score_component(rainfall_risk_score, "Rainfall risk")
    groundwater = _score_component(groundwater_risk, "Groundwater risk")
    historical = _score_component(historical_risk, "Historical risk")
    exposure = _score_component(exposure_risk_score, "Exposure risk")

    score = (
        0.35 * water
        + 0.25 * rainfall
        + 0.20 * groundwater
        + 0.10 * historical
        + 0.10 * exposure
    )
    score = round(clamp(score), 2)

    if score >= 80:
        level, priority = "CRITICAL", "P1"
    elif score >= 60:
        level, priority = "HIGH", "P1"
    elif score >= 30:
        level, priority = "WATCH", "P2"
    else:
        level, priority = "LOW", "P3"

    return score, level, priority


def calculate_location_risk(row):
    """Calculate risk for one row, rejecting invalid scoring evidence."""
    water_rate = _finite_number(row["water_contamination_rate"], "Water contamination rate")
    groundwater_rate = _finite_number(row["groundwater_stress"], "Groundwater stress")
    water_tests = _finite_number(row["water_tests"], "Water test count")
    contaminated_tests = _finite_number(row["contaminated_tests"], "Contaminated test count")

    if not 0 <= water_rate <= 1:
        raise ValueError("Water contamination rate must be between 0 and 1.")
    if not 0 <= groundwater_rate <= 1:
        raise ValueError("Groundwater stress must be between 0 and 1.")
    if water_tests <= 0:
        raise ValueError("At least one water test is required for risk scoring.")
    if not 0 <= contaminated_tests <= water_tests:
        raise ValueError("Contaminated test count must be between zero and total tests.")

    water = clamp(water_rate * 100)
    rain = rainfall_risk(row["rainfall_7d"], row["rainfall_normal"])
    groundwater = clamp(groundwater_rate * 100)
    historical = clamp((contaminated_tests / water_tests) * 100)
    exposure = exposure_risk(row["population"])

    score, level, priority = calculate_risk(water, rain, groundwater, historical, exposure)
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
