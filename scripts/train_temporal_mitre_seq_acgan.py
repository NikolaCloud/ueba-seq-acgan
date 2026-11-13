"""Train multi-stage MITRE scenario Seq-ACGAN from normal data only."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader,TensorDataset
from train_normal_conditional_gan import clean_normal_mask,stratified_normal_indices
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import MITRESequenceDiscriminator,RoleConditionalForecastGenerator

def inject(x,profiles,features):
 out=x.clone(); labels=torch.randint(1,len(profiles)+1,(len(x),),device=x.device)
 for label,profile in enumerate(profiles,1):
  mask=labels==label
  for stage_no,stage in enumerate(profile['stages']):
   days=min(stage['days'],x.size(1)); low,high=(.18,.55) if stage_no==0 else (.42,1.05)
   for name in stage['features']:
    j=features.index(name);delta=torch.empty(int(mask.sum()),days,device=x.device).uniform_(low,high);out[mask,-days:,j]=torch.clamp(out[mask,-days:,j]+delta,-1,1)
 return out,labels
def main():
 p=argparse.ArgumentParser();p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--normal-gan-dir',type=Path,default=Path('artifacts/r5.2_normal_role_conditional_gan'));p.add_argument('--ldap-dir',type=Path,default=Path('data/raw/cert/r5.2/r5.2/LDAP'));p.add_argument('--profiles',type=Path,default=Path('configs/mitre_temporal_scenarios.json'));p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_temporal_mitre_seq_acgan'));p.add_argument('--epochs',type=int,default=30);p.add_argument('--max-normal',type=int,default=40000);p.add_argument('--smoke-test',action='store_true');a=p.parse_args()
 if a.smoke_test:a.epochs,a.max_normal=1,1000
 raw=np.load(a.sequences/'train.npz');clean=clean_normal_mask(raw['user'],raw['end_day'],raw['y'],raw['x'].shape[1]);sel=stratified_normal_indices(raw['user'],clean,a.max_normal);x=raw['x'][sel].astype('float32');u_raw=raw['user'][sel];days=raw['end_day'][sel];state=torch.load(a.normal_gan_dir/'checkpoint.pt',map_location='cpu',weights_only=True);bundle=joblib.load(a.normal_gan_dir/'transformer_users_roles.joblib');t,um,rm=bundle['transformer'],bundle['user_index'],bundle['role_index'];features=json.loads((a.sequences/'manifest.json').read_text())['features'];profiles=json.loads(a.profiles.read_text());x=t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32');u=np.asarray([um.get(str(v),0) for v in u_raw]);r_raw=roles_for_windows(u_raw,days,a.ldap_dir);r=np.asarray([rm.get(str(v),0) for v in r_raw]);loader=DataLoader(TensorDataset(torch.from_numpy(x),torch.from_numpy(u),torch.from_numpy(r)),batch_size=256,shuffle=True,drop_last=True)
 dev=torch.device('cpu');g=RoleConditionalForecastGenerator(state['feature_dim'],state['count_indices'],len(um),len(rm)).eval();g.load_state_dict(state['generator']);d=MITRESequenceDiscriminator(x.shape[-1],len(profiles)).to(dev);opt=Adam(d.parameters(),1e-4);bce,ce=nn.BCEWithLogitsLoss(),nn.CrossEntropyLoss();hist=[]
 for e in range(a.epochs):
  total=0.;n=0
  for real,user,role in loader:
   real,user,role=real.to(dev),user.to(dev),role.to(dev)
   with torch.no_grad():base=g(real[:,:-1],user,role,real[:,-1,state['calendar_indices']]);normal=torch.cat((real[:,:-1],base.unsqueeze(1)),1);fake,labels=inject(normal,profiles,features)
   opt.zero_grad();rs,rc=d(real);fs,fc=d(fake);loss=bce(rs,torch.ones_like(rs))+bce(fs,torch.zeros_like(fs))+ce(rc,torch.zeros(len(real),dtype=torch.long,device=dev))+ce(fc,labels);loss.backward();opt.step();total+=loss.item();n+=1
  row={'epoch':e+1,'loss':total/n};hist.append(row);print(json.dumps(row),flush=True)
 a.artifact_dir.mkdir(parents=True,exist_ok=True);torch.save({'discriminator':d.state_dict(),'feature_dim':x.shape[-1],'scenarios':len(profiles),'architecture':'multistage_MITRE_Seq_ACGAN'},a.artifact_dir/'checkpoint.pt');joblib.dump(t,a.artifact_dir/'transformer.joblib');(a.artifact_dir/'training.json').write_text(json.dumps({'profiles':profiles,'real_anomaly_labels_used_for_optimisation':False,'history':hist},indent=2))
if __name__=='__main__':main()
