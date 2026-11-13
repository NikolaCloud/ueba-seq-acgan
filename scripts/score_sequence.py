"""Score a saved NPZ sequence by index using the selected UEBA detector."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from ueba_seq_acgan.risk import UEBARiskScorer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sequences", type=Path, default=Path("data/processed/r5.2_sequences/test.npz")
    )
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts/r5.2_final_raw_baseline"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/processed/r5.2_sequences/manifest.json")
    )
    args = parser.parse_args()
    payload = np.load(args.sequences)
    result = UEBARiskScorer(args.model_dir, args.manifest).score(payload["x"][args.index])
    print(result)


if __name__ == "__main__":
    main()
