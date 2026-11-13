"""Train a strict normal-only, personalised conditional forecasting GAN for UEBA."""
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

from ueba_seq_acgan.models import ConditionalForecastDiscriminator, ConditionalForecastGenerator
from ueba_seq_acgan.transforms import BoundedLogTransformer


def clean_normal_mask(users: np.ndarray, days: np.ndarray, labels: np.ndarray, length: int) -> np.ndarray:
    """Retain only windows whose endpoint and prior history are known normal."""
    valid = np.zeros(len(labels), dtype=bool)
    for user in np.unique(users):
        index = np.where(users == user)[0]
        index = index[np.argsort(days[index])]
        anomaly_prefix = np.concatenate(([0], np.cumsum(labels[index], dtype=np.int32)))
        for position, row in enumerate(index):
            left = max(0, position - length + 1)
            valid[row] = anomaly_prefix[position + 1] - anomaly_prefix[left] == 0
    return valid


def stratified_normal_indices(users: np.ndarray, mask: np.ndarray, limit: int, seed: int = 42) -> np.ndarray:
    """Keep every active user represented before sampling remaining normal windows."""
    rng = np.random.default_rng(seed); selected, remainder = [], []
    for user in np.unique(users):
        rows = np.where((users == user) & mask)[0]; rng.shuffle(rows)
        selected.extend(rows[: min(20, len(rows))]); remainder.extend(rows[min(20, len(rows)) :])
    if len(selected) > limit:
        return np.asarray(rng.choice(selected, size=limit, replace=False), dtype=np.int64)
    remainder = np.asarray(remainder, dtype=np.int64); rng.shuffle(remainder)
    return np.asarray(selected + remainder[: max(0, limit - len(selected))].tolist(), dtype=np.int64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_conditional_gan"))
    parser.add_argument("--epochs", type=int, default=35)
    parser.add_argument("--max-normal", type=int, default=60000)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test: args.epochs, args.max_normal = 1, 1000
    raw = np.load(args.sequences / "train.npz")
    mask = clean_normal_mask(raw["user"], raw["end_day"], raw["y"], raw["x"].shape[1])
    selected = stratified_normal_indices(raw["user"], mask, args.max_normal)
    x = raw["x"][selected].astype("float32")
    users_raw = raw["user"][selected]
    manifest = json.loads((args.sequences / "manifest.json").read_text(encoding="utf-8")); features = manifest["features"]
    transformer = BoundedLogTransformer(features).fit(x.reshape(-1, x.shape[-1]))
    x = transformer.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype("float32")
    user_values = sorted(str(value) for value in np.unique(users_raw)); user_index = {value: i + 1 for i, value in enumerate(user_values)}
    users = np.array([user_index[str(value)] for value in users_raw], dtype=np.int64)
    history, target = x[:, :-1], x[:, -1]
    calendar_indices = transformer.calendar_indices.tolist(); count_indices = transformer.count_indices.tolist()
    loader = DataLoader(TensorDataset(torch.from_numpy(history), torch.from_numpy(target), torch.from_numpy(users)), batch_size=256, shuffle=True, drop_last=True)
    device = torch.device("cpu")
    generator = ConditionalForecastGenerator(x.shape[-1], count_indices, len(user_values)).to(device)
    discriminator = ConditionalForecastDiscriminator(x.shape[-1], len(user_values)).to(device)
    generator_optim = Adam(generator.parameters(), lr=2e-4, betas=(0.5, 0.999)); discriminator_optim = Adam(discriminator.parameters(), lr=1e-4, betas=(0.5, 0.999))
    bce, l1 = nn.BCEWithLogitsLoss(), nn.SmoothL1Loss(); history_rows = []
    for epoch in range(args.epochs):
        d_sum = g_sum = residual_sum = 0.0; batches = 0
        for prior, real, user in loader:
            prior, real, user = prior.to(device), real.to(device), user.to(device); calendar = real[:, calendar_indices]
            fake = generator(prior, user, calendar)
            discriminator_optim.zero_grad()
            real_score = discriminator(prior, real, user); fake_score = discriminator(prior, fake.detach(), user)
            d_loss = bce(real_score, torch.ones_like(real_score) * 0.9) + bce(fake_score, torch.zeros_like(fake_score))
            d_loss.backward(); discriminator_optim.step()
            generator_optim.zero_grad(); fake = generator(prior, user, calendar); fake_score = discriminator(prior, fake, user)
            residual = l1(fake[:, count_indices], real[:, count_indices])
            g_loss = 20.0 * residual + 0.5 * bce(fake_score, torch.ones_like(fake_score))
            g_loss.backward(); generator_optim.step()
            d_sum += d_loss.item(); g_sum += g_loss.item(); residual_sum += residual.item(); batches += 1
        row = {"epoch": epoch + 1, "d_loss": d_sum / batches, "g_loss": g_sum / batches, "count_forecast_smooth_l1": residual_sum / batches}; history_rows.append(row); print(json.dumps(row), flush=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"generator": generator.state_dict(), "discriminator": discriminator.state_dict(), "feature_dim": x.shape[-1], "sequence_length": x.shape[1], "count_indices": count_indices, "calendar_indices": calendar_indices, "normal_only": True, "architecture": "personalised_conditional_forecasting_gan"}, args.artifact_dir / "checkpoint.pt")
    joblib.dump({"transformer": transformer, "user_index": user_index}, args.artifact_dir / "transformer_and_users.joblib")
    (args.artifact_dir / "training.json").write_text(json.dumps({"normal_windows": int(len(x)), "users_represented": int(len(user_values)), "sampling": "at least 20 clean normal windows per user, then deterministic random remainder", "excluded_windows_with_known_anomaly_in_history": int((~mask).sum()), "observed_anomalies_used_for_optimisation": False, "history": history_rows}, indent=2), encoding="utf-8")


if __name__ == "__main__": main()
