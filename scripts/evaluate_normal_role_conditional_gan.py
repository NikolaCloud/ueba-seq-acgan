"""Held-out evaluation for the strict normal-only LDAP-role conditional GAN."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, numpy as np, torch
from sklearn.metrics import average_precision_score, roc_auc_score
from train_normal_conditional_gan import clean_normal_mask
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import RoleConditionalForecastDiscriminator, RoleConditionalForecastGenerator

def codes(values,mapping): return np.asarray([mapping.get(str(v),0) for v in values],dtype=np.int64)
def load(path):
 p=np.load(path); return p['x'].astype('float32'),p['y'].astype('int8'),p['user'],p['end_day']
@torch.inference_mode()
def predict(g,d,t,x,u,r,counts,cals,dev):
 tx=t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32'); residual=[]; critic=[]
 for i in range(0,len(x),1024):
  prior=torch.from_numpy(tx[i:i+1024,:-1]).to(dev); actual=torch.from_numpy(tx[i:i+1024,-1]).to(dev); user=torch.from_numpy(u[i:i+1024]).to(dev); role=torch.from_numpy(r[i:i+1024]).to(dev); fake=g(prior,user,role,actual[:,cals]); source=d(prior,actual,user,role); pred=t.inverse_transform(fake.cpu().numpy())[:,counts]; residual.append(np.abs(np.log1p(x[i:i+1024,-1,counts])-np.log1p(pred))); critic.append((-torch.sigmoid(source)).cpu().numpy())
 return np.concatenate(residual),np.concatenate(critic)
def scale(x,lo,hi): return np.clip((x-lo)/np.maximum(hi-lo,1e-8),0,1)
def report(y,s):
 order=np.argsort(s)[::-1]; pos=max(int(y.sum()),1); return {'pr_auc':float(average_precision_score(y,s)),'roc_auc':float(roc_auc_score(y,s)),'precision_at_100':float(y[order[:100]].mean()),'recall_at_100':float(y[order[:100]].sum()/pos),'recall_at_500':float(y[order[:500]].sum()/pos)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_normal_role_conditional_gan'));p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--ldap-dir',type=Path,default=Path('data/raw/cert/r5.2/r5.2/LDAP'));a=p.parse_args();dev=torch.device('cpu');state=torch.load(a.artifact_dir/'checkpoint.pt',map_location=dev,weights_only=True);bundle=joblib.load(a.artifact_dir/'transformer_users_roles.joblib');t,umap,rmap=bundle['transformer'],bundle['user_index'],bundle['role_index'];g=RoleConditionalForecastGenerator(state['feature_dim'],state['count_indices'],len(umap),len(rmap)).eval();d=RoleConditionalForecastDiscriminator(state['feature_dim'],len(umap),len(rmap)).eval();g.load_state_dict(state['generator']);d.load_state_dict(state['discriminator']);tr,ty,tu,td=load(a.sequences/'train.npz');va,vy,vu,vd=load(a.sequences/'validation.npz');te,ey,eu,ed=load(a.sequences/'test.npz');clean=clean_normal_mask(tu,td,ty,tr.shape[1]);trr,trc=predict(g,d,t,tr[clean],codes(tu[clean],umap),codes(roles_for_windows(tu[clean],td[clean],a.ldap_dir),rmap),state['count_indices'],state['calendar_indices'],dev);median,p99=np.median(trr,0),np.quantile(trr,.99,0);cb=np.quantile(trc,[.5,.99])
 def score(x,u,days):
  rr,cc=predict(g,d,t,x,codes(u,umap),codes(roles_for_windows(u,days,a.ldap_dir),rmap),state['count_indices'],state['calendar_indices'],dev); return .85*np.sort(scale(rr,median,p99),axis=1)[:,-3:].mean(1)+.15*scale(cc,*cb)
 out={'method':'strict normal-only LDAP-role personalised conditional forecasting GAN','observed_anomaly_labels_used_for_training_or_calibration':False,'validation':report(vy,score(va,vu,vd)),'test':report(ey,score(te,eu,ed)),'unknown_user_codes_test':int((codes(eu,umap)==0).sum()),'unknown_role_codes_test':int((codes(roles_for_windows(eu,ed,a.ldap_dir),rmap)==0).sum())};(a.artifact_dir/'evaluation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
