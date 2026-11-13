"""Create leakage-safe chronological sequences from daily UEBA feature vectors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


NON_FEATURES = {"user", "day", "anomaly", "scenario", "split"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/r3.1_daily_features.parquet"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/sequences"))
    parser.add_argument("--sequence-length", type=int, default=14)
    parser.add_argument("--train-end", default="2010-07-31")
    parser.add_argument("--validation-end", default="2010-08-31")
    args = parser.parse_args()

    observed = pd.read_parquet(args.input).sort_values(["user", "day"])
    train_end, validation_end = pd.Timestamp(args.train_end), pd.Timestamp(args.validation_end)
    features = [column for column in observed.columns if column not in NON_FEATURES]
    completed_groups = []
    for user, group in observed.groupby("user", sort=False):
        # Missing calendar days mean no recorded activity, not a shorter day.
        full_days = pd.date_range(group.day.min(), group.day.max(), freq="D")
        complete = group.set_index("day").reindex(full_days)
        complete.index.name = "day"
        complete["user"] = user
        complete[features] = complete[features].fillna(0)
        complete["anomaly"] = complete["anomaly"].fillna(0).astype("int8")
        if "scenario" in complete:
            complete["scenario"] = complete["scenario"].fillna(0).astype("int8")
        complete = complete.reset_index()
        complete["day_of_week"] = complete["day"].dt.dayofweek.astype("int8")
        complete["month"] = complete["day"].dt.month.astype("int8")
        completed_groups.append(complete)
    daily = pd.concat(completed_groups, ignore_index=True)
    daily["split"] = np.where(
        daily.day <= train_end, "train", np.where(daily.day <= validation_end, "validation", "test")
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"sequence_length": args.sequence_length, "features": features, "splits": {}}

    buckets = {split: {"sequences": [], "labels": [], "scenarios": [], "users": [], "ends": []} for split in ("train", "validation", "test")}
    for user, group in daily.groupby("user", sort=False):
        values = group[features].to_numpy(dtype=np.float32)
        target = group["anomaly"].to_numpy(dtype=np.int8)
        scenarios = group["scenario"].to_numpy(dtype=np.int8) if "scenario" in group else np.zeros(len(group), dtype=np.int8)
        dates = group["day"].to_numpy(dtype="datetime64[ns]")
        splits = group["split"].to_numpy()
        for index in range(args.sequence_length - 1, len(group)):
            bucket = buckets[splits[index]]
            bucket["sequences"].append(values[index - args.sequence_length + 1 : index + 1])
            bucket["labels"].append(target[index])
            bucket["scenarios"].append(scenarios[index])
            bucket["users"].append(user)
            bucket["ends"].append(dates[index])

    for split, bucket in buckets.items():
        payload = {
            "x": np.asarray(bucket["sequences"], dtype=np.float32),
            "y": np.asarray(bucket["labels"], dtype=np.int8),
            "scenario": np.asarray(bucket["scenarios"], dtype=np.int8),
            "user": np.asarray(bucket["users"]),
            "end_day": np.asarray(bucket["ends"]),
        }
        np.savez_compressed(args.output_dir / f"{split}.npz", **payload)
        anomaly_count = int(np.asarray(bucket["labels"], dtype=np.int64).sum())
        manifest["splits"][split] = {"sequences": len(bucket["labels"]), "anomalies": anomaly_count}
        print(f"{split}: {len(bucket['labels']):,} sequences, {anomaly_count:,} anomalous")

    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
