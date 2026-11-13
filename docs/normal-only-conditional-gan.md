# Strict normal-only conditional GAN: r5.2 iteration

## Decision

Earlier GAN variants reconstructed an entire 14-day window. That is a poor
inductive bias for a UEBA alert: a sufficiently expressive autoencoder can also
reconstruct an anomalous final day. The current model therefore forecasts the
final day from the preceding 13 days and the user's normal history.

The generator and discriminator form a conditional GAN. The generator predicts
the final feature vector; the discriminator receives the same history, target
day, and learned user identity and judges whether that target is plausible.
An anomaly score is derived from the forecast residual and the discriminator's
novelty signal.

## Integrity constraints

- No synthetic attacks, perturbations, pseudo-labels, or generated samples are
  used in this experiment.
- Known anomaly labels are used only to remove contaminated training windows.
  They are never an optimisation target, a calibration input, or a tuning
  criterion.
- Every 14-day window containing a known anomaly is excluded from training.
- Training sampling is stratified: each active user receives up to 20 clean
  windows before the remaining 60,000-window budget is sampled deterministically.
- Validation/test labels are read only by the final evaluation script.

## Run

`artifacts/r5.2_normal_conditional_gan` contains the active 35-epoch run.
The sole evaluator is `scripts/evaluate_normal_conditional_gan.py`.

## Result

The completed run used 60,000 clean normal windows from all 2,000 users. Its
held-out test result is PR-AUC 0.01027 and ROC-AUC 0.91282; recall@500 is
0.00882. It improves the ranking metrics over the prior strict normal-only GAN
experiments, but is still not a production-quality alert detector. These
numbers are reported as observed, without threshold selection or test-set
tuning.
