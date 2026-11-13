"""Strict normal-only sequential GANomaly training for UEBA.

Observed anomaly rows are never passed to an optimiser.  They are only filtered
from the historical trusted-normal training partition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset

from ueba_seq_acgan.models import GANomalySequenceDecoder, GANomalySequenceDiscriminator, GANomalySequenceEncoder
from ueba_seq_acgan.transforms import BoundedLogTransformer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_ganomaly"))
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--max-normal", type=int, default=50000)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        args.epochs, args.max_normal = 1, 1000
    raw = np.load(args.sequences / "train.npz")
    normal = raw["x"][raw["y"] == 0].astype("float32")[: args.max_normal]
    features = json.loads((args.sequences / "manifest.json").read_text(encoding="utf-8"))["features"]
    transformer = BoundedLogTransformer(features).fit(normal.reshape(-1, normal.shape[-1]))
    x = transformer.transform(normal.reshape(-1, normal.shape[-1])).reshape(normal.shape).astype("float32")
    loader = DataLoader(TensorDataset(torch.from_numpy(x)), batch_size=128, shuffle=True, drop_last=True)
    device = torch.device("cpu")
    encoder = GANomalySequenceEncoder(x.shape[-1]).to(device)
    decoder = GANomalySequenceDecoder(x.shape[-1], max_length=x.shape[1]).to(device)
    encoder2 = GANomalySequenceEncoder(x.shape[-1]).to(device)
    discriminator = GANomalySequenceDiscriminator(x.shape[-1]).to(device)
    generator_optim = Adam(list(encoder.parameters()) + list(decoder.parameters()) + list(encoder2.parameters()), lr=2e-4, betas=(0.5, 0.999))
    discriminator_optim = Adam(discriminator.parameters(), lr=1e-4, betas=(0.5, 0.999))
    bce, l1, mse = nn.BCEWithLogitsLoss(), nn.L1Loss(), nn.MSELoss()
    history = []
    for epoch in range(args.epochs):
        d_total = g_total = context_total = latent_total = 0.0
        batches = 0
        for (real,) in loader:
            real = real.to(device)
            reconstruction = decoder(encoder(real), real.size(1))
            discriminator_optim.zero_grad()
            real_source, _ = discriminator(real)
            fake_source, _ = discriminator(reconstruction.detach())
            d_loss = bce(real_source, torch.ones_like(real_source)) + bce(fake_source, torch.zeros_like(fake_source))
            d_loss.backward(); discriminator_optim.step()
            generator_optim.zero_grad()
            reconstruction = decoder(encoder(real), real.size(1))
            _, real_features = discriminator(real)
            fake_source, fake_features = discriminator(reconstruction)
            context = l1(reconstruction, real)
            latent = mse(encoder2(reconstruction), encoder(real).detach())
            feature_match = mse(fake_features, real_features.detach())
            adversarial = bce(fake_source, torch.ones_like(fake_source))
            g_loss = 40 * context + 10 * latent + feature_match + 0.25 * adversarial
            g_loss.backward(); generator_optim.step()
            d_total += d_loss.item(); g_total += g_loss.item(); context_total += context.item(); latent_total += latent.item(); batches += 1
        row = {"epoch": epoch + 1, "d_loss": d_total / batches, "g_loss": g_total / batches, "reconstruction_l1": context_total / batches, "latent_mse": latent_total / batches}
        history.append(row); print(json.dumps(row), flush=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"encoder": encoder.state_dict(), "decoder": decoder.state_dict(), "encoder2": encoder2.state_dict(), "discriminator": discriminator.state_dict(), "feature_dim": x.shape[-1], "sequence_length": x.shape[1], "normal_only": True, "architecture": "sequential_GANomaly"}, args.artifact_dir / "checkpoint.pt")
    joblib.dump(transformer, args.artifact_dir / "transformer.joblib")
    (args.artifact_dir / "training.json").write_text(json.dumps({"normal_samples": len(x), "observed_anomalies_used_for_optimisation": False, "history": history}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
