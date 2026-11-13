"""Test server and all API endpoints in-process."""

import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, "src")
from ueba_seq_acgan.dashboard import serve

server_thread = threading.Thread(
    target=serve,
    args=(
        Path("artifacts/dashboard/data.json"),
        Path("src/ueba_seq_acgan/web"),
        "127.0.0.1",
        8899,
        False,
    ),
    daemon=True,
)
server_thread.start()
time.sleep(2)

print("--- 1. Testing GET / (HTML) ---")
html = urllib.request.urlopen("http://127.0.0.1:8899/").read().decode("utf-8")
print(f"HTML received, length={len(html)}")
assert "icon.png" in html
assert "calcThresholdSlider" in html
assert "TERMS" in html
assert "btnRandomUser" in html
print("[OK] HTML verification passed!")

print("\n--- 2. Testing GET /icon.png ---")
icon_png = urllib.request.urlopen("http://127.0.0.1:8899/icon.png").read()
print(f"Icon PNG received, length={len(icon_png)}")
assert len(icon_png) > 1000
print("[OK] Icon PNG verification passed!")

print("\n--- 3. Testing GET /api/dashboard ---")
dash = json.loads(urllib.request.urlopen("http://127.0.0.1:8899/api/dashboard").read().decode("utf-8"))
print(f"Total users: {len(dash['users'])}")
first_user = dash["users"][0]
print(f"First user ID: {first_user['user']}")
print("[OK] Dashboard API verification passed!")

print("\n--- 4. Testing POST /api/generate with specified user ---")
target_user = first_user["user"]
target_name = first_user["display_name"]
req = urllib.request.Request(
    "http://127.0.0.1:8899/api/generate",
    data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42, "user": target_user}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
gen = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
gen_user = gen.get("user")
gen_name = gen.get("display_name")
print(f"Target user ID:    {target_user}")
print(f"Generated user ID: {gen_user}")
assert target_user == gen_user, f"User ID mismatch: {target_user} != {gen_user}"
assert target_name == gen_name, f"Display name mismatch: {target_name} != {gen_name}"
print(f"[OK] Exact match verified: {gen_user} == {target_user}, name matches 100%!")
print(f"[OK] Simulation scores: {gen.get('scores')}")

print("\n--- 5. Testing POST /api/generate in auto/random user mode ---")
req_auto = urllib.request.Request(
    "http://127.0.0.1:8899/api/generate",
    data=json.dumps({"scenario_id": "T1078", "intensity": 1.2, "seed": 99}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
gen_auto = json.loads(urllib.request.urlopen(req_auto, timeout=15).read().decode("utf-8"))
print(f"Auto-generated user ID: {gen_auto.get('user')}")
print("[OK] Auto generation verified!")

print("\n========================================================")
print("SUCCESS: ALL 5 IN-PROCESS TESTS PASSED PERFECTLY!")
print("========================================================")
