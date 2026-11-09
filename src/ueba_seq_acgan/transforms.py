"""Bounded, zero-aware transform for heavy-tailed UEBA count features."""

from __future__ import annotations

import numpy as np


class BoundedLogTransformer:
    """Log-transform non-calendar counts, clip train quantiles, map to [-1, 1]."""

    def __init__(
        self, feature_names: list[str], lower_quantile: float = 0.0, upper_quantile: float = 0.995
    ) -> None:
        self.feature_names = feature_names
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile
        self.calendar_indices = np.array(
            [i for i, name in enumerate(feature_names) if name in {"day_of_week", "month"}]
        )
        self.count_indices = np.array(
            [i for i in range(len(feature_names)) if i not in self.calendar_indices]
        )

    def _prepared(self, values: np.ndarray) -> np.ndarray:
        output = values.astype(np.float32, copy=True)
        output[..., self.count_indices] = np.log1p(
            np.clip(output[..., self.count_indices], 0, None)
        )
        return output

    def fit(self, values: np.ndarray) -> BoundedLogTransformer:
        prepared = self._prepared(values)
        self.lower_ = np.quantile(prepared, self.lower_quantile, axis=0).astype(np.float32)
        self.upper_ = np.quantile(prepared, self.upper_quantile, axis=0).astype(np.float32)
        self.upper_ = np.maximum(self.upper_, self.lower_ + 1e-3)
        return self

    def transform(self, values: np.ndarray) -> np.ndarray:
        prepared = self._prepared(values)
        clipped = np.clip(prepared, self.lower_, self.upper_)
        return (2.0 * (clipped - self.lower_) / (self.upper_ - self.lower_) - 1.0).astype(
            np.float32
        )

    def inverse_transform(self, values: np.ndarray) -> np.ndarray:
        prepared = (np.clip(values, -1, 1) + 1.0) * 0.5 * (self.upper_ - self.lower_) + self.lower_
        output = prepared.astype(np.float32, copy=True)
        output[..., self.count_indices] = np.expm1(output[..., self.count_indices])
        return np.maximum(output, 0)
