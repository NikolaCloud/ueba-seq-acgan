"""Measure GAN/MITRE augmentation utility with few real anomalies per scenario."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import RobustScaler
from train_baseline import metrics, sequence_features

from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import RoleConditionalForecastGenerator, SequenceDiscriminator


def scenario_array(daily_path: Path, users: np.ndarray, days: np.ndarray) -> np.ndarray:
    daily = pd.read_parquet(daily_path, columns=["user", "day", "scenario"])
    daily["day"] = pd.to_datetime(daily["day"])
    lookup = daily.set_index(["user", "day"])["scenario"]
    index = pd.MultiIndex.from_arrays([users.astype(str), pd.to_datetime(days)])
    return lookup.reindex(index, fill_value=0).to_numpy(dtype=np.int8)


def stratified_few_shot(
    scenarios: np.ndarray, labels: np.ndarray, shots: int, seed: int
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    selected = []
    for scenario in (1, 2, 3, 4):
        candidates = np.flatnonzero((labels == 1) & (scenarios == scenario))
        selected.extend(rng.choice(candidates, min(shots, len(candidates)), replace=False))
    return np.asarray(selected, dtype=np.int64)


@torch.inference_mode()
def gan_scenarios(
    raw: dict[str, np.ndarray],
    base_indices: np.ndarray,
    prototypes: dict[int, np.ndarray],
    profiles: list[dict],
    features: list[str],
    transformer,
    generator: RoleConditionalForecastGenerator,
    discriminator: SequenceDiscriminator,
    user_map: dict,
    role_map: dict,
    roles: np.ndarray,
    device: torch.device,
    seed: int,
) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(seed)
    output = []
    quality = {}
    for profile in profiles:
        scenario = int(profile["scenario"])
        chosen = rng.choice(base_indices, len(base_indices) // len(profiles), replace=False)
        source = raw["x"][chosen].astype(np.float32)
        scaled = transformer.transform(source.reshape(-1, source.shape[-1])).reshape(source.shape)
        users = torch.tensor([user_map.get(str(v), 0) for v in raw["user"][chosen]], device=device)
        role_codes = torch.tensor([role_map.get(str(v), 0) for v in roles[chosen]], device=device)
        batches = []
        mitre_scores = []
        for start in range(0, len(chosen), 512):
            batch = torch.from_numpy(scaled[start : start + 512]).to(device)
            generated_day = generator(
                batch[:, :-1],
                users[start : start + 512],
                role_codes[start : start + 512],
                batch[:, -1, generator.calendar_indices],
            )
            synthetic = torch.cat((batch[:, :-1], generated_day[:, None]), dim=1)
            prototype_pool = prototypes[scenario]
            prototype_choice = prototype_pool[
                rng.integers(0, len(prototype_pool), size=len(synthetic))
            ].copy()
            strength = rng.uniform(0.75, 1.25, size=(len(synthetic), 1)).astype(np.float32)
            indices = [features.index(name) for name in profile["features"]]
            target = synthetic[:, -1].cpu().numpy()
            target[:, indices] += strength * (prototype_choice[:, indices] - target[:, indices])
            target[:, indices] += rng.normal(0, 0.06, size=(len(target), len(indices)))
            synthetic[:, -1, indices] = torch.from_numpy(np.clip(target[:, indices], -1, 1)).to(
                device
            )
            _, logits = discriminator(synthetic)
            mitre_scores.append(torch.softmax(logits, dim=1)[:, 1].cpu().numpy())
            batches.append(synthetic.cpu().numpy())
        transformed = np.concatenate(batches)
        raw_synthetic = transformer.inverse_transform(
            transformed.reshape(-1, transformed.shape[-1])
        ).reshape(transformed.shape)
        output.append(raw_synthetic)
        final = raw_synthetic[:, -1, [features.index(name) for name in profile["features"]]]
        quality[str(scenario)] = {
            "name": profile["name"],
            "techniques": profile["techniques"],
            "samples": len(raw_synthetic),
            "mean_mitre_probability": float(np.concatenate(mitre_scores).mean()),
            "mean_feature_std": float(final.std(axis=0).mean()),
            "distinct_final_days": len(np.unique(np.round(final, 2), axis=0)),
        }
    return np.concatenate(output), quality


def scenario_report(y: np.ndarray, scenarios: np.ndarray, scores: np.ndarray) -> dict:
    order = np.argsort(scores)[::-1]
    result = {}
    for scenario in (1, 2, 3, 4):
        mask = (y == 1) & (scenarios == scenario)
        total = int(mask.sum())
        result[str(scenario)] = {
            "events": total,
            "recall_at_100": float(mask[order[:100]].sum() / max(total, 1)),
            "recall_at_500": float(mask[order[:500]].sum() / max(total, 1)),
        }
    return result


def fit_detector(
    x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray, seed: int
) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=250,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=seed,
    ).fit(x, y, sample_weight=sample_weight)


def balanced_low_shot_weights(
    normal_count: int,
    real_count: int,
    synthetic_count: int = 0,
    synthetic_share: float = 0.25,
) -> np.ndarray:
    """Keep class balance fixed while limiting synthetic influence."""
    normal = np.full(normal_count, 0.5 / normal_count)
    if not synthetic_count:
        return np.concatenate((normal, np.full(real_count, 0.5 / real_count)))
    real = np.full(real_count, 0.5 * (1 - synthetic_share) / real_count)
    synthetic = np.full(synthetic_count, 0.5 * synthetic_share / synthetic_count)
    return np.concatenate((normal, real, synthetic))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences", type=Path, default=Path("data/processed/r5.2_sequences"))
    parser.add_argument(
        "--daily-scenarios", type=Path, default=Path("data/processed/r5.2_daily_scenarios.parquet")
    )
    parser.add_argument(
        "--normal-gan-dir", type=Path, default=Path("artifacts/r5.2_normal_role_conditional_gan")
    )
    parser.add_argument(
        "--mitre-dir", type=Path, default=Path("artifacts/r5.2_mitre_augmented_seq_acgan")
    )
    parser.add_argument("--ldap-dir", type=Path, default=Path("data/raw/cert/r5.2/r5.2/LDAP"))
    parser.add_argument(
        "--profiles", type=Path, default=Path("configs/cert_low_shot_profiles.json")
    )
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r5.2_low_shot_gan"))
    parser.add_argument("--normal-samples", type=int, default=50_000)
    parser.add_argument("--synthetic-per-scenario", type=int, default=1_000)
    parser.add_argument("--shots", type=int, nargs="+", default=[1, 3, 5, 10])
    parser.add_argument("--synthetic-share", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    started = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}", flush=True)

    train_file = np.load(args.sequences / "train.npz")
    validation_file = np.load(args.sequences / "validation.npz")
    train = {key: train_file[key] for key in train_file.files}
    validation = {key: validation_file[key] for key in validation_file.files}
    train_scenarios = scenario_array(args.daily_scenarios, train["user"], train["end_day"])
    validation_scenarios = scenario_array(
        args.daily_scenarios, validation["user"], validation["end_day"]
    )
    manifest = json.loads((args.sequences / "manifest.json").read_text(encoding="utf-8"))
    features = manifest["features"]
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))

    state = torch.load(
        args.normal_gan_dir / "checkpoint.pt", map_location=device, weights_only=True
    )
    bundle = joblib.load(args.normal_gan_dir / "transformer_users_roles.joblib")
    transformer = bundle["transformer"]
    generator = (
        RoleConditionalForecastGenerator(
            state["feature_dim"],
            state["count_indices"],
            len(bundle["user_index"]),
            len(bundle["role_index"]),
        )
        .to(device)
        .eval()
    )
    generator.load_state_dict(state["generator"])
    mitre_state = torch.load(
        args.mitre_dir / "checkpoint.pt", map_location=device, weights_only=True
    )
    discriminator = SequenceDiscriminator(mitre_state["feature_dim"]).to(device).eval()
    discriminator.load_state_dict(mitre_state["discriminator"])
    roles = roles_for_windows(train["user"], train["end_day"], args.ldap_dir)

    rng = np.random.default_rng(args.seed)
    normal_candidates = np.flatnonzero(train["y"] == 0)
    normal_indices = rng.choice(normal_candidates, args.normal_samples, replace=False)
    base_indices = rng.choice(
        normal_candidates, args.synthetic_per_scenario * len(profiles), replace=False
    )
    validation_features = sequence_features(validation["x"])
    results = []
    best = None
    for shots in args.shots:
        few_indices = stratified_few_shot(train_scenarios, train["y"], shots, args.seed)
        scaled_few = transformer.transform(
            train["x"][few_indices].reshape(-1, train["x"].shape[-1])
        ).reshape(train["x"][few_indices].shape)
        prototypes = {
            scenario: scaled_few[train_scenarios[few_indices] == scenario, -1]
            for scenario in (1, 2, 3, 4)
        }
        synthetic, quality = gan_scenarios(
            train,
            base_indices,
            prototypes,
            profiles,
            features,
            transformer,
            generator,
            discriminator,
            bundle["user_index"],
            bundle["role_index"],
            roles,
            device,
            args.seed + shots,
        )
        base_x = np.concatenate(
            (
                sequence_features(train["x"][normal_indices]),
                sequence_features(train["x"][few_indices]),
            )
        )
        base_y = np.concatenate(
            (np.zeros(len(normal_indices), dtype=np.int8), np.ones(len(few_indices), dtype=np.int8))
        )
        scaler = RobustScaler().fit(base_x)
        scaled_base = scaler.transform(base_x)
        scaled_validation = scaler.transform(validation_features)
        baseline_weights = balanced_low_shot_weights(len(normal_indices), len(few_indices))
        baseline = fit_detector(scaled_base, base_y, baseline_weights, args.seed)
        baseline_scores = baseline.predict_proba(scaled_validation)[:, 1]
        augmented_x = np.concatenate((scaled_base, scaler.transform(sequence_features(synthetic))))
        augmented_y = np.concatenate((base_y, np.ones(len(synthetic), dtype=np.int8)))
        augmented_weights = balanced_low_shot_weights(
            len(normal_indices), len(few_indices), len(synthetic), args.synthetic_share
        )
        augmented = fit_detector(augmented_x, augmented_y, augmented_weights, args.seed)
        augmented_scores = augmented.predict_proba(scaled_validation)[:, 1]
        baseline_metrics = metrics(validation["y"], baseline_scores)
        augmented_metrics = metrics(validation["y"], augmented_scores)
        row = {
            "real_anomalies_per_scenario": shots,
            "real_anomalies_total": len(few_indices),
            "normal_training_windows": len(normal_indices),
            "synthetic_training_windows": len(synthetic),
            "synthetic_positive_weight_share": args.synthetic_share,
            "without_augmentation": baseline_metrics,
            "with_gan_mitre_augmentation": augmented_metrics,
            "relative_pr_auc_gain": float(
                (augmented_metrics["pr_auc"] - baseline_metrics["pr_auc"])
                / max(baseline_metrics["pr_auc"], 1e-12)
            ),
            "scenario_recall_without": scenario_report(
                validation["y"], validation_scenarios, baseline_scores
            ),
            "scenario_recall_with": scenario_report(
                validation["y"], validation_scenarios, augmented_scores
            ),
            "synthetic_quality": quality,
        }
        results.append(row)
        print(
            json.dumps({"shots": shots, "without": baseline_metrics, "with": augmented_metrics}),
            flush=True,
        )
        if best is None or augmented_metrics["pr_auc"] > best[0]:
            best = (augmented_metrics["pr_auc"], shots, scaler, augmented)

    report = {
        "protocol": "train-only few-shot anomalies; GAN/MITRE augmentation; unchanged validation evaluation",
        "device": str(device),
        "seed": args.seed,
        "results": results,
        "best_shots": best[1],
        "elapsed_seconds": time.time() - started,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": best[2], "model": best[3]}, args.artifact_dir / "best_model.joblib")
    (args.artifact_dir / "evaluation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"saved {args.artifact_dir}; elapsed={report['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
