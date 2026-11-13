"""Compile standalone one-file executable using PyInstaller with all dependencies bundled."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import xgboost

root = Path(__file__).resolve().parent
xgb_dir = Path(xgboost.__file__).resolve().parent
xgb_lib_dir = xgb_dir / "lib"

# Collect all data pairs (source, target_in_bundle)
datas = [
    (str(root / "src" / "ueba_seq_acgan" / "web"), "src/ueba_seq_acgan/web"),
    (str(root / "configs"), "configs"),
    (str(root / "artifacts" / "dashboard"), "artifacts/dashboard"),
    (str(root / "artifacts" / "r5.2_normal_role_conditional_gan"), "artifacts/r5.2_normal_role_conditional_gan"),
    (str(root / "artifacts" / "r5.2_mitre_augmented_seq_acgan"), "artifacts/r5.2_mitre_augmented_seq_acgan"),
    (str(root / "artifacts" / "r5.2_gpu_detector"), "artifacts/r5.2_gpu_detector"),
    (str(root / "artifacts" / "r5.2_low_shot_gan"), "artifacts/r5.2_low_shot_gan"),
    (str(root / "data" / "processed" / "r5.2_sequences" / "validation.npz"), "data/processed/r5.2_sequences"),
    (str(root / "data" / "processed" / "r5.2_sequences" / "manifest.json"), "data/processed/r5.2_sequences"),
    (str(root / "data" / "raw" / "cert" / "r5.2" / "r5.2" / "LDAP"), "data/raw/cert/r5.2/r5.2/LDAP"),
    (str(xgb_dir), "xgboost"),
]

binaries = []
if (xgb_lib_dir / "xgboost.dll").exists():
    binaries.append((str(xgb_lib_dir / "xgboost.dll"), "xgboost/lib"))

hidden_imports = [
    "torch",
    "torch.nn",
    "torch.nn.functional",
    "xgboost",
    "xgboost.core",
    "xgboost.training",
    "xgboost.sklearn",
    "sklearn",
    "sklearn.ensemble",
    "sklearn.preprocessing",
    "sklearn.preprocessing._data",
    "sklearn.utils",
    "joblib",
    "joblib.numpy_pickle",
    "numpy",
    "scipy",
    "scipy.stats",
    "scipy.signal",
    "scipy.sparse",
    "pandas",
    "ueba_seq_acgan",
    "ueba_seq_acgan.transforms",
    "ueba_seq_acgan.models",
    "ueba_seq_acgan.synthetic",
    "ueba_seq_acgan.risk",
    "ueba_seq_acgan.ldap",
    "ueba_seq_acgan.identity",
    "ueba_seq_acgan.paths",
    "ueba_seq_acgan.dashboard",
    "ueba_seq_acgan.audit",
    "ueba_seq_acgan.trust",
]

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--onefile",
    "--clean",
    "--noconfirm",
    "--name",
    "UEBA_Threat_Detection",
    "--icon",
    str(root / "icon.ico"),
    "--paths",
    str(root / "src"),
]

for src, dst in datas:
    cmd.extend(["--add-data", f"{src};{dst}"])

for src, dst in binaries:
    cmd.extend(["--add-binary", f"{src};{dst}"])

for imp in hidden_imports:
    cmd.extend(["--hidden-import", imp])

entrypoint = str(root / "src" / "ueba_seq_acgan" / "__main__.py")
cmd.append(entrypoint)

print("=" * 60)
print("Starting PyInstaller standalone executable compilation...")
print("=" * 60)
res = subprocess.run(cmd, cwd=str(root))
if res.returncode != 0:
    print(f"PyInstaller build failed with return code {res.returncode}!")
    sys.exit(res.returncode)

exe_path = root / "dist" / "UEBA_Threat_Detection.exe"
root_exe_path = root / "UEBA_Threat_Detection.exe"

try:
    shutil.copy2(str(exe_path), str(root_exe_path))
    print(f"Copied standalone EXE to workspace root: {root_exe_path}")
except Exception as e:
    print(f"Notice: Could not copy to root ({e}). File in dist/ is available.")

size_mb = exe_path.stat().st_size / (1024 * 1024)
print("=" * 60)
print(f"SUCCESS: Executable successfully built!")
print(f"File: {exe_path}")
print(f"Size: {size_mb:.1f} MB")
print("=" * 60)
