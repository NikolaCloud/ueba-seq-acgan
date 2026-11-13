"""Extract r5.2 anomaly-scenario labels per user-day from official answer events."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


SOURCES = ("logon", "device", "file", "http", "email")


def scenario_ids(answer_dir: Path, release: str) -> dict[tuple[str, str], int]:
    output: dict[tuple[str, str], int] = {}
    for folder in answer_dir.glob(f"{release}-*"):
        if not folder.is_dir():
            continue
        scenario = int(folder.name.rsplit("-", 1)[1])
        for path in folder.glob("*.csv"):
            with path.open(encoding="utf-8", newline="") as file:
                for row in csv.reader(file):
                    output[(row[0], row[1])] = scenario
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", default="r5.2")
    parser.add_argument("--release-dir", type=Path, default=Path("data/raw/cert/r5.2/r5.2"))
    parser.add_argument("--answer-dir", type=Path, default=Path("data/raw/cert/answers/answers"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/r5.2_scenario_labels.parquet"))
    args = parser.parse_args(); labels = scenario_ids(args.answer_dir, args.release); parts=[]
    for source in SOURCES:
        print(f"Scanning {source}...", flush=True)
        for chunk in pd.read_csv(args.release_dir / f"{source}.csv", usecols=["id", "date", "user"], chunksize=250_000):
            chunk["scenario"] = chunk.id.map(lambda value: labels.get((source, value), 0)).astype("int8")
            chunk = chunk[chunk.scenario > 0]
            if len(chunk):
                chunk["day"] = pd.to_datetime(chunk.date, format="%m/%d/%Y %H:%M:%S").dt.floor("D")
                parts.append(chunk.groupby(["user", "day"], as_index=False).scenario.max())
    result = pd.concat(parts, ignore_index=True).groupby(["user", "day"], as_index=False).scenario.max()
    args.output.parent.mkdir(parents=True, exist_ok=True); result.to_parquet(args.output, index=False)
    print(f"Saved {len(result):,} labeled days: {result.scenario.value_counts().sort_index().to_dict()}")


if __name__ == "__main__": main()
