"""Aggregate repeated low-shot augmentation experiments into presentation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs",
        type=Path,
        nargs="+",
        default=[
            Path("artifacts/r5.2_low_shot_gan"),
            *[Path(f"artifacts/r5.2_low_shot_gan_seed{seed}") for seed in (40, 41, 43, 44, 45)],
        ],
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/r5.2_low_shot_gan/aggregate.json")
    )
    args = parser.parse_args()
    reports = [
        json.loads((directory / "evaluation.json").read_text(encoding="utf-8"))
        for directory in args.inputs
    ]
    shots = sorted(
        {row["real_anomalies_per_scenario"] for report in reports for row in report["results"]}
    )
    aggregate = []
    for count in shots:
        rows = [
            next(row for row in report["results"] if row["real_anomalies_per_scenario"] == count)
            for report in reports
        ]
        without = np.asarray([row["without_augmentation"]["pr_auc"] for row in rows])
        with_gan = np.asarray([row["with_gan_mitre_augmentation"]["pr_auc"] for row in rows])
        recall_without = np.asarray([row["without_augmentation"]["recall_at_500"] for row in rows])
        recall_with = np.asarray(
            [row["with_gan_mitre_augmentation"]["recall_at_500"] for row in rows]
        )
        aggregate.append(
            {
                "real_anomalies_per_scenario": count,
                "runs": len(rows),
                "mean_pr_auc_without": float(without.mean()),
                "mean_pr_auc_with_gan": float(with_gan.mean()),
                "mean_relative_pr_auc_gain": float(
                    (with_gan.mean() - without.mean()) / without.mean()
                ),
                "median_relative_pr_auc_gain": float(np.median((with_gan - without) / without)),
                "runs_improved": int((with_gan > without).sum()),
                "mean_recall_at_500_without": float(recall_without.mean()),
                "mean_recall_at_500_with_gan": float(recall_with.mean()),
                "mean_pr_auc_without_std": float(without.std(ddof=1)),
                "mean_pr_auc_with_gan_std": float(with_gan.std(ddof=1)),
            }
        )
    output = {
        "protocol": "six deterministic seeds; same train-only low-shot protocol; unchanged validation",
        "seeds": [report["seed"] for report in reports],
        "aggregate": aggregate,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
