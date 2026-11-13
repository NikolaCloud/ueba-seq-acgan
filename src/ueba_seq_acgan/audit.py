"""Reusable metrics and diagnostics for held-out UEBA model audits."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def ranking_metrics(y: np.ndarray, scores: np.ndarray, budgets: Iterable[int]) -> dict:
    """Return ranking metrics at explicit alert budgets."""
    y = np.asarray(y, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    order = np.argsort(scores, kind="stable")[::-1]
    positives = int(y.sum())
    result = {
        "events": len(y),
        "anomalies": positives,
        "pr_auc": float(average_precision_score(y, scores)) if positives else None,
        "roc_auc": float(roc_auc_score(y, scores)) if 0 < positives < len(y) else None,
        "alert_budgets": {},
    }
    for requested in budgets:
        k = min(int(requested), len(y))
        found = int(y[order[:k]].sum())
        result["alert_budgets"][str(requested)] = {
            "alerts": k,
            "true_anomalies": found,
            "precision": float(found / k) if k else 0.0,
            "recall": float(found / positives) if positives else None,
        }
    return result


def scenario_metrics(
    y: np.ndarray,
    scenarios: np.ndarray,
    scores: np.ndarray,
    budgets: Iterable[int],
) -> dict[str, dict]:
    """Report per-scenario recall within the model's global alert ranking."""
    y = np.asarray(y, dtype=np.int8)
    scenarios = np.asarray(scenarios, dtype=np.int16)
    scores = np.asarray(scores, dtype=np.float64)
    order = np.argsort(scores, kind="stable")[::-1]
    output: dict[str, dict] = {}
    values = sorted(int(value) for value in np.unique(scenarios[y == 1]))
    for value in values:
        mask = (y == 1) & (scenarios == value)
        count = int(mask.sum())
        row = {"anomalies": count, "mean_score": float(scores[mask].mean()), "recall": {}}
        for requested in budgets:
            k = min(int(requested), len(y))
            row["recall"][str(requested)] = float(mask[order[:k]].sum() / count)
        output[str(value)] = row
    return output


def choose_candidate(reports: dict[str, dict]) -> dict:
    """Apply the predeclared model gate without consulting test results.

    Temporal modelling must improve validation PR-AUC by at least 10% and find
    at least one additional real anomaly at either 100 or 500 alerts. Otherwise
    the simpler, already evaluated MITRE model remains selected.
    """
    baseline = reports["mitre_augmented"]["overall"]
    temporal = reports["temporal_mitre"]["overall"]
    baseline_pr = float(baseline["pr_auc"])
    temporal_pr = float(temporal["pr_auc"])
    relative_gain = (temporal_pr - baseline_pr) / baseline_pr if baseline_pr else float("inf")
    operational_gain = any(
        temporal["alert_budgets"][str(k)]["true_anomalies"]
        > baseline["alert_budgets"][str(k)]["true_anomalies"]
        for k in (100, 500)
    )
    temporal_passes = relative_gain >= 0.10 and operational_gain
    return {
        "selected": "temporal_mitre" if temporal_passes else "mitre_augmented",
        "rule": (
            "Select temporal_mitre only with >=10% relative validation PR-AUC gain "
            "and >=1 additional true anomaly at alert budget 100 or 500."
        ),
        "relative_pr_auc_gain": float(relative_gain),
        "operational_gain": bool(operational_gain),
        "temporal_passes": bool(temporal_passes),
    }
