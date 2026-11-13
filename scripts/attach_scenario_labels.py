"""Join scenario labels to precomputed daily features without changing features."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--daily",type=Path,default=Path("data/processed/r5.2_daily_features.parquet")); p.add_argument("--labels",type=Path,default=Path("data/processed/r5.2_scenario_labels.parquet")); p.add_argument("--output",type=Path,default=Path("data/processed/r5.2_daily_scenarios.parquet")); a=p.parse_args()
    daily=pd.read_parquet(a.daily); labels=pd.read_parquet(a.labels); result=daily.merge(labels,on=["user","day"],how="left"); result["scenario"]=result.scenario.fillna(0).astype("int8"); result.to_parquet(a.output,index=False); print(result.scenario.value_counts().sort_index().to_dict())
if __name__ == "__main__": main()
