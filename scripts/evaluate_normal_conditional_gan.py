"""Held-out evaluation of the strict normal-only conditional forecasting GAN."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

from ueba_seq_acgan.models import ConditionalForecastDiscriminator, ConditionalForecastGenerator


def load(path: Path):
    raw = np.load(path)
    return raw["x"].astype("float32"), raw["y"].astype("int8"), raw["user"]


def user_codes(users, mapping):
    return np.asarray([mapping.get(str(user), 0) for user in users], dtype=np.int64)


def clean_normal_mask(users, days, labels, length):
    valid = np.zeros(len(labels), dtype=bool)
    for user in np.unique(users):
        index = np.where(users == user)[0]; index = index[np.argsort(days[index])]
        prefix = np.concatenate(([0], np.cumsum(labels[index], dtype=np.int32)))
        for position, row in enumerate(index):
            valid[row] = prefix[position + 1] - prefix[max(0, position - length + 1)] == 0
    return valid


@torch.inference_mode()
def predict(generator, discriminator, transformer, x, users, count_indices, calendar_indices, device):
    transformed = transformer.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype("float32")
    residuals, critic = [], []
    for start in range(0, len(x), 1024):
        history = torch.from_numpy(transformed[start : start + 1024, :-1]).to(device)
        actual = torch.from_numpy(transformed[start : start + 1024, -1]).to(device)
        code = torch.from_numpy(users[start : start + 1024]).to(device)
        forecast = generator(history, code, actual[:, calendar_indices])
        source = discriminator(history, actual, code)
        forecast_raw = transformer.inverse_transform(forecast.cpu().numpy())[:, count_indices]
        actual_raw = x[start : start + 1024, -1, count_indices]
        residuals.append(np.abs(np.log1p(actual_raw) - np.log1p(forecast_raw)))
        critic.append((-torch.sigmoid(source)).cpu().numpy())
    return np.concatenate(residuals), np.concatenate(critic)


def scale(value, lo, hi): return np.clip((value - lo) / np.maximum(hi - lo, 1e-8), 0, 1)
def report(y, s):
    order = np.argsort(s)[::-1]; pos = max(int(y.sum()), 1)
    return {"pr_auc": float(average_precision_score(y, s)), "roc_auc": float(roc_auc_score(y, s)), "precision_at_100": float(y[order[:100]].mean()), "recall_at_100": float(y[order[:100]].sum() / pos), "recall_at_500": float(y[order[:500]].sum() / pos)}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_conditional_gan")); parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences")); args = parser.parse_args()
    device = torch.device("cpu"); state = torch.load(args.artifact_dir / "checkpoint.pt", map_location=device, weights_only=True); bundle = joblib.load(args.artifact_dir / "transformer_and_users.joblib"); transformer, mapping = bundle["transformer"], bundle["user_index"]
    generator = ConditionalForecastGenerator(state["feature_dim"], state["count_indices"], len(mapping)).eval(); discriminator = ConditionalForecastDiscriminator(state["feature_dim"], len(mapping)).eval(); generator.load_state_dict(state["generator"]); discriminator.load_state_dict(state["discriminator"])
    train_x, train_y, train_users = load(args.sequences / "train.npz"); val_x, val_y, val_users = load(args.sequences / "validation.npz"); test_x, test_y, test_users = load(args.sequences / "test.npz")
    train_payload = np.load(args.sequences / "train.npz"); clean = clean_normal_mask(train_users, train_payload["end_day"], train_y, train_x.shape[1])
    train_residual, train_critic = predict(generator, discriminator, transformer, train_x[clean], user_codes(train_users[clean], mapping), state["count_indices"], state["calendar_indices"], device)
    # Per-feature robust normal scale, then top-three deviation: attacks often affect only a few telemetry channels.
    median = np.median(train_residual, axis=0); p99 = np.quantile(train_residual, .99, axis=0)
    critic_bounds = np.quantile(train_critic, [.50, .99])
    def score(x, users):
        residual, critic = predict(generator, discriminator, transformer, x, user_codes(users, mapping), state["count_indices"], state["calendar_indices"], device)
        standard = scale(residual, median, p99); top = np.sort(standard, axis=1)[:, -min(3, standard.shape[1]):].mean(axis=1)
        return .85 * top + .15 * scale(critic, *critic_bounds)
    output = {"method": "strict normal-only personalised conditional forecasting GAN", "observed_anomaly_labels_used_for_training_or_calibration": False, "score": "top-3 per-feature forecast residuals, calibrated on normal training windows, plus discriminator novelty", "validation": report(val_y, score(val_x, val_users)), "test": report(test_y, score(test_x, test_users)), "normal_calibration": {"residual_median": median.tolist(), "residual_p99": p99.tolist(), "critic_median": float(critic_bounds[0]), "critic_p99": float(critic_bounds[1])}}
    (args.artifact_dir / "evaluation.json").write_text(json.dumps(output, indent=2), encoding="utf-8"); print(json.dumps(output, indent=2))


if __name__ == "__main__": main()
