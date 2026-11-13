"""Strict normal-only conditional forecasting GAN with LDAP role context."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, numpy as np, torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset
from train_normal_conditional_gan import clean_normal_mask, stratified_normal_indices
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import RoleConditionalForecastDiscriminator, RoleConditionalForecastGenerator
from ueba_seq_acgan.transforms import BoundedLogTransformer

def main():
 p=argparse.ArgumentParser(); p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences')); p.add_argument('--ldap-dir',type=Path,default=Path('data/raw/cert/r5.2/r5.2/LDAP')); p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_normal_role_conditional_gan')); p.add_argument('--epochs',type=int,default=35); p.add_argument('--max-normal',type=int,default=60000); p.add_argument('--smoke-test',action='store_true'); a=p.parse_args()
 if a.smoke_test: a.epochs,a.max_normal=1,1000
 raw=np.load(a.sequences/'train.npz'); mask=clean_normal_mask(raw['user'],raw['end_day'],raw['y'],raw['x'].shape[1]); selected=stratified_normal_indices(raw['user'],mask,a.max_normal); x=raw['x'][selected].astype('float32'); users_raw=raw['user'][selected]; roles_raw=roles_for_windows(users_raw,raw['end_day'][selected],a.ldap_dir)
 features=json.loads((a.sequences/'manifest.json').read_text())['features']; transformer=BoundedLogTransformer(features).fit(x.reshape(-1,x.shape[-1])); x=transformer.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32')
 user_values=sorted(map(str,np.unique(users_raw))); role_values=sorted(map(str,np.unique(roles_raw))); user_map={v:i+1 for i,v in enumerate(user_values)}; role_map={v:i+1 for i,v in enumerate(role_values)}; users=np.asarray([user_map[str(v)] for v in users_raw],dtype=np.int64); roles=np.asarray([role_map[str(v)] for v in roles_raw],dtype=np.int64)
 count_indices=transformer.count_indices.tolist(); calendar_indices=transformer.calendar_indices.tolist(); loader=DataLoader(TensorDataset(torch.from_numpy(x[:,:-1]),torch.from_numpy(x[:,-1]),torch.from_numpy(users),torch.from_numpy(roles)),batch_size=256,shuffle=True,drop_last=True)
 dev=torch.device('cpu'); g=RoleConditionalForecastGenerator(x.shape[-1],count_indices,len(user_map),len(role_map)).to(dev); d=RoleConditionalForecastDiscriminator(x.shape[-1],len(user_map),len(role_map)).to(dev); go=Adam(g.parameters(),lr=2e-4,betas=(.5,.999)); do=Adam(d.parameters(),lr=1e-4,betas=(.5,.999)); bce,l1=nn.BCEWithLogitsLoss(),nn.SmoothL1Loss(); hist=[]
 for epoch in range(a.epochs):
  ds=gs=rs=0.; n=0
  for prior,real,user,role in loader:
   prior,real,user,role=prior.to(dev),real.to(dev),user.to(dev),role.to(dev); calendar=real[:,calendar_indices]; fake=g(prior,user,role,calendar); do.zero_grad(); real_score=d(prior,real,user,role); fake_score=d(prior,fake.detach(),user,role); dl=bce(real_score,torch.ones_like(real_score)*.9)+bce(fake_score,torch.zeros_like(fake_score)); dl.backward(); do.step(); go.zero_grad(); fake=g(prior,user,role,calendar); fake_score=d(prior,fake,user,role); residual=l1(fake[:,count_indices],real[:,count_indices]); gl=20*residual+.5*bce(fake_score,torch.ones_like(fake_score)); gl.backward(); go.step(); ds+=dl.item();gs+=gl.item();rs+=residual.item();n+=1
  row={'epoch':epoch+1,'d_loss':ds/n,'g_loss':gs/n,'count_forecast_smooth_l1':rs/n};hist.append(row);print(json.dumps(row),flush=True)
 a.artifact_dir.mkdir(parents=True,exist_ok=True); torch.save({'generator':g.state_dict(),'discriminator':d.state_dict(),'feature_dim':x.shape[-1],'sequence_length':x.shape[1],'count_indices':count_indices,'calendar_indices':calendar_indices,'normal_only':True,'architecture':'role_personalised_conditional_forecasting_gan'},a.artifact_dir/'checkpoint.pt'); joblib.dump({'transformer':transformer,'user_index':user_map,'role_index':role_map},a.artifact_dir/'transformer_users_roles.joblib'); (a.artifact_dir/'training.json').write_text(json.dumps({'normal_windows':len(x),'users_represented':len(user_map),'roles_represented':len(role_map),'observed_anomalies_used_for_optimisation':False,'history':hist},indent=2))
if __name__=='__main__': main()
