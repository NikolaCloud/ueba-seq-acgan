"""Evaluate a frozen UEBA detector on an independent CERT release."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from ueba_seq_acgan.risk import sequence_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts/r4.2_final_raw_baseline"))
    parser.add_argument("--input", type=Path, default=Path("data/processed/r5.2_sequences/test.npz"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/external-validation/r5.2_test.json"))
    args = parser.parse_args()
    artifact = joblib.load(args.model_dir / "model.joblib")
    data = np.load(args.input); y = data["y"].astype(np.int8)
    scores = artifact["model"].predict_proba(artifact["scaler"].transform(sequence_summary(data["x"])))[:, 1]
    report: dict[str, float | int] = {"samples": int(len(y)), "anomalies": int(y.sum()), "pr_auc": float(average_precision_score(y, scores)), "roc_auc": float(roc_auc_score(y, scores))}
    for budget in (50, 100, 500, 1000):
        top = np.argsort(scores)[-budget:]
        report[f"recall_at_{budget}"] = float(y[top].sum() / y.sum())
        report[f"precision_at_{budget}"] = float(y[top].mean())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
