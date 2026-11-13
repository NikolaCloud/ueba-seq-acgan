"""Add leakage-safe user-relative deviation features to daily UEBA vectors."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


EXCLUDED = {"user", "day", "anomaly", "day_of_week", "month"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/r4.2_daily_features.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/r4.2_daily_features_relative.parquet"))
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--min-history", type=int, default=7)
    args = parser.parse_args()
    observed = pd.read_parquet(args.input).sort_values(["user", "day"])
    feature_columns = [column for column in observed.columns if column not in EXCLUDED]
    complete_groups = []
    for user, group in observed.groupby("user", sort=False):
        days = pd.date_range(group.day.min(), group.day.max(), freq="D")
        complete = group.set_index("day").reindex(days)
        complete.index.name = "day"
        complete["user"] = user
        complete[feature_columns] = complete[feature_columns].fillna(0)
        complete["anomaly"] = complete["anomaly"].fillna(0).astype("int8")
        complete = complete.reset_index()
        complete["day_of_week"] = complete.day.dt.dayofweek.astype("int8")
        complete["month"] = complete.day.dt.month.astype("int8")
        history = complete[feature_columns].rolling(args.window, min_periods=args.min_history)
        mean = history.mean().shift(1)
        std = history.std().shift(1).fillna(0)
        relative = ((complete[feature_columns] - mean) / (std + 1.0)).fillna(0).clip(-5, 5)
        relative.columns = [f"relative_{column}" for column in feature_columns]
        complete_groups.append(pd.concat((complete, relative.astype("float32")), axis=1))
    output = pd.concat(complete_groups, ignore_index=True).sort_values(["day", "user"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(args.output, index=False)
    print(f"Saved {len(output):,} rows with {len(feature_columns)} relative features: {args.output}")


if __name__ == "__main__":
    main()
