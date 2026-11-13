from pathlib import Path

import numpy as np

from ueba_seq_acgan.risk import UEBARiskScorer
from ueba_seq_acgan.synthetic import MITREScenarioSimulator


def test_retained_r5_2_model_scores_one_sequence():
    root = Path(__file__).parents[1]
    scorer = UEBARiskScorer(
        root / "artifacts/r5.2_final_raw_baseline",
        root / "data/processed/r5.2_sequences/manifest.json",
    )
    raw = np.load(root / "data/processed/r5.2_sequences/validation.npz")
    probabilities = scorer.probabilities(raw["x"][:2], batch_size=1)
    assert probabilities.shape == (2,)
    assert np.all((0 <= probabilities) & (probabilities <= 1))


def test_gpu_detector_scores_one_sequence():
    root = Path(__file__).parents[1]
    scorer = UEBARiskScorer(
        root / "artifacts/r5.2_gpu_detector",
        root / "data/processed/r5.2_sequences/manifest.json",
    )
    raw = np.load(root / "data/processed/r5.2_sequences/validation.npz")
    probabilities = scorer.probabilities(raw["x"][:2], batch_size=1)
    assert probabilities.shape == (2,)
    assert np.all((0 <= probabilities) & (probabilities <= 1))


def test_retained_generator_builds_reproducible_mitre_scenario():
    root = Path(__file__).parents[1]
    simulator = MITREScenarioSimulator(
        root / "data/processed/r5.2_sequences/validation.npz",
        root / "data/processed/r5.2_sequences/manifest.json",
        root / "artifacts/r5.2_normal_role_conditional_gan",
        root / "artifacts/r5.2_mitre_augmented_seq_acgan",
        root / "artifacts/r5.2_gpu_detector",
        root / "data/raw/cert/r5.2/r5.2/LDAP",
        root / "configs/mitre_pseudo_scenarios.json",
    )
    first = simulator.generate("T1052.001", intensity=1.0, seed=42)
    second = simulator.generate("T1052.001", intensity=1.0, seed=42)
    assert first["user"] == second["user"]
    assert first["role_display"]
    assert first["series"] == second["series"]
    assert len(first["dates"]) == 14
    assert (
        first["scores"]["scenario_mitre_probability"] > first["scores"]["normal_mitre_probability"]
    )
