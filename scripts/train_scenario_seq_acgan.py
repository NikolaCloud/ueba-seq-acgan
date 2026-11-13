"""Train scenario-conditioned Seq-ACGAN: normal + four CERT r5.2 scenarios."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, numpy as np, torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from ueba_seq_acgan.models import ScenarioSequenceDiscriminator, ScenarioSequenceGenerator
from ueba_seq_acgan.transforms import BoundedLogTransformer

def main() -> None:
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--sequences',type=Path,default=Path('data/processed/r5.2_scenario_sequences')); p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/r5.2_scenario_seq_acgan')); p.add_argument('--epochs',type=int,default=40); p.add_argument('--max-normal',type=int,default=30000); p.add_argument('--batch-size',type=int,default=128); p.add_argument('--smoke-test',action='store_true'); a=p.parse_args()
 if a.smoke_test: a.epochs,a.max_normal=1,1000
 torch.manual_seed(42); rng=np.random.default_rng(42); manifest=json.loads((a.sequences/'manifest.json').read_text()); raw=np.load(a.sequences/'train.npz'); x=raw['x'].astype(np.float32); scenario=raw['scenario'].astype(np.int64); binary=(scenario>0).astype(np.int64)
 normal=np.flatnonzero(scenario==0); anomaly=np.flatnonzero(scenario>0); selected=np.concatenate((rng.choice(normal,min(len(normal),a.max_normal),replace=False),anomaly)); rng.shuffle(selected); x,scenario,binary=x[selected],scenario[selected],binary[selected]
 transform=BoundedLogTransformer(manifest['features']).fit(x.reshape(-1,x.shape[-1])); x=transform.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype(np.float32)
 data=TensorDataset(torch.from_numpy(x),torch.from_numpy(scenario),torch.from_numpy(binary)); counts=np.bincount(scenario,minlength=5); weights=1.0/counts[scenario]; loader=DataLoader(data,batch_size=a.batch_size,sampler=WeightedRandomSampler(weights,max(len(data),a.batch_size*20),replacement=True),drop_last=True)
 device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); g=ScenarioSequenceGenerator(x.shape[-1]).to(device); d=ScenarioSequenceDiscriminator(x.shape[-1]).to(device); go=Adam(g.parameters(),lr=2e-4,betas=(.5,.999)); do=Adam(d.parameters(),lr=1e-4,betas=(.5,.999)); bce,ce=nn.BCEWithLogitsLoss(),nn.CrossEntropyLoss(); history=[]
 for epoch in range(1,a.epochs+1):
  dl=gl=0.;steps=0
  for real,sc,binary_label in loader:
   real,sc,binary_label=real.to(device),sc.to(device),binary_label.to(device); n=len(real); fake=g(torch.randn(n,real.size(1),g.latent_dim,device=device),sc)
   do.zero_grad(); rs,rc=d(real,sc); fs,fc=d(fake.detach(),sc); dloss=bce(rs,torch.full_like(rs,.9))+bce(fs,torch.full_like(fs,.1))+ce(rc,binary_label)+.25*ce(fc,binary_label); dloss.backward();do.step()
   go.zero_grad();fs,fc=d(fake,sc); real_embed=d.encode(real).detach(); fake_embed=d.encode(fake); fm=torch.mean(torch.abs(fake_embed.mean(0)-real_embed.mean(0))); gloss=bce(fs,torch.ones_like(fs))+ce(fc,binary_label)+5*fm;gloss.backward();go.step();dl+=dloss.item();gl+=gloss.item();steps+=1
  item={'epoch':epoch,'d_loss':dl/steps,'g_loss':gl/steps};history.append(item);print(json.dumps(item),flush=True)
 a.artifact_dir.mkdir(parents=True,exist_ok=True);torch.save({'generator':g.state_dict(),'discriminator':d.state_dict(),'feature_dim':x.shape[-1],'sequence_length':x.shape[1],'scenario':True},a.artifact_dir/'checkpoint.pt');joblib.dump(transform,a.artifact_dir/'transformer.joblib');(a.artifact_dir/'training.json').write_text(json.dumps({'class_counts':counts.tolist(),'history':history},indent=2))
if __name__=='__main__':main()
