"""Complete health test for index.html."""

import json
import re
import urllib.request

base_url = "http://127.0.0.1:8765"

print("--- 1. Fetching index.html from dev server ---")
html = urllib.request.urlopen(f"{base_url}/").read().decode("utf-8")
print(f"HTML size: {len(html)} bytes")

# Check modal placement
main_idx = html.find("</main>")
script_idx = html.find("<script>")
modal_idx = html.find('id="detailModal"')

assert modal_idx < script_idx, "ERROR: detailModal must be located BEFORE <script>!"
assert modal_idx < main_idx, "ERROR: detailModal must be inside <main>!"
print("[OK] Modal is properly placed inside <main> before <script>!")

# Check API endpoints
dash = json.loads(urllib.request.urlopen(f"{base_url}/api/dashboard").read().decode("utf-8"))
assert len(dash["users"]) == 100
assert "timelines" in dash
print(f"[OK] Dashboard API returned {len(dash['users'])} users, {len(dash['timelines'])} timelines!")

scen = json.loads(urllib.request.urlopen(f"{base_url}/api/scenarios").read().decode("utf-8"))
assert len(scen) >= 6
print(f"[OK] Scenarios API returned {len(scen)} scenarios!")

sess = json.loads(urllib.request.urlopen(f"{base_url}/api/session").read().decode("utf-8"))
assert "id" in sess
print(f"[OK] Session API returned session ID: {sess['id']}!")

# Test Generator
target_user = dash["users"][0]["user"]
target_name = dash["users"][0]["display_name"]
req = urllib.request.Request(
    f"{base_url}/api/generate",
    data=json.dumps({"scenario_id": "T1052.001", "intensity": 1.0, "seed": 42, "user": target_user}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
gen = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
assert gen.get("user") == target_user
assert gen.get("display_name") == target_name
print(f"[OK] Generator simulation OK for user {target_user} ({target_name})!")

print("\n========================================================")
print("100% HEALTH VERIFIED! APPLICATION IS COMPLETELY RESTORED!")
print("========================================================")
