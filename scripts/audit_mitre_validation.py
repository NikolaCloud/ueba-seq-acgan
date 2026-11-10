"""Compare retained MITRE detectors on validation only and freeze model selection."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from ueba_seq_acgan.audit import choose_candidate, ranking_metrics, scenario_metrics
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import MITRESequenceDiscriminator, SequenceDiscriminator

BUDGETS = (50, 100, 500)


def load_scenarios(path: Path, users: np.ndarray, days: np.ndarray) -> np.ndarray:
    """Map retained daily scenario labels to sequence end dates."""
    frame = pd.read_parquet(path, columns=["user", "day", "scenario"])
    frame["day"] = pd.to_datetime(frame["day"])
    lookup = frame.set_index(["user", "day"])["scenario"]
    index = pd.MultiIndex.from_arrays([users.astype(str), pd.to_datetime(days)])
    return lookup.reindex(index, fill_value=0).to_numpy(dtype=np.int8)


@torch.inference_mode()
def score_model(kind: str, artifact_dir: Path, x: np.ndarray, batch_size: int) -> np.ndarray:
    state = torch.load(artifact_dir / "checkpoint.pt", map_location="cpu", weights_only=True)
    if kind == "mitre_augmented":
        model = SequenceDiscriminator(state["feature_dim"]).eval()
    else:
        model = MITRESequenceDiscriminator(state["feature_dim"], state["scenarios"]).eval()
    model.load_state_dict(state["discriminator"])
    transformer = joblib.load(artifact_dir / "transformer.joblib")
    output = []
    for start in range(0, len(x), batch_size):
        batch = x[start : start + batch_size].astype(np.float32, copy=False)
        scaled = transformer.transform(batch.reshape(-1, batch.shape[-1]))
        scaled = scaled.reshape(batch.shape).astype(np.float32, copy=False)
        _, logits = model(torch.from_numpy(scaled))
        probabilities = torch.softmax(logits, dim=1)
        score = probabilities[:, 1] if kind == "mitre_augmented" else 1 - probabilities[:, 0]
        output.append(score.numpy())
    return np.concatenate(output)


def false_positive_audit(
    raw: dict[str, np.ndarray],
    scores: np.ndarray,
    features: list[str],
    ldap_dir: Path,
    budget: int = 500,
) -> dict:
    normal = raw["y"] == 0
    order = np.argsort(np.where(normal, scores, -np.inf), kind="stable")[::-1]
    selected = order[: min(budget, int(normal.sum()))]
    roles = roles_for_windows(raw["user"][selected], raw["end_day"][selected], ldap_dir)
    top_users = Counter(raw["user"][selected].astype(str)).most_common(15)
    last_day = raw["x"][:, -1].astype(np.float64)
    reference = last_day[normal]
    scale = np.where(reference.std(axis=0) > 0, reference.std(axis=0), 1.0)
    z_lift = (last_day[selected].mean(axis=0) - reference.mean(axis=0)) / scale
    feature_order = np.argsort(np.abs(z_lift))[::-1][:8]
    return {
        "budget": len(selected),
        "role_counts": dict(Counter(roles.astype(str)).most_common(15)),
        "user_counts": dict(top_users),
        "activity_feature_lift": [
            {"feature": features[i], "standardised_mean_difference": float(z_lift[i])}
            for i in feature_order
        ],
        "note": "Feature lift describes top false-positive activity; it is not model attribution.",
    }


def temporal_slices(y: np.ndarray, scores: np.ndarray, days: np.ndarray) -> dict:
    months = np.asarray(days).astype("datetime64[M]").astype(str)
    return {
        month: ranking_metrics(y[months == month], scores[months == month], BUDGETS)
        for month in sorted(np.unique(months))
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument(
        "--daily-scenarios", type=Path, default=Path("data/processed/r5.2_daily_scenarios.parquet")
    )
    parser.add_argument("--ldap-dir", type=Path, default=Path("data/raw/cert/r5.2/r5.2/LDAP"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/r5.2_model_selection"))
    parser.add_argument("--batch-size", type=int, default=1024)
    args = parser.parse_args()

    loaded = np.load(args.sequences / "validation.npz")
    raw = {key: loaded[key] for key in loaded.files}
    scenarios = load_scenarios(args.daily_scenarios, raw["user"], raw["end_day"])
    features = json.loads((args.sequences / "manifest.json").read_text(encoding="utf-8"))[
        "features"
    ]
    candidates = {
        "mitre_augmented": Path("artifacts/r5.2_mitre_augmented_seq_acgan"),
        "temporal_mitre": Path("artifacts/r5.2_temporal_mitre_seq_acgan"),
    }
    reports = {}
    for name, artifact_dir in candidates.items():
        print(f"Scoring {name} on validation...", flush=True)
        scores = score_model(name, artifact_dir, raw["x"], args.batch_size)
        reports[name] = {
            "artifact_dir": str(artifact_dir),
            "overall": ranking_metrics(raw["y"], scores, BUDGETS),
            "real_cert_scenarios": scenario_metrics(raw["y"], scenarios, scores, BUDGETS),
            "monthly": temporal_slices(raw["y"], scores, raw["end_day"]),
            "top_500_false_positives": false_positive_audit(raw, scores, features, args.ldap_dir),
        }
    output = {
        "scope": "validation-only model selection; test was not read",
        "split": "validation",
        "budgets": list(BUDGETS),
        "models": reports,
        "decision": choose_candidate(reports),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "validation_audit.json"
    destination.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output["decision"], indent=2), flush=True)
    print(f"Saved {destination}", flush=True)


if __name__ == "__main__":
    main()
