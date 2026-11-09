"""Train a two-head Seq-ACGAN detector from normal GAN forecasts + MITRE scenarios.

Observed CERT anomaly labels are used only to exclude contaminated windows.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader,TensorDataset
from train_normal_conditional_gan import clean_normal_mask,stratified_normal_indices
from ueba_seq_acgan.ldap import roles_for_windows
from ueba_seq_acgan.models import RoleConditionalForecastGenerator,SequenceDiscriminator

def apply_profile(sequence,profiles,features):
    """MITRE scenario delta in bounded feature space; calendar fields are untouched."""
    output=sequence.clone(); kinds=torch.randint(len(profiles),(len(sequence),),device=sequence.device)
    for kind,profile in enumerate(profiles):
        chosen=kinds==kind
        for name in profile['features']:
            index=features.index(name)
            # Scenario intensity is fixed before evaluation; only the final-day telemetry changes.
            delta=torch.empty(int(chosen.sum()),device=sequence.device).uniform_(.45,1.10)
            output[chosen,-1,index]=torch.clamp(output[chosen,-1,index]+delta,-1,1)
    return output,kinds

def main():
 p=argparse.ArgumentParser();p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--normal-gan-dir',type=Path,default=Path('artifacts/r5.2_normal_role_conditional_gan'));p.add_argument('--ldap-dir',type=Path,default=Path('data/raw/cert/r5.2/r5.2/LDAP'));p.add_argument('--profiles',type=Path,default=Path('configs/mitre_pseudo_scenarios.json'));p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_mitre_augmented_seq_acgan'));p.add_argument('--epochs',type=int,default=25);p.add_argument('--max-normal',type=int,default=40000);p.add_argument('--smoke-test',action='store_true');a=p.parse_args()
 if a.smoke_test:a.epochs,a.max_normal=1,1000
 raw=np.load(a.sequences/'train.npz');clean=clean_normal_mask(raw['user'],raw['end_day'],raw['y'],raw['x'].shape[1]);sel=stratified_normal_indices(raw['user'],clean,a.max_normal);x=raw['x'][sel].astype('float32'); users_raw=raw['user'][sel];days=raw['end_day'][sel]
 state=torch.load(a.normal_gan_dir/'checkpoint.pt',map_location='cpu',weights_only=True);bundle=joblib.load(a.normal_gan_dir/'transformer_users_roles.joblib');transformer,umap,rmap=bundle['transformer'],bundle['user_index'],bundle['role_index'];features=json.loads((a.sequences/'manifest.json').read_text())['features'];profiles=json.loads(a.profiles.read_text())
 x=transformer.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32');users=np.asarray([umap.get(str(v),0) for v in users_raw],dtype=np.int64);roles_raw=roles_for_windows(users_raw,days,a.ldap_dir);roles=np.asarray([rmap.get(str(v),0) for v in roles_raw],dtype=np.int64);loader=DataLoader(TensorDataset(torch.from_numpy(x),torch.from_numpy(users),torch.from_numpy(roles)),batch_size=256,shuffle=True,drop_last=True)
 dev=torch.device('cpu');g=RoleConditionalForecastGenerator(state['feature_dim'],state['count_indices'],len(umap),len(rmap)).to(dev).eval();g.load_state_dict(state['generator']);
 for param in g.parameters():param.requires_grad=False
 d=SequenceDiscriminator(x.shape[-1]).to(dev);opt=Adam(d.parameters(),lr=1e-4);bce,ce=nn.BCEWithLogitsLoss(),nn.CrossEntropyLoss();hist=[]
 for epoch in range(a.epochs):
  total=source=klass=0.;n=0
  for real,user,role in loader:
   real,user,role=real.to(dev),user.to(dev),role.to(dev)
   with torch.no_grad(): base=g(real[:,:-1],user,role,real[:,-1,state['calendar_indices']]); generated=torch.cat((real[:,:-1],base.unsqueeze(1)),1); scenario,_=apply_profile(generated,profiles,features)
   opt.zero_grad();rs,rc=d(real);fs,fc=d(scenario);loss_source=bce(rs,torch.ones_like(rs))+bce(fs,torch.zeros_like(fs));loss_class=ce(rc,torch.zeros(len(real),dtype=torch.long,device=dev))+ce(fc,torch.ones(len(real),dtype=torch.long,device=dev));loss=loss_source+loss_class;loss.backward();opt.step();total+=loss.item();source+=loss_source.item();klass+=loss_class.item();n+=1
  row={'epoch':epoch+1,'loss':total/n,'source_loss':source/n,'anomaly_loss':klass/n};hist.append(row);print(json.dumps(row),flush=True)
 a.artifact_dir.mkdir(parents=True,exist_ok=True);torch.save({'discriminator':d.state_dict(),'feature_dim':x.shape[-1],'sequence_length':x.shape[1],'architecture':'normal_GAN_plus_MITRE_scenario_Seq_ACGAN'},a.artifact_dir/'checkpoint.pt');joblib.dump(transformer,a.artifact_dir/'transformer.joblib');(a.artifact_dir/'training.json').write_text(json.dumps({'normal_windows':len(x),'real_anomaly_labels_used_for_optimisation':False,'normal_generator':str(a.normal_gan_dir),'scenario_profiles':profiles,'history':hist},indent=2))
if __name__=='__main__':main()
