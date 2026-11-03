"""Run independent train/calibration/holdout validation for JalRakshak 360."""
import argparse
import json
import sys
from pathlib import Path

# Add the repository root so "src" can be imported when this file is
# executed directly as: python scripts/evaluate_model.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.model_validation import evaluate_independent_model


def main():
    parser = argparse.ArgumentParser(description="Evaluate against expert-reviewed independent holdout labels.")
    parser.add_argument("--train-csv", default="data/validation/input/train.csv")
    parser.add_argument("--calibration-csv", default="data/validation/input/calibration.csv")
    parser.add_argument("--test-csv", default="data/validation/input/test.csv")
    parser.add_argument("--output-dir", default="reports/model_validation")
    parser.add_argument("--contamination", type=float, default=0.20)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    paths = [Path(args.train_csv), Path(args.calibration_csv), Path(args.test_csv)]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Validation input not found: {path}. Populate the templates "
                "in data/validation/templates/ using verified non-synthetic data."
            )

    train, calibration, test = (pd.read_csv(path) for path in paths)
    report, predictions = evaluate_independent_model(
        train, calibration, test,
        contamination=args.contamination,
        random_state=args.random_state,
    )
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "independent_holdout_metrics.json"
    predictions_path = output / "independent_holdout_predictions.csv"
    metrics_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    predictions.to_csv(predictions_path, index=False)

    print("INDEPENDENT MODEL VALIDATION COMPLETE")
    print("Training rows:", report["datasets"]["training"]["rows"])
    print("Calibration rows:", report["datasets"]["calibration"]["rows"])
    print("Holdout rows:", report["datasets"]["holdout_test"]["rows"])
    print("Selected calibration:", report["calibration"]["selected"])
    for name, metrics in report["holdout_metrics"].items():
        print(
            f"{name}: ROC-AUC={metrics['roc_auc']:.3f}, "
            f"F1={metrics['f1']:.3f}, Precision={metrics['precision']:.3f}, "
            f"Recall={metrics['recall']:.3f}"
        )
    print("Metrics:", metrics_path)
    print("Predictions:", predictions_path)
    print("Production scoring remains unchanged.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", type(exc).__name__, str(exc))
        raise
