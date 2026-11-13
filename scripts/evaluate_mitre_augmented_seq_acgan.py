"""Final real-CERT evaluation of the MITRE-augmented Seq-ACGAN detector."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from sklearn.metrics import average_precision_score,roc_auc_score
from ueba_seq_acgan.models import SequenceDiscriminator
def metric(y,s):
 order=np.argsort(s)[::-1];pos=max(int(y.sum()),1);return {'pr_auc':float(average_precision_score(y,s)),'roc_auc':float(roc_auc_score(y,s)),'precision_at_100':float(y[order[:100]].mean()),'recall_at_100':float(y[order[:100]].sum()/pos),'recall_at_500':float(y[order[:500]].sum()/pos)}
@torch.inference_mode()
def score(d,t,path):
 raw=np.load(path);x=raw['x'].astype('float32');x=t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32');out=[]
 for i in range(0,len(x),1024):_,logits=d(torch.from_numpy(x[i:i+1024]));out.append(torch.softmax(logits,1)[:,1].numpy())
 return raw['y'].astype('int8'),np.concatenate(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_mitre_augmented_seq_acgan'));p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));a=p.parse_args();state=torch.load(a.artifact_dir/'checkpoint.pt',map_location='cpu',weights_only=True);d=SequenceDiscriminator(state['feature_dim']).eval();d.load_state_dict(state['discriminator']);t=joblib.load(a.artifact_dir/'transformer.joblib');vy,vs=score(d,t,a.sequences/'validation.npz');ty,ts=score(d,t,a.sequences/'test.npz');out={'method':'normal GAN generated baseline + MITRE scenario augmented two-head Seq-ACGAN','real_anomalies_used_only_for_evaluation':True,'validation':metric(vy,vs),'test':metric(ty,ts)};(a.artifact_dir/'evaluation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
