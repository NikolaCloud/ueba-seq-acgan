"""Validation-only scorer for multi-stage MITRE Seq-ACGAN model selection."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from sklearn.metrics import average_precision_score,roc_auc_score
from ueba_seq_acgan.models import MITRESequenceDiscriminator
def metrics(y,s):
 o=np.argsort(s)[::-1];p=max(int(y.sum()),1);return {'pr_auc':float(average_precision_score(y,s)),'roc_auc':float(roc_auc_score(y,s)),'precision_at_100':float(y[o[:100]].mean()),'recall_at_100':float(y[o[:100]].sum()/p),'recall_at_500':float(y[o[:500]].sum()/p)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_temporal_mitre_seq_acgan'));p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--split',default='validation',choices=['validation','test']);a=p.parse_args();s=torch.load(a.artifact_dir/'checkpoint.pt',map_location='cpu',weights_only=True);d=MITRESequenceDiscriminator(s['feature_dim'],s['scenarios']).eval();d.load_state_dict(s['discriminator']);t=joblib.load(a.artifact_dir/'transformer.joblib');raw=np.load(a.sequences/f'{a.split}.npz');x=raw['x'].astype('float32');x=t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32');scores=[]
 with torch.inference_mode():
  for i in range(0,len(x),1024):_,z=d(torch.from_numpy(x[i:i+1024]));scores.append((1-torch.softmax(z,1)[:,0]).numpy())
 out={'split':a.split,'metrics':metrics(raw['y'].astype('int8'),np.concatenate(scores))};(a.artifact_dir/f'{a.split}_evaluation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
