"""Evaluate scenario-conditioned Seq-ACGAN on r5.2."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score
from ueba_seq_acgan.models import ScenarioSequenceDiscriminator,ScenarioSequenceGenerator

def summary(x): return np.concatenate((x[:,-1],x.mean(1),x.std(1),x.max(1),x[:,-1]-x[:,0]),1)
def load(path,t):
 p=np.load(path);x=p['x'].astype('float32');return t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32'),p['y'].astype('int8'),p['scenario'].astype('int64')
def metrics(y,s): return {'pr_auc':float(average_precision_score(y,s)),'roc_auc':float(roc_auc_score(y,s)),'recall_at_100':float(y[np.argsort(s)[-100:]].sum()/y.sum())}
@torch.inference_mode()
def predict(d,x,sc,dev):
 a=[];r=[]
 for i in range(0,len(x),1024):
  src,anom=d(torch.from_numpy(x[i:i+1024]).to(dev),torch.from_numpy(sc[i:i+1024]).to(dev));a.append(torch.softmax(anom,1)[:,1].cpu().numpy());r.append(torch.sigmoid(src).cpu().numpy())
 return np.concatenate(a),np.concatenate(r)
def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_scenario_seq_acgan'));p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_scenario_sequences'));a=p.parse_args();dev=torch.device('cpu');st=torch.load(a.artifact_dir/'checkpoint.pt',map_location=dev,weights_only=True);g=ScenarioSequenceGenerator(st['feature_dim']).eval();d=ScenarioSequenceDiscriminator(st['feature_dim']).eval();g.load_state_dict(st['generator']);d.load_state_dict(st['discriminator']);t=joblib.load(a.artifact_dir/'transformer.joblib');tr,ty,ts=load(a.sequences/'train.npz',t);va,vy,vs=load(a.sequences/'validation.npz',t);te,ey,es=load(a.sequences/'test.npz',t);vscore,vreal=predict(d,va,vs,dev);tscore,treal=predict(d,te,es,dev);sc=np.repeat(np.arange(5),1000);fake=g(torch.randn(len(sc),st['sequence_length'],g.latent_dim),torch.from_numpy(sc)).detach().numpy();_,fsource=predict(d,fake,sc,dev);clf=HistGradientBoostingClassifier(max_iter=150,class_weight='balanced',random_state=42).fit(summary(fake),(sc>0));tstr=clf.predict_proba(summary(te))[:,1];out={'anomaly_head':{'validation':metrics(vy,vscore),'test':metrics(ey,tscore)},'source':{'real_validation':float(vreal.mean()),'real_test':float(treal.mean()),'fake':float(fsource.mean())},'tstr':metrics(ey,tstr),'scenario_train_counts':{str(i):int((ts==i).sum()) for i in range(5)}};(a.artifact_dir/'scenario_evaluation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
