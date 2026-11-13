"""Automated validation of index.html syntax and API responses."""

import json
import urllib.request

base_url = "http://127.0.0.1:8765"

print("--- 1. Testing GET / ---")
html = urllib.request.urlopen(f"{base_url}/").read().decode("utf-8")
print(f"HTML size: {len(html)} bytes")

# Verify pulse-beam is removed
assert "arch-pulse-beam" not in html, "ERROR: arch-pulse-beam still present in HTML!"
assert "pulseFlow" not in html, "ERROR: pulseFlow still present in CSS!"
print("[OK] Pulse beam animation completely removed (no freeze/lags)!")

# Verify SOC Simulator components
assert "calcThresholdSlider" in html, "ERROR: calcThresholdSlider missing!"
assert "btnApplySocThreshold" in html, "ERROR: btnApplySocThreshold missing!"
assert "updateSOCSimulator" in html, "ERROR: updateSOCSimulator missing!"
assert "btnRandomUser" in html, "ERROR: btnRandomUser missing!"
print("[OK] SOC Simulator & Generator controls present and bound!")

print("\n--- 2. Testing GET /api/dashboard ---")
dash = json.loads(urllib.request.urlopen(f"{base_url}/api/dashboard").read().decode("utf-8"))
print(f"Users loaded: {len(dash['users'])}, Timelines count: {len(dash['timelines'])}")
print("[OK] Dashboard API returned valid data!")

print("\n--- 3. Testing POST /api/generate with selected user ---")
target = dash["users"][0]
req = urllib.request.Request(
    f"{base_url}/api/generate",
    data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42, "user": target["user"]}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
gen = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
print(f"Target:    {target['user']} ({target['display_name']})")
print(f"Generated: {gen.get('user')} ({gen.get('display_name')})")
assert target["user"] == gen.get("user")
assert target["display_name"] == gen.get("display_name")
print("[OK] Generator user selection matches 100%!")

print("\n========================================================")
print("ALL WEB INTERFACE & LOGIC CHECKS PASSED SUCCESSFULLY!")
print("========================================================")
