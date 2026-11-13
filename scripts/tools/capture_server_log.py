"""Capture exact server error on /api/generate."""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

temp_dir = os.path.abspath(os.path.join(os.environ.get("TEMP", "C:/Temp"), "ueba_exact_debug"))
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
os.makedirs(temp_dir, exist_ok=True)

src_exe = os.path.abspath("dist/UEBA_Threat_Detection.exe")
dst_exe = os.path.join(temp_dir, "UEBA_Threat_Detection.exe")
shutil.copy2(src_exe, dst_exe)

server_log_file = os.path.join(temp_dir, "server_stdout.txt")
f_out = open(server_log_file, "w", encoding="utf-8", errors="replace")

proc = subprocess.Popen(
    [dst_exe, "serve", "--host", "127.0.0.1", "--port", "8793"],
    cwd=temp_dir,
    stdout=f_out,
    stderr=subprocess.STDOUT,
)

print("Waiting 15s for server startup...")
time.sleep(15)

try:
    print("Testing /api/generate...")
    req = urllib.request.Request(
        "http://127.0.0.1:8793/api/generate",
        data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req, timeout=10)
    print("Response code:", res.status)
    print("Response body:", res.read().decode("utf-8"))
except Exception as e:
    print("Request exception:", e)

time.sleep(2)
proc.terminate()
try:
    proc.wait(timeout=5)
except:
    proc.kill()
f_out.close()

print("\n--- SERVER LOG ---")
with open(server_log_file, "r", encoding="utf-8", errors="replace") as f:
    print(f.read())
