import numpy as np

from ueba_seq_acgan.audit import choose_candidate, ranking_metrics, scenario_metrics
from ueba_seq_acgan.risk import sequence_summary


def test_ranking_metrics_at_explicit_budgets():
    y = np.array([0, 1, 0, 1], dtype=np.int8)
    scores = np.array([0.1, 0.8, 0.2, 0.9])
    result = ranking_metrics(y, scores, (1, 2))
    assert result["anomalies"] == 2
    assert result["alert_budgets"]["1"]["precision"] == 1.0
    assert result["alert_budgets"]["2"]["recall"] == 1.0


def test_scenario_metrics_use_global_ranking():
    y = np.array([1, 1, 0, 1], dtype=np.int8)
    scenarios = np.array([1, 2, 0, 1], dtype=np.int8)
    scores = np.array([0.9, 0.8, 0.1, 0.2])
    result = scenario_metrics(y, scenarios, scores, (2,))
    assert result["1"]["anomalies"] == 2
    assert result["1"]["recall"]["2"] == 0.5
    assert result["2"]["recall"]["2"] == 1.0


def _report(pr_auc, at_100, at_500):
    return {
        "overall": {
            "pr_auc": pr_auc,
            "alert_budgets": {
                "100": {"true_anomalies": at_100},
                "500": {"true_anomalies": at_500},
            },
        }
    }


def test_temporal_candidate_must_pass_both_parts_of_gate():
    reports = {
        "mitre_augmented": _report(0.01, 2, 7),
        "temporal_mitre": _report(0.012, 3, 7),
    }
    assert choose_candidate(reports)["selected"] == "temporal_mitre"
    reports["temporal_mitre"] = _report(0.0105, 3, 8)
    assert choose_candidate(reports)["selected"] == "mitre_augmented"
    reports["temporal_mitre"] = _report(0.012, 2, 7)
    assert choose_candidate(reports)["selected"] == "mitre_augmented"


def test_sequence_summary_shape_and_values():
    sequences = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    summary = sequence_summary(sequences)
    assert summary.shape == (2, 20)
    np.testing.assert_array_equal(summary[:, :4], sequences[:, -1])
    np.testing.assert_array_equal(summary[:, -4:], sequences[:, -1] - sequences[:, 0])
