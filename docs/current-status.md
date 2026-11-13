# Current project status

Updated: 2026-08-11

## Last completed action

Validation-only model selection is complete for the two retained MITRE
detectors. The audit did not read the temporal model's test split.

| Candidate | Validation PR-AUC | ROC-AUC | TP@100 | TP@500 | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| MITRE augmented | 0.00998 | 0.83995 | 2 | 7 | **Selected** |
| Temporal MITRE | 0.01034 | 0.81910 | 2 | 7 | Rejected |

The predeclared gate required the temporal model to improve validation PR-AUC
by at least 10% and find at least one additional anomaly at alert budget 100 or
500. It achieved a 3.6% relative PR-AUC increase and no operational gain.

The selected research detector remains
`artifacts/r5.2_mitre_augmented_seq_acgan`. Its already recorded real CERT test
result is PR-AUC 0.01313, ROC-AUC 0.85558, 4 true anomalies at 100 alerts, and
12 true anomalies at 500 alerts. No temporal test evaluation will be run as
part of this model-selection round.

The GPU-tuned `artifacts/r5.2_gpu_detector` is now the primary detector: test
PR-AUC 0.8910, Precision@100 1.00, Recall@500 0.8882 and Precision@500 0.604.
It improves the prior final baseline (PR-AUC 0.8342, Recall@500 0.8412).
At the validation-selected operating threshold it produces 246 test alerts,
including 242 true anomalies: precision 0.9837 and recall 0.7118.
The GAN detectors are research comparisons, not production-quality detectors.

## Audit findings

- The selected MITRE model detects validation scenario 1 best (4/6 at 500
  alerts), but detects none of the 162 scenario-2 events at that budget.
- Its top validation false positives are dominated by after-hours activity,
  file activity, and file-content volume.
- The temporal candidate concentrates many false positives in a few users and
  roles, especially technicians, and does not improve TP@100 or TP@500.
- Full evidence is stored in
  `artifacts/r5.2_model_selection/validation_audit.json`.

## Next recommended action

The first local web presentation layer is complete. It uses the supervised
r5.2 baseline as the default score, provides a ranked user table, risk
timelines, retrospective CERT markers and presentation-safe feature deviations.
The HTTP and JSON endpoints have been smoke-tested locally.

The interface also includes runtime synthetic generation. The retained
role-aware conditional GAN forecasts 14 future days, an explicit MITRE profile
is applied in bounded feature space, and both the supervised baseline and the
MITRE research discriminator score the result. This is labelled as scenario
simulation throughout the Russian-language UI.

A six-seed low-shot experiment now directly demonstrates augmentation utility.
With 3 real examples per CERT scenario, mean validation PR-AUC improves by
84.5%; with 10 examples it improves by 104.8%, and mean Recall@500 rises from
12.6% to 31.1%.

Next, review the dashboard interactively, then decide between a browser-based
local delivery and a Windows executable wrapper. Production claims remain
blocked by low real-event PR-AUC of the GAN detector and failed TSTR utility of
the old fully synthetic scenario generator.

## Interpretation rules

- Synthetic samples are simulated MITRE scenarios, not observed attacks.
- Real CERT anomaly labels are used only for held-out reporting in GAN work.
- Do not tune models, scenarios, thresholds, or selection rules from test data.
- Do not claim production-grade accuracy for either GAN detector.
