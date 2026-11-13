# MITRE model selection on CERT r5.2

## Protocol

Both retained MITRE detectors were compared on the unchanged r5.2 validation
split (113,914 windows, 227 anomalies). The temporal model's test split was not
read. Selection was frozen before any further evaluation:

> Select the temporal model only if it improves validation PR-AUC by at least
> 10% relative and finds at least one additional anomaly at alert budget 100 or
> 500.

## Results

| Candidate | PR-AUC | ROC-AUC | TP@50 | TP@100 | TP@500 |
| --- | ---: | ---: | ---: | ---: | ---: |
| MITRE augmented | 0.00998 | 0.83995 | 0 | 2 | 7 |
| Temporal MITRE | 0.01034 | 0.81910 | 2 | 2 | 7 |

The temporal model improved PR-AUC by only 3.6% relative and did not improve
TP@100 or TP@500. It therefore failed the gate. The retained research model is
`artifacts/r5.2_mitre_augmented_seq_acgan`.

## Scenario audit

At 500 alerts, the selected model found 4/6 validation events in CERT scenario
1, 0/162 in scenario 2, 1/2 in scenario 3, and 2/57 in scenario 4. This uneven
coverage is a material limitation. The top false-positive cohort is associated
primarily with after-hours and file activity.

The complete machine-readable report, including month slices, role/user false
positive counts, and feature lift, is
`artifacts/r5.2_model_selection/validation_audit.json`.

## Final interpretation

The selected MITRE model remains a research demonstration. The adapted
supervised r5.2 baseline is the primary practical detector because its held-out
test PR-AUC is 0.8342 versus 0.01313 for the selected MITRE detector.
