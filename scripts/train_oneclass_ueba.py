"""Train normal-only UEBA detector; labels are evaluation-only."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score,roc_auc_score
from sklearn.preprocessing import RobustScaler
from ueba_seq_acgan.risk import sequence_summary
def metric(y,s):
 return {'pr_auc':float(average_precision_score(y,s)),'roc_auc':float(roc_auc_score(y,s)),'recall_at_100':float(y[np.argsort(s)[-100:]].sum()/y.sum())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_oneclass'));a=p.parse_args()
 tr=np.load(a.sequences/'train.npz');va=np.load(a.sequences/'validation.npz');te=np.load(a.sequences/'test.npz');xtr=sequence_summary(tr['x']);normal=xtr[tr['y']==0];scaler=RobustScaler().fit(normal);model=IsolationForest(n_estimators=300,max_samples=1024,contamination='auto',random_state=42,n_jobs=-1).fit(scaler.transform(normal));report={}
 for name,d in [('validation',va),('test',te)]:
  score=-model.score_samples(scaler.transform(sequence_summary(d['x'])));report[name]=metric(d['y'],score)
 a.artifact_dir.mkdir(parents=True,exist_ok=True);joblib.dump({'scaler':scaler,'model':model},a.artifact_dir/'model.joblib');(a.artifact_dir/'metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
