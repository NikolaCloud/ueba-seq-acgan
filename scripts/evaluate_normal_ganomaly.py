"""Held-out evaluation for strict normal-only sequential GANomaly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

from ueba_seq_acgan.models import GANomalySequenceDecoder, GANomalySequenceDiscriminator, GANomalySequenceEncoder


def load(path: Path, transformer):
    raw = np.load(path)
    x = raw["x"].astype("float32")
    return transformer.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype("float32"), raw["y"].astype("int8")


@torch.inference_mode()
def components(encoder, decoder, encoder2, discriminator, x, device):
    reconstruction, latent, critic = [], [], []
    for start in range(0, len(x), 1024):
        batch = torch.from_numpy(x[start : start + 1024]).to(device)
        z = encoder(batch); recovered = decoder(z, batch.size(1)); z_recovered = encoder2(recovered)
        source, _ = discriminator(batch)
        reconstruction.append((recovered - batch).abs().mean(dim=(1, 2)).cpu().numpy())
        latent.append((z_recovered - z).pow(2).mean(dim=1).cpu().numpy())
        critic.append((-torch.sigmoid(source)).cpu().numpy())
    return np.concatenate(reconstruction), np.concatenate(latent), np.concatenate(critic)


def normalise(x, lo, hi):
    return np.clip((x - lo) / max(hi - lo, 1e-8), 0.0, 1.0)


def report(y, s):
    order = np.argsort(s)[::-1]; positives = max(int(y.sum()), 1)
    return {"pr_auc": float(average_precision_score(y, s)), "roc_auc": float(roc_auc_score(y, s)), "precision_at_100": float(y[order[:100]].mean()), "recall_at_100": float(y[order[:100]].sum() / positives), "recall_at_500": float(y[order[:500]].sum() / positives)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_ganomaly"))
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    args = parser.parse_args(); device = torch.device("cpu")
    state = torch.load(args.artifact_dir / "checkpoint.pt", map_location=device, weights_only=True)
    encoder = GANomalySequenceEncoder(state["feature_dim"]).eval(); decoder = GANomalySequenceDecoder(state["feature_dim"], max_length=state["sequence_length"]).eval(); encoder2 = GANomalySequenceEncoder(state["feature_dim"]).eval(); discriminator = GANomalySequenceDiscriminator(state["feature_dim"]).eval()
    encoder.load_state_dict(state["encoder"]); decoder.load_state_dict(state["decoder"]); encoder2.load_state_dict(state["encoder2"]); discriminator.load_state_dict(state["discriminator"])
    transformer = joblib.load(args.artifact_dir / "transformer.joblib")
    train_x, train_y = load(args.sequences / "train.npz", transformer); val_x, val_y = load(args.sequences / "validation.npz", transformer); test_x, test_y = load(args.sequences / "test.npz", transformer)
    train_parts = components(encoder, decoder, encoder2, discriminator, train_x[train_y == 0], device)
    bounds = [(float(np.quantile(part, .50)), float(np.quantile(part, .99))) for part in train_parts]

    def anomaly_score(x):
        parts = components(encoder, decoder, encoder2, discriminator, x, device)
        scaled = [normalise(part, *bound) for part, bound in zip(parts, bounds)]
        # The latent discrepancy is the primary GANomaly score. Others are independent diagnostics.
        return 0.60 * scaled[1] + 0.30 * scaled[0] + 0.10 * scaled[2]

    output = {"method": "strict normal-only sequential GANomaly", "observed_anomaly_labels_used_for_training_or_calibration": False, "score": "0.60 latent inconsistency + 0.30 reconstruction deviation + 0.10 discriminator normality", "normal_training_quantiles": {name: {"median": lo, "p99": hi} for name, (lo, hi) in zip(["reconstruction", "latent", "critic"], bounds)}, "validation": report(val_y, anomaly_score(val_x)), "test": report(test_y, anomaly_score(test_x))}
    (args.artifact_dir / "evaluation.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__": main()
