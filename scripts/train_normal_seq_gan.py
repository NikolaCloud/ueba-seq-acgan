"""Normal-only adversarial sequence autoencoder; no real anomalies are used to train."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib,numpy as np,torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader,TensorDataset
from ueba_seq_acgan.models import NormalSequenceEncoder,NormalSequenceDecoder,StableSequenceDiscriminator
from ueba_seq_acgan.transforms import BoundedLogTransformer
def corrupt(x, profiles, feature_names):
 y=x.clone(); rows=torch.arange(x.size(0),device=x.device); kinds=torch.randint(0,len(profiles),(x.size(0),),device=x.device)
 for kind, profile in enumerate(profiles):
  mask=kinds==kind
  for name in profile['features']:
   index=feature_names.index(name); y[mask,-1,index]=torch.clamp(y[mask,-1,index]+torch.empty(mask.sum(),device=x.device).uniform_(.6,1.35),-1,1)
 return y
def main():
 p=argparse.ArgumentParser();p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_sequences'));p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_normal_seq_gan'));p.add_argument('--epochs',type=int,default=30);p.add_argument('--max-normal',type=int,default=30000);p.add_argument('--smoke-test',action='store_true');a=p.parse_args();
 if a.smoke_test:a.epochs,a.max_normal=1,1000
 raw=np.load(a.sequences/'train.npz');x=raw['x'][raw['y']==0].astype('float32');x=x[:a.max_normal];features=json.loads((a.sequences/'manifest.json').read_text())['features'];profiles=json.loads(Path('configs/mitre_pseudo_scenarios.json').read_text());t=BoundedLogTransformer(features).fit(x.reshape(-1,x.shape[-1]));x=t.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype('float32');loader=DataLoader(TensorDataset(torch.from_numpy(x)),batch_size=128,shuffle=True,drop_last=True);dev=torch.device('cpu');e=NormalSequenceEncoder(x.shape[-1]).to(dev);g=NormalSequenceDecoder(x.shape[-1]).to(dev);d=StableSequenceDiscriminator(x.shape[-1]).to(dev);eo=Adam(list(e.parameters())+list(g.parameters()),2e-4);do=Adam(d.parameters(),1e-4);bce,ce,l1=nn.BCEWithLogitsLoss(),nn.CrossEntropyLoss(),nn.L1Loss();hist=[]
 for ep in range(a.epochs):
  dl=gl=0.;n=0
  for (real,) in loader:
   real=real.to(dev);recon=g(e(real),real.size(1));pseudo=corrupt(real,profiles,features);do.zero_grad();rs,ra=d(real);fs,fa=d(recon.detach());_,pa=d(pseudo);loss=bce(rs,torch.ones_like(rs))+bce(fs,torch.zeros_like(fs))+ce(ra,torch.zeros(len(real),dtype=torch.long,device=dev))+ce(fa,torch.zeros(len(real),dtype=torch.long,device=dev))+ce(pa,torch.ones(len(real),dtype=torch.long,device=dev));loss.backward();do.step();eo.zero_grad();fs,fa=d(recon);lossg=10*l1(recon,real)+bce(fs,torch.ones_like(fs))+ce(fa,torch.zeros(len(real),dtype=torch.long,device=dev));lossg.backward();eo.step();dl+=loss.item();gl+=lossg.item();n+=1
  print(json.dumps({'epoch':ep+1,'d_loss':dl/n,'g_loss':gl/n}),flush=True);hist.append({'d_loss':dl/n,'g_loss':gl/n})
 a.artifact_dir.mkdir(parents=True,exist_ok=True);torch.save({'encoder':e.state_dict(),'decoder':g.state_dict(),'discriminator':d.state_dict(),'feature_dim':x.shape[-1],'sequence_length':x.shape[1],'normal_only':True},a.artifact_dir/'checkpoint.pt');joblib.dump(t,a.artifact_dir/'transformer.joblib');(a.artifact_dir/'training.json').write_text(json.dumps({'normal_samples':len(x),'profiles':profiles,'history':hist},indent=2))
if __name__=='__main__':main()
