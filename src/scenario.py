"""JalRakshak 360 what-if scenario engine."""

import pandas as pd

from src.risk_engine import calculate_location_risk


def simulate_rainfall(row, rainfall_change_percent):
    """Simulate a change in 7-day rainfall and recalculate rule-based risk."""
    simulated = row.copy()

    simulated["rainfall_7d"] = (
        float(row["rainfall_7d"])
        * (1 + float(rainfall_change_percent) / 100)
    )

    result = calculate_location_risk(simulated)

    return {
        "original_rainfall": round(float(row["rainfall_7d"]), 2),
        "simulated_rainfall": round(float(simulated["rainfall_7d"]), 2),
        "rainfall_change_percent": float(rainfall_change_percent),
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "priority": result["priority"],
        "rainfall_risk": result["rainfall_risk"],
    }


def simulate_dataset(df, rainfall_change_percent):
    """Run a rainfall scenario for every location."""
    rows = []

    for _, row in df.iterrows():
        result = simulate_rainfall(row, rainfall_change_percent)

        rows.append({
            "village": row["village"],
            "district": row["district"],
            **result,
        })

    return pd.DataFrame(rows).sort_values(
        "risk_score",
        ascending=False,
    ).reset_index(drop=True)
