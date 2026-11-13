"""Train Seq-ACGAN on labeled CERT UEBA sequences.

Use --smoke-test for a short CPU verification run. A production run should
increase epochs and normal samples only after reviewing the resulting metrics.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.preprocessing import RobustScaler
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

from ueba_seq_acgan.models import SequenceDiscriminator, SequenceGenerator


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_training_data(path: Path, max_normal: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    sequences, labels = data["x"].astype(np.float32), data["y"].astype(np.int64)
    normal_indices = np.flatnonzero(labels == 0)
    anomaly_indices = np.flatnonzero(labels == 1)
    if not len(anomaly_indices):
        raise ValueError("Training data has no anomalous sequences.")
    rng = np.random.default_rng(seed)
    normal_indices = rng.choice(normal_indices, size=min(max_normal, len(normal_indices)), replace=False)
    indices = np.concatenate((normal_indices, anomaly_indices))
    rng.shuffle(indices)
    return sequences[indices], labels[indices]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/sequences/train.npz"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/seq_acgan"))
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-normal", type=int, default=30_000)
    parser.add_argument("--steps-per-epoch", type=int, default=0, help="0 means all sampled batches")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        args.epochs, args.max_normal, args.steps_per_epoch = 1, 1_000, 10

    seed_everything(args.seed)
    sequences, labels = load_training_data(args.sequences, args.max_normal, args.seed)
    count, length, feature_dim = sequences.shape
    scaler = RobustScaler().fit(sequences.reshape(-1, feature_dim))
    sequences = scaler.transform(sequences.reshape(-1, feature_dim)).reshape(count, length, feature_dim).astype(np.float32)

    dataset = TensorDataset(torch.from_numpy(sequences), torch.from_numpy(labels))
    class_counts = np.bincount(labels, minlength=2)
    weights = (1.0 / class_counts[labels]).astype(np.float64)
    sampler = WeightedRandomSampler(weights, num_samples=max(len(dataset), args.batch_size * 10), replacement=True)
    loader = DataLoader(dataset, batch_size=args.batch_size, sampler=sampler, drop_last=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = SequenceGenerator(feature_dim).to(device)
    discriminator = SequenceDiscriminator(feature_dim).to(device)
    generator_optimizer = Adam(generator.parameters(), lr=2e-4, betas=(0.5, 0.999))
    discriminator_optimizer = Adam(discriminator.parameters(), lr=2e-4, betas=(0.5, 0.999))
    source_loss, class_loss = nn.BCEWithLogitsLoss(), nn.CrossEntropyLoss()
    history = []

    for epoch in range(1, args.epochs + 1):
        generator.train(); discriminator.train()
        d_total = g_total = 0.0
        steps = 0
        for real, real_labels in loader:
            real, real_labels = real.to(device), real_labels.to(device)
            batch = real.size(0)
            generated_labels = torch.randint(0, 2, (batch,), device=device)
            noise = torch.randn(batch, length, generator.latent_dim, device=device)
            fake = generator(noise, generated_labels)

            discriminator_optimizer.zero_grad()
            real_source, real_class = discriminator(real)
            fake_source, fake_class = discriminator(fake.detach())
            d_loss = (
                source_loss(real_source, torch.ones_like(real_source))
                + source_loss(fake_source, torch.zeros_like(fake_source))
                + class_loss(real_class, real_labels)
                + class_loss(fake_class, generated_labels)
            )
            d_loss.backward(); discriminator_optimizer.step()

            generator_optimizer.zero_grad()
            fake_source, fake_class = discriminator(fake)
            g_loss = source_loss(fake_source, torch.ones_like(fake_source)) + class_loss(fake_class, generated_labels)
            g_loss.backward(); generator_optimizer.step()
            d_total += d_loss.item(); g_total += g_loss.item(); steps += 1
            if args.steps_per_epoch and steps >= args.steps_per_epoch:
                break
        metrics = {"epoch": epoch, "d_loss": d_total / steps, "g_loss": g_total / steps}
        history.append(metrics)
        print(json.dumps(metrics))

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"generator": generator.state_dict(), "discriminator": discriminator.state_dict(), "feature_dim": feature_dim, "sequence_length": length},
        args.artifact_dir / "checkpoint.pt",
    )
    joblib.dump(scaler, args.artifact_dir / "scaler.joblib")
    (args.artifact_dir / "training.json").write_text(
        json.dumps({"device": str(device), "samples": count, "class_counts": class_counts.tolist(), "history": history}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
