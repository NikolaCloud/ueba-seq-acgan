"""Tune a GPU XGBoost sequence detector on train, then chronologically refit."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.metrics import precision_recall_curve
from train_baseline import metrics, sequence_features

CONFIGS = [
    {"max_depth": 4, "eta": 0.08, "min_child_weight": 2, "scale_pos_weight": 30},
    {"max_depth": 6, "eta": 0.05, "min_child_weight": 2, "scale_pos_weight": 30},
    {"max_depth": 4, "eta": 0.05, "min_child_weight": 5, "scale_pos_weight": 100},
    {"max_depth": 6, "eta": 0.05, "min_child_weight": 5, "scale_pos_weight": 100},
    {"max_depth": 8, "eta": 0.03, "min_child_weight": 5, "scale_pos_weight": 30},
]


def load(directory: Path, split: str) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(directory / f"{split}.npz")
    return sequence_features(data["x"]), data["y"].astype(np.int8)


def parameters(candidate: dict, seed: int) -> dict:
    return {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "device": "cuda",
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_lambda": 3.0,
        "reg_alpha": 0.05,
        "max_bin": 256,
        "seed": seed,
        **candidate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_gpu_detector"))
    parser.add_argument("--rounds", type=int, default=700)
    parser.add_argument("--early-stopping", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    started = time.time()
    x_train, y_train = load(args.sequences, "train")
    x_validation, y_validation = load(args.sequences, "validation")
    x_test, y_test = load(args.sequences, "test")
    train_matrix = xgb.DMatrix(x_train, label=y_train)
    validation_matrix = xgb.DMatrix(x_validation, label=y_validation)
    test_matrix = xgb.DMatrix(x_test, label=y_test)

    candidates = []
    best = None
    best_validation_scores = None
    for index, candidate in enumerate(CONFIGS):
        model = xgb.train(
            parameters(candidate, args.seed),
            train_matrix,
            num_boost_round=args.rounds,
            evals=[(validation_matrix, "validation")],
            early_stopping_rounds=args.early_stopping,
            verbose_eval=False,
        )
        rounds = model.best_iteration + 1
        scores = model.predict(validation_matrix, iteration_range=(0, rounds))
        result = metrics(y_validation, scores)
        row = {"index": index, "parameters": candidate, "rounds": rounds, "validation": result}
        candidates.append(row)
        print(json.dumps(row), flush=True)
        if best is None or result["pr_auc"] > best[0]:
            best = (result["pr_auc"], candidate, rounds)
            best_validation_scores = scores

    precision, recall, thresholds = precision_recall_curve(y_validation, best_validation_scores)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    threshold_index = int(np.nanargmax(f1[:-1]))
    selected_threshold = float(thresholds[threshold_index])

    final_x = np.concatenate((x_train, x_validation))
    final_y = np.concatenate((y_train, y_validation))
    final_matrix = xgb.DMatrix(final_x, label=final_y)
    final_model = xgb.train(
        parameters(best[1], args.seed), final_matrix, num_boost_round=best[2], verbose_eval=False
    )
    train_scores = final_model.predict(final_matrix)
    test_scores = final_model.predict(test_matrix)
    report = {
        "model": "GPU XGBoost on 14-day sequence summaries",
        "selection": "configuration and rounds selected on validation; final refit on train+validation",
        "device": "cuda",
        "candidates": candidates,
        "selected_parameters": best[1],
        "selected_rounds": best[2],
        "validation_selected_threshold": selected_threshold,
        "validation_best_f1": float(f1[threshold_index]),
        "final_train_validation": metrics(final_y, train_scores),
        "test": metrics(y_test, test_scores),
        "elapsed_seconds": time.time() - started,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    final_model.save_model(args.artifact_dir / "model.ubj")
    (args.artifact_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["test"], indent=2))
    print(f"saved {args.artifact_dir}; elapsed={report['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
