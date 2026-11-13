"""Test the standalone UEBA_Threat_Detection.exe in an isolated directory."""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

temp_dir = os.path.abspath(os.path.join(os.environ.get("TEMP", "C:/Temp"), "ueba_isolated_test_v2"))
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
os.makedirs(temp_dir, exist_ok=True)

src_exe = os.path.abspath("dist/UEBA_Threat_Detection.exe")
dst_exe = os.path.join(temp_dir, "UEBA_Threat_Detection.exe")
print(f"Copying {src_exe} to {dst_exe}...")
shutil.copy2(src_exe, dst_exe)

print(f"Starting {dst_exe} in isolated cwd {temp_dir}...")
proc = subprocess.Popen(
    [dst_exe, "serve", "--host", "127.0.0.1", "--port", "8796"],
    cwd=temp_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

# Wait for server ready (up to 60s for onefile unpacking)
ready = False
start_time = time.time()
print("Waiting for server to become ready on http://127.0.0.1:8796...")
while time.time() - start_time < 60:
    try:
        urllib.request.urlopen("http://127.0.0.1:8796/", timeout=1)
        ready = True
        print(f"Server is ready after {time.time() - start_time:.1f}s!")
        break
    except Exception:
        time.sleep(1.0)

if not ready:
    print("ERROR: Server failed to start within 60s!")
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
        print("Process output:\n", out)
    except:
        proc.kill()
    sys.exit(1)

try:
    print("\n--- Test 1: GET / (HTML Interface) ---")
    html = urllib.request.urlopen("http://127.0.0.1:8796/").read().decode("utf-8")
    print(f"HTML received, length={len(html)}, title present={'<title>' in html}")

    print("\n--- Test 2: GET /api/dashboard ---")
    dash = json.loads(urllib.request.urlopen("http://127.0.0.1:8796/api/dashboard").read().decode("utf-8"))
    users = len(dash.get("users", []))
    print(f"Dashboard data OK, total users={users}, summary observed anomalies={dash.get('summary', {}).get('observed_anomalies')}")

    print("\n--- Test 3: GET /api/scenarios ---")
    scenarios = json.loads(urllib.request.urlopen("http://127.0.0.1:8796/api/scenarios").read().decode("utf-8"))
    print(f"Scenarios list OK, count={len(scenarios)}, names={[s['id'] for s in scenarios]}")

    print("\n--- Test 4: POST /api/generate (T1052.001) ---")
    req = urllib.request.Request(
        "http://127.0.0.1:8796/api/generate",
        data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    gen = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
    print(f"Standard generation OK! User={gen.get('user')}, role={gen.get('role')}, scores={gen.get('scores')}")

    print("\n--- Test 5: POST /api/generate (Custom profile from constructor) ---")
    req_custom = urllib.request.Request(
        "http://127.0.0.1:8796/api/generate",
        data=json.dumps({
            "scenario_id": "custom",
            "intensity": 1.2,
            "custom_profile": {
                "name": "Пользовательский инцидент",
                "features": {"device_connect": 1.5, "file_events": 1.2},
                "start_day": 12,
                "duration": 2
            }
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    gen_custom = json.loads(urllib.request.urlopen(req_custom, timeout=15).read().decode("utf-8"))
    print(f"Custom generation OK! Affected days={gen_custom.get('affected_days')}, scores={gen_custom.get('scores')}")

    print("\n========================================================")
    print("SUCCESS: ALL 5 STANDALONE TESTS PASSED WITHOUT ERRORS!")
    print("========================================================")

except Exception as e:
    print(f"\nTEST FAILED: {e}")
    import traceback
    traceback.print_exc()

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
    print("Process terminated.")
