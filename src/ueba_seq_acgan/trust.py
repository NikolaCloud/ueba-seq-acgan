"""Cumulative trust-aware risk policy for one-class UEBA scores."""

from __future__ import annotations


def update_trust(previous: float, anomaly_score: float, decay: float = 0.97) -> tuple[float, float]:
    """Return updated trust (0..100) and cumulative risk; isolated events decay."""
    cumulative = decay * (100 - previous) + (1 - decay) * 100 * anomaly_score
    trust = max(0.0, min(100.0, 100 - cumulative))
    return trust, cumulative
