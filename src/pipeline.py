"""JalRakshak 360 central processing pipeline."""

import pandas as pd

from src.risk_engine import calculate_location_risk
from src.anomaly_model import train_anomaly_model, add_anomaly_scores
from src.risk_fusion import add_fused_risk


def load_and_process_data(path):
    """Load location data and generate final AI-fused risk scores."""
    df = pd.read_csv(path)

    risk_results = df.apply(
        calculate_location_risk,
        axis=1,
        result_type="expand",
    )

    df = pd.concat([df, risk_results], axis=1)

    model = train_anomaly_model(df)
    df = add_anomaly_scores(df, model)

    df = add_fused_risk(df)

    return df, model
