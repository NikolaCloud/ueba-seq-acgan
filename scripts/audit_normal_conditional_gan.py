"""Read-only scenario and false-positive audit for the normal-only GAN."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from evaluate_normal_conditional_gan import clean_normal_mask, predict, scale, user_codes
from ueba_seq_acgan.models import ConditionalForecastDiscriminator, ConditionalForecastGenerator


def role_lookup(ldap_dir: Path, users: np.ndarray, days: np.ndarray) -> list[str]:
    required = {(str(user), str(np.datetime64(day, "M"))) for user, day in zip(users, days)}
    result = {key: "unknown" for key in required}
    for path in ldap_dir.glob("*.csv"):
        month = path.stem
        frame = pd.read_csv(path, usecols=["user_id", "role"])
        for user, role in frame.itertuples(index=False):
            key = (str(user), month)
            if key in result: result[key] = str(role)
    return [result[(str(user), str(np.datetime64(day, "M")))] for user, day in zip(users, days)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_normal_conditional_gan"))
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument("--scenario-sequences", type=Path, default=Path("data/processed/r5.2_scenario_sequences"))
    parser.add_argument("--ldap-dir", type=Path, default=Path("data/raw/cert/r5.2/r5.2/LDAP"))
    args = parser.parse_args(); device = torch.device("cpu")
    state = torch.load(args.artifact_dir / "checkpoint.pt", map_location=device, weights_only=True); bundle = joblib.load(args.artifact_dir / "transformer_and_users.joblib"); transformer, mapping = bundle["transformer"], bundle["user_index"]
    generator = ConditionalForecastGenerator(state["feature_dim"], state["count_indices"], len(mapping)).eval(); discriminator = ConditionalForecastDiscriminator(state["feature_dim"], len(mapping)).eval(); generator.load_state_dict(state["generator"]); discriminator.load_state_dict(state["discriminator"])
    train = np.load(args.sequences / "train.npz"); test = np.load(args.sequences / "test.npz"); scenario = np.load(args.scenario_sequences / "test.npz")["scenario"]
    clean = clean_normal_mask(train["user"], train["end_day"], train["y"], train["x"].shape[1])
    tr_residual, tr_critic = predict(generator, discriminator, transformer, train["x"][clean], user_codes(train["user"][clean], mapping), state["count_indices"], state["calendar_indices"], device)
    median, p99 = np.median(tr_residual, 0), np.quantile(tr_residual, .99, 0); critic_bounds = np.quantile(tr_critic, [.50, .99])
    residual, critic = predict(generator, discriminator, transformer, test["x"], user_codes(test["user"], mapping), state["count_indices"], state["calendar_indices"], device)
    standard = scale(residual, median, p99); score = .85 * np.sort(standard, axis=1)[:, -3:].mean(1) + .15 * scale(critic, *critic_bounds)
    features = json.loads((args.sequences / "manifest.json").read_text())["features"]; count_features = [features[i] for i in state["count_indices"]]
    by_scenario = {}
    for value in sorted(set(scenario[test["y"] == 1])):
        mask = (scenario == value) & (test["y"] == 1); ranks = np.argsort(score)[::-1]; by_scenario[str(int(value))] = {"events": int(mask.sum()), "mean_score": float(score[mask].mean()), "recall_at_100": float(mask[ranks[:100]].sum() / mask.sum()), "recall_at_500": float(mask[ranks[:500]].sum() / mask.sum()), "top_residual_features": [count_features[i] for i in np.argsort(standard[mask].mean(0))[-3:][::-1]]}
    false_positive = (test["y"] == 0); fp_order = np.argsort(np.where(false_positive, score, -np.inf))[::-1][:500]
    roles = role_lookup(args.ldap_dir, test["user"][fp_order], test["end_day"][fp_order]); role_counts = pd.Series(roles).value_counts().head(15).to_dict()
    output = {"scope": "read-only audit; labels used only for reporting", "test_scenarios": by_scenario, "top_500": {"true_anomalies": int(test["y"][np.argsort(score)[::-1][:500]].sum()), "false_positive_role_counts": role_counts, "false_positive_top_residual_features": [count_features[i] for i in np.argsort(standard[fp_order].mean(0))[-5:][::-1]], "unknown_user_codes": int((user_codes(test["user"], mapping) == 0).sum())}}
    (args.artifact_dir / "audit.json").write_text(json.dumps(output, indent=2), encoding="utf-8"); print(json.dumps(output, indent=2))


if __name__ == "__main__": main()
