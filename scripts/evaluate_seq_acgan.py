"""Evaluate Seq-ACGAN detection and conditional synthetic sequence quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from ueba_seq_acgan.models import (
    SequenceDiscriminator,
    SequenceGenerator,
    StableSequenceDiscriminator,
    StableSequenceGenerator,
)


def load_split(path: Path, scaler: object) -> tuple[np.ndarray, np.ndarray]:
    raw = np.load(path)
    x, y = raw["x"].astype(np.float32), raw["y"].astype(np.int8)
    samples, length, features = x.shape
    x = scaler.transform(x.reshape(-1, features)).reshape(samples, length, features).astype(np.float32)
    return x, y


def summary_features(x: np.ndarray) -> np.ndarray:
    return np.concatenate((x[:, -1], x.mean(axis=1), x.std(axis=1), x.max(axis=1), x[:, -1] - x[:, 0]), axis=1)


def classification_metrics(y: np.ndarray, score: np.ndarray) -> dict[str, float | int | None]:
    output: dict[str, float | int | None] = {
        "samples": int(len(y)),
        "anomalies": int(y.sum()),
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)) if len(np.unique(y)) > 1 else None,
    }
    for budget in (50, 100, 500):
        top = np.argsort(score)[-min(budget, len(score)) :]
        output[f"recall_at_{budget}"] = float(y[top].sum() / max(1, y.sum()))
    return output


@torch.inference_mode()
def predict(discriminator: SequenceDiscriminator, x: np.ndarray, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    anomaly, source = [], []
    for start in range(0, len(x), 1024):
        source_logits, anomaly_logits = discriminator(torch.from_numpy(x[start : start + 1024]).to(device))
        anomaly.append(torch.softmax(anomaly_logits, dim=1)[:, 1].cpu().numpy())
        source.append(torch.sigmoid(source_logits).cpu().numpy())
    return np.concatenate(anomaly), np.concatenate(source)


def distribution_quality(real: np.ndarray, fake: np.ndarray) -> dict[str, float]:
    real_vectors, fake_vectors = real.mean(axis=1), fake.mean(axis=1)
    mean_gap = np.abs(real_vectors.mean(axis=0) - fake_vectors.mean(axis=0))
    std_gap = np.abs(real_vectors.std(axis=0) - fake_vectors.std(axis=0))
    return {
        "mean_absolute_feature_mean_gap": float(mean_gap.mean()),
        "mean_absolute_feature_std_gap": float(std_gap.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/seq_acgan/checkpoint.pt"))
    parser.add_argument("--scaler", type=Path, default=Path("artifacts/seq_acgan/scaler.joblib"))
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/sequences"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/seq_acgan/evaluation"))
    parser.add_argument("--synthetic-per-class", type=int, default=2000)
    parser.add_argument("--stable", action="store_true", help="Load the bounded stable Seq-ACGAN architecture")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state = torch.load(args.checkpoint, map_location=device, weights_only=True)
    generator_type = StableSequenceGenerator if args.stable or state.get("stable") else SequenceGenerator
    discriminator_type = StableSequenceDiscriminator if args.stable or state.get("stable") else SequenceDiscriminator
    generator = generator_type(state["feature_dim"]).to(device).eval()
    discriminator = discriminator_type(state["feature_dim"]).to(device).eval()
    generator.load_state_dict(state["generator"])
    discriminator.load_state_dict(state["discriminator"])
    scaler = joblib.load(args.scaler)
    train_x, train_y = load_split(args.sequences / "train.npz", scaler)
    validation_x, validation_y = load_split(args.sequences / "validation.npz", scaler)
    test_x, test_y = load_split(args.sequences / "test.npz", scaler)

    validation_scores, validation_source = predict(discriminator, validation_x, device)
    test_scores, test_source = predict(discriminator, test_x, device)
    labels = np.repeat(np.arange(2, dtype=np.int64), args.synthetic_per_class)
    with torch.inference_mode():
        noise = torch.randn(len(labels), state["sequence_length"], generator.latent_dim, device=device)
        synthetic = generator(noise, torch.from_numpy(labels).to(device)).cpu().numpy()
    fake_scores, fake_source = predict(discriminator, synthetic, device)

    # TSTR: a conventional detector gets synthetic sequences only, then sees real test data.
    tstr = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15, class_weight="balanced", random_state=42)
    tstr.fit(summary_features(synthetic), labels)
    tstr_scores = tstr.predict_proba(summary_features(test_x))[:, 1]
    result = {
        "anomaly_head": {"validation": classification_metrics(validation_y, validation_scores), "test": classification_metrics(test_y, test_scores)},
        "source_head": {"real_validation_probability_mean": float(validation_source.mean()), "real_test_probability_mean": float(test_source.mean()), "synthetic_probability_mean": float(fake_source.mean())},
        "distribution_quality_standardized": {
            "normal": distribution_quality(train_x[train_y == 0], synthetic[labels == 0]),
            "anomaly": distribution_quality(train_x[train_y == 1], synthetic[labels == 1]),
        },
        "tstr_synthetic_train_real_test": classification_metrics(test_y, tstr_scores),
        "caveat": "TSTR and distribution gaps assess usefulness, not a guarantee of realism. Synthetic augmentation is allowed only after validation quality gates pass.",
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.artifact_dir / "synthetic_sequences.npz", x=synthetic, y=labels)
    (args.artifact_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
