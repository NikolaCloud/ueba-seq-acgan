"""Summarize CERT answer-key coverage before defining chronological splits."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", default="r4.2")
    parser.add_argument("--answer-dir", type=Path, default=Path("data/raw/cert/answers/answers"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/data-audit/r4.2_answers.json"))
    args = parser.parse_args()
    dataset = args.release.removeprefix("r")
    insiders = pd.read_csv(args.answer_dir / "insiders.csv", dtype=str)
    scenarios = insiders[insiders.dataset == dataset].copy()
    scenarios["start"] = pd.to_datetime(scenarios["start"])
    scenarios["end"] = pd.to_datetime(scenarios["end"])
    paths = list(args.answer_dir.glob(f"{args.release}-*.csv")) + list(args.answer_dir.glob(f"{args.release}-*/*.csv"))
    source_counts: Counter[str] = Counter()
    event_count = 0
    for path in paths:
        with path.open(encoding="utf-8", newline="") as file:
            for row in csv.reader(file):
                source_counts[row[0]] += 1
                event_count += 1
    by_scenario = scenarios.groupby("scenario").agg(
        actors=("user", "nunique"), start=("start", "min"), end=("end", "max")
    )
    monthly = scenarios.assign(month=scenarios.start.dt.to_period("M").astype(str)).groupby("month").size()
    output = {
        "release": args.release,
        "actors": int(scenarios.user.nunique()),
        "scenario_windows": int(len(scenarios)),
        "answer_events": event_count,
        "event_sources": dict(source_counts),
        "scenario_summary": json.loads(by_scenario.to_json(orient="index", date_format="iso")),
        "scenario_starts_by_month": {str(month): int(count) for month, count in monthly.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
