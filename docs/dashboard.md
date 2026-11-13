# Local UEBA dashboard

The dashboard is a zero-framework local presentation layer for the retained
CERT r5.2 experiment. The entire user-facing interface is in Russian. It uses
the GPU-tuned XGBoost detector for the primary risk score and the selected
MITRE Seq-ACGAN as a separate research signal.

## Build compact dashboard data

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = 'src'
python -m ueba_seq_acgan build
```

This scores the retained held-out test windows in batches and writes
`artifacts/dashboard/data.json`. The file contains the 100 users with the
highest peak risk, their timelines and presentation-safe feature deviations.

## Run locally

```powershell
$env:PYTHONPATH = 'src'
python -m ueba_seq_acgan serve
```

Open `http://127.0.0.1:8765`. The server binds to localhost by default and does
not send data over the network.

## Dynamic modules

- **Мониторинг** replays scores actually produced by the retained supervised
  model. Playback speed, clickable chart points, hover tooltips, alert
  highlighting, user details and the event feed are interactive.
- **Генератор сценариев** loads the retained LDAP-role-aware conditional GAN.
  It autoregressively forecasts 14 days for a real clean user context, applies
  one of six auditable MITRE profiles, and scores normal/scenario sequences with
  both retained detectors.
- **Качество и методика** exposes the detector and TSTR limitations directly in
  the product as an interactive six-seed low-data augmentation comparison.

The first generation request lazily loads PyTorch checkpoints and can take a
few seconds. Subsequent requests reuse the models. `seed` and intensity make
the demonstration reproducible and controllable.

## Interpretation

- Red points are retained CERT ground-truth events shown retrospectively.
- “Drivers” are within-window feature deviations, not causal explanations.
- The validation-selected threshold is frozen and is not fitted on test.
- The GAN learns a normal next-day forecast conditioned on user and LDAP role.
  The MITRE component is an explicit rule-guided simulation applied in bounded
  feature space; it is not claimed to be a learned or observed attack.
- The old fully scenario-conditioned generator has TSTR PR-AUC 0.0038 and did
  not pass the synthetic-data quality gate.
- The dashboard is a research demonstration, not an operational SOC console.
