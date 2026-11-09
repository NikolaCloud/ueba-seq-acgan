"""Inference contract for the selected UEBA risk detector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

FEATURE_DISPLAY_NAMES = {
    "logon_events": "События входа",
    "after_hours_events": "Активность вне графика",
    "weekend_events": "Активность в выходные",
    "logon_count": "Входы",
    "logoff_count": "Выходы",
    "device_events": "События устройств",
    "device_connect": "Подключения USB",
    "file_events": "Файловые операции",
    "file_content_chars": "Объём файлов",
    "http_events": "Веб-запросы",
    "http_job_search": "Поиск работы",
    "http_leak_site": "Обращения к leak-сайтам",
    "email_events": "Почтовые события",
    "email_external": "Внешние письма",
    "email_size": "Объём почты",
    "email_attachments": "Вложения",
}


def sequence_summary(sequences: np.ndarray) -> np.ndarray:
    """Create the exact summary representation used by the final detector."""
    if sequences.ndim != 3:
        raise ValueError("Expected shape: (batch, sequence_length, feature_count)")
    return np.concatenate(
        (
            sequences[:, -1],
            sequences.mean(axis=1),
            sequences.std(axis=1),
            sequences.max(axis=1),
            sequences[:, -1] - sequences[:, 0],
        ),
        axis=1,
    )


@dataclass(frozen=True)
class RiskResult:
    anomaly_probability: float
    risk_score: int
    risk_band: str
    drivers: list[dict[str, float | str]]


class UEBARiskScorer:
    """Load the selected model and produce presentation-safe UEBA results."""

    def __init__(self, artifact_dir: Path, manifest_path: Path) -> None:
        self.feature_names = json.loads(manifest_path.read_text(encoding="utf-8"))["features"]
        expected = len(self.feature_names) * 5
        if (artifact_dir / "model.ubj").exists():
            import xgboost as xgb

            self.model_type = "xgboost"
            self.scaler = None
            self.model = xgb.Booster()
            self.model.load_model(artifact_dir / "model.ubj")
            if self.model.num_features() != expected:
                raise ValueError("Model and manifest feature counts do not match")
        else:
            artifact = joblib.load(artifact_dir / "model.joblib")
            self.model_type = "sklearn"
            self.scaler, self.model = artifact["scaler"], artifact["model"]
            if getattr(self.scaler, "n_features_in_", expected) != expected:
                raise ValueError("Model and manifest feature counts do not match")

    def probabilities(self, sequences: np.ndarray, batch_size: int = 8192) -> np.ndarray:
        """Score a batch without materialising the full transformed dataset."""
        sequences = np.asarray(sequences, dtype=np.float32)
        if sequences.ndim != 3 or sequences.shape[2] != len(self.feature_names):
            raise ValueError("Expected (batch, sequence_length, features) in manifest order")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        output = []
        for start in range(0, len(sequences), batch_size):
            summary = sequence_summary(sequences[start : start + batch_size])
            if self.model_type == "xgboost":
                import xgboost as xgb

                output.append(self.model.predict(xgb.DMatrix(summary)))
            else:
                transformed = self.scaler.transform(summary)
                output.append(self.model.predict_proba(transformed)[:, 1])
        return np.concatenate(output) if output else np.empty(0, dtype=np.float64)

    @staticmethod
    def _band(score: int) -> str:
        if score >= 80:
            return "critical"
        if score >= 55:
            return "high"
        if score >= 30:
            return "medium"
        return "low"

    def score(self, sequence: np.ndarray) -> RiskResult:
        sequence = np.asarray(sequence, dtype=np.float32)
        if sequence.ndim == 2:
            sequence = sequence[None, ...]
        if sequence.shape[0] != 1 or sequence.shape[2] != len(self.feature_names):
            raise ValueError("Provide one sequence with the feature order from manifest.json")
        probability = float(self.probabilities(sequence)[0])
        score = round(100 * probability)
        last, mean, std = sequence[0, -1], sequence[0].mean(axis=0), sequence[0].std(axis=0)
        deviation = np.abs(last - mean) / (std + 1.0)
        behaviour = np.asarray(
            [
                index
                for index, name in enumerate(self.feature_names)
                if name not in {"day_of_week", "month"}
            ]
        )
        top = behaviour[np.argsort(deviation[behaviour])[-3:][::-1]]
        drivers = [
            {
                "feature": FEATURE_DISPLAY_NAMES.get(
                    self.feature_names[index], self.feature_names[index]
                ),
                "last_value": float(last[index]),
                "relative_deviation": float(deviation[index]),
            }
            for index in top
        ]
        return RiskResult(probability, score, self._band(score), drivers)
