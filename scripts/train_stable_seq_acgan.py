"""Train the stabilized Seq-ACGAN on bounded r4.2 feature sequences."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

from ueba_seq_acgan.models import StableSequenceDiscriminator, StableSequenceGenerator
from ueba_seq_acgan.transforms import BoundedLogTransformer


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sequences", type=Path, default=Path("data/processed/r4.2_sequences"))
    p.add_argument("--artifact-dir", type=Path, default=Path("artifacts/r4.2_seq_acgan"))
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--max-normal", type=int, default=30000)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--temporal-weight", type=float, default=0.0, help="Weight of adjacent-step dynamics matching")
    p.add_argument("--instance-noise", type=float, default=0.0, help="Initial Gaussian noise for discriminator inputs")
    p.add_argument("--smoke-test", action="store_true")
    a = p.parse_args()
    if a.smoke_test: a.epochs, a.max_normal = 1, 1000
    torch.manual_seed(42); rng = np.random.default_rng(42)
    manifest = json.loads((a.sequences / "manifest.json").read_text())
    raw = np.load(a.sequences / "train.npz"); x, y = raw["x"].astype(np.float32), raw["y"].astype(np.int64)
    normal, anomaly = np.flatnonzero(y == 0), np.flatnonzero(y == 1)
    selected = np.concatenate((rng.choice(normal, min(a.max_normal, len(normal)), replace=False), anomaly)); rng.shuffle(selected)
    x, y = x[selected], y[selected]
    transformer = BoundedLogTransformer(manifest["features"]).fit(x.reshape(-1, x.shape[-1]))
    x = transformer.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype(np.float32)
    data = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    counts = np.bincount(y, minlength=2); weights = 1.0 / counts[y]
    loader = DataLoader(data, batch_size=a.batch_size, sampler=WeightedRandomSampler(weights, max(len(data), a.batch_size * 20), replacement=True), drop_last=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    g, d = StableSequenceGenerator(x.shape[-1]).to(device), StableSequenceDiscriminator(x.shape[-1]).to(device)
    go, do = Adam(g.parameters(), lr=2e-4, betas=(0.5, .999)), Adam(d.parameters(), lr=1e-4, betas=(0.5, .999))
    bce, ce = nn.BCEWithLogitsLoss(), nn.CrossEntropyLoss(); history=[]
    for epoch in range(1, a.epochs + 1):
        dl=gl=fml=0.; steps=0
        for real, labels in loader:
            real, labels = real.to(device), labels.to(device); n=real.size(0)
            fake = g(torch.randn(n, real.size(1), g.latent_dim, device=device), labels)
            sigma = a.instance_noise * max(0.0, 1.0 - (epoch - 1) / max(1, a.epochs - 1))
            real_d = real + sigma * torch.randn_like(real) if sigma else real
            fake_d = fake.detach() + sigma * torch.randn_like(fake) if sigma else fake.detach()
            do.zero_grad(); rs, rc=d(real_d); fs, fc=d(fake_d)
            dloss=bce(rs, torch.full_like(rs,.9))+bce(fs,torch.full_like(fs,.1))+ce(rc,labels)+.25*ce(fc,labels)
            dloss.backward(); do.step()
            go.zero_grad(); fs,fc=d(fake); real_embedding=d.encode(real).detach(); fake_embedding=d.encode(fake)
            fm=torch.mean(torch.abs(fake_embedding.mean(0)-real_embedding.mean(0)))
            real_delta = real[:, 1:] - real[:, :-1]
            fake_delta = fake[:, 1:] - fake[:, :-1]
            temporal = torch.mean(torch.abs(real_delta.mean((0, 1)) - fake_delta.mean((0, 1))))
            temporal = temporal + torch.mean(torch.abs(real_delta.std((0, 1)) - fake_delta.std((0, 1))))
            gloss=bce(fs,torch.ones_like(fs))+ce(fc,labels)+5*fm+a.temporal_weight*temporal; gloss.backward(); go.step()
            dl+=dloss.item(); gl+=gloss.item(); fml+=fm.item(); steps+=1
        item={"epoch":epoch,"d_loss":dl/steps,"g_loss":gl/steps,"feature_matching":fml/steps,"instance_noise":sigma,"temporal_weight":a.temporal_weight}; history.append(item); print(json.dumps(item),flush=True)
    a.artifact_dir.mkdir(parents=True,exist_ok=True)
    torch.save({"generator":g.state_dict(),"discriminator":d.state_dict(),"feature_dim":x.shape[-1],"sequence_length":x.shape[1],"stable":True},a.artifact_dir/'checkpoint.pt')
    joblib.dump(transformer,a.artifact_dir/'transformer.joblib')
    (a.artifact_dir/'training.json').write_text(json.dumps({"samples":len(y),"class_counts":counts.tolist(),"history":history},indent=2))

if __name__ == "__main__": main()
