"""Evaluate a normal-only Seq-GAN without exposing anomaly labels to training.

The threshold scaling is fitted on the normal portion of the *training* split.
Validation and test labels are read only after scoring to report held-out quality.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

from ueba_seq_acgan.models import NormalSequenceDecoder, NormalSequenceEncoder, StableSequenceDiscriminator


def load_split(path: Path, transformer):
    raw = np.load(path)
    x = raw["x"].astype("float32")
    x = transformer.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype("float32")
    return x, raw["y"].astype("int8")


@torch.inference_mode()
def score(encoder, decoder, discriminator, x: np.ndarray, device: torch.device):
    errors, pseudo_prob = [], []
    for start in range(0, len(x), 1024):
        batch = torch.from_numpy(x[start : start + 1024]).to(device)
        reconstruction = decoder(encoder(batch), batch.size(1))
        _, logits = discriminator(batch)
        errors.append(((reconstruction - batch).abs().mean(dim=(1, 2))).cpu().numpy())
        pseudo_prob.append(torch.softmax(logits, dim=1)[:, 1].cpu().numpy())
    return np.concatenate(errors), np.concatenate(pseudo_prob)


def report(y: np.ndarray, s: np.ndarray) -> dict[str, float]:
    order = np.argsort(s)[::-1]
    positives = max(int(y.sum()), 1)
    return {
        "pr_auc": float(average_precision_score(y, s)),
        "roc_auc": float(roc_auc_score(y, s)),
        "precision_at_100": float(y[order[:100]].mean()),
        "recall_at_100": float(y[order[:100]].sum() / positives),
        "recall_at_500": float(y[order[:500]].sum() / positives),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_seq_gan_mitre"))
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    args = parser.parse_args()
    device = torch.device("cpu")
    checkpoint = torch.load(args.artifact_dir / "checkpoint.pt", map_location=device, weights_only=True)
    encoder = NormalSequenceEncoder(checkpoint["feature_dim"]).eval()
    decoder = NormalSequenceDecoder(checkpoint["feature_dim"]).eval()
    discriminator = StableSequenceDiscriminator(checkpoint["feature_dim"]).eval()
    encoder.load_state_dict(checkpoint["encoder"])
    decoder.load_state_dict(checkpoint["decoder"])
    discriminator.load_state_dict(checkpoint["discriminator"])
    transformer = joblib.load(args.artifact_dir / "transformer.joblib")

    train_x, train_y = load_split(args.sequences / "train.npz", transformer)
    val_x, val_y = load_split(args.sequences / "validation.npz", transformer)
    test_x, test_y = load_split(args.sequences / "test.npz", transformer)
    train_error, _ = score(encoder, decoder, discriminator, train_x[train_y == 0], device)
    lo, hi = np.quantile(train_error, [0.50, 0.99])

    def combined(x):
        reconstruction_error, discriminator_probability = score(encoder, decoder, discriminator, x, device)
        reconstruction_score = np.clip((reconstruction_error - lo) / max(hi - lo, 1e-8), 0, 1)
        return 0.7 * reconstruction_score + 0.3 * discriminator_probability

    val_score, test_score = combined(val_x), combined(test_x)
    output = {
        "method": "normal-only adversarial sequence autoencoder",
        "training_labels_used": "normal records only; no observed anomaly labels",
        "score": "0.7 calibrated reconstruction deviation + 0.3 pseudo-anomaly discriminator probability",
        "normal_error_calibration": {"median": float(lo), "p99": float(hi)},
        "validation": report(val_y, val_score),
        "test": report(test_y, test_score),
    }
    (args.artifact_dir / "evaluation.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
