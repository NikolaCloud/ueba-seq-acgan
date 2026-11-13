"""Diagnose why /api/generate disconnected in standalone exe."""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

temp_dir = os.path.abspath(os.path.join(os.environ.get("TEMP", "C:/Temp"), "ueba_debug_test"))
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
os.makedirs(temp_dir, exist_ok=True)

src_exe = os.path.abspath("dist/UEBA_Threat_Detection.exe")
dst_exe = os.path.join(temp_dir, "UEBA_Threat_Detection.exe")
shutil.copy2(src_exe, dst_exe)

proc = subprocess.Popen(
    [dst_exe, "serve", "--host", "127.0.0.1", "--port", "8792"],
    cwd=temp_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

server_logs = []
def reader():
    for line in proc.stdout:
        server_logs.append(line)
        print("[SERVER]", line, end="", flush=True)

t = threading.Thread(target=reader, daemon=True)
t.start()

time.sleep(15)

try:
    print("\nSending POST /api/generate...")
    req = urllib.request.Request(
        "http://127.0.0.1:8792/api/generate",
        data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req, timeout=10)
    print("Response status:", res.status)
    print("Response data:", res.read().decode("utf-8")[:200])
except Exception as e:
    print("Request exception:", e)

time.sleep(2)
proc.terminate()
try:
    proc.wait(timeout=3)
except:
    proc.kill()
