"""Train and evaluate a chronological, non-generative UEBA baseline.

The classifier consumes summary features from each 14-day sequence.  It is a
benchmark only: no synthetic samples and no data beyond the training boundary
are used to fit its scaler or classifier.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
from sklearn.preprocessing import RobustScaler


def sequence_features(sequences: np.ndarray) -> np.ndarray:
    """Convert (samples, time, features) to level, variation and trend features."""
    last = sequences[:, -1, :]
    mean = sequences.mean(axis=1)
    std = sequences.std(axis=1)
    maximum = sequences.max(axis=1)
    trend = sequences[:, -1, :] - sequences[:, 0, :]
    return np.concatenate((last, mean, std, maximum, trend), axis=1)


def load_split(directory: Path, split: str) -> tuple[np.ndarray, np.ndarray]:
    payload = np.load(directory / f"{split}.npz")
    return sequence_features(payload["x"]), payload["y"].astype(np.int8)


def metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float | int | None]:
    result: dict[str, float | int | None] = {
        "samples": int(len(labels)),
        "anomalies": int(labels.sum()),
        "pr_auc": float(average_precision_score(labels, scores)),
        "roc_auc": float(roc_auc_score(labels, scores)) if len(np.unique(labels)) > 1 else None,
    }
    for budget in (50, 100, 500):
        selected = np.argsort(scores)[-min(budget, len(scores)) :]
        result[f"recall_at_{budget}"] = float(labels[selected].sum() / max(1, labels.sum()))
        result[f"precision_at_{budget}"] = float(labels[selected].mean())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/sequences"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/baseline"))
    parser.add_argument("--train-with-validation", action="store_true", help="Refit final model on train+validation before the one-time test evaluation")
    args = parser.parse_args()

    x_train, y_train = load_split(args.sequences, "train")
    x_validation, y_validation = load_split(args.sequences, "validation")
    x_test, y_test = load_split(args.sequences, "test")
    if args.train_with_validation:
        x_train = np.concatenate((x_train, x_validation))
        y_train = np.concatenate((y_train, y_validation))
    scaler = RobustScaler().fit(x_train)
    x_train, x_validation, x_test = map(scaler.transform, (x_train, x_validation, x_test))
    model = HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=250,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=42,
    ).fit(x_train, y_train)

    validation_scores = model.predict_proba(x_validation)[:, 1]
    test_scores = model.predict_proba(x_test)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_validation, validation_scores)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    best_index = int(np.nanargmax(f1[:-1]))
    threshold = float(thresholds[best_index])

    report = {
        "model": "HistGradientBoostingClassifier sequence-summary baseline",
        "train_with_validation": args.train_with_validation,
        "train": metrics(y_train, model.predict_proba(x_train)[:, 1]),
        "validation": metrics(y_validation, validation_scores),
        "test": metrics(y_test, test_scores),
        "validation_selected_threshold": threshold,
        "validation_best_f1": float(f1[best_index]),
        "test_at_validation_threshold": {
            "precision": float(((test_scores >= threshold) & (y_test == 1)).sum() / max(1, (test_scores >= threshold).sum())),
            "recall": float(((test_scores >= threshold) & (y_test == 1)).sum() / max(1, y_test.sum())),
            "alerts": int((test_scores >= threshold).sum()),
        },
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "model": model}, args.artifact_dir / "model.joblib")
    (args.artifact_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
