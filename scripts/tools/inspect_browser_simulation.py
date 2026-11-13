"""Simulate the browser initialization steps of index.html in detail."""

import json
import re
import urllib.request
from pathlib import Path

html = Path("src/ueba_seq_acgan/web/index.html").read_text(encoding="utf-8")
script = re.search(r"<script>(.*?)</script>", html, re.DOTALL).group(1)

# Fetch dashboard data like the browser does
base = "http://127.0.0.1:8765"
d = json.loads(urllib.request.urlopen(f"{base}/api/dashboard").read().decode("utf-8"))
s = json.loads(urllib.request.urlopen(f"{base}/api/scenarios").read().decode("utf-8"))
session = json.loads(urllib.request.urlopen(f"{base}/api/session").read().decode("utf-8"))

print("Data loaded successfully from API.")
print("Summary keys:", list(d["summary"].keys()))
print("Population keys:", list(d["population"].keys()))
print("Users count:", len(d["users"]))
print("Event features count:", len(d.get("event_features", [])))
print("Timelines count:", len(d.get("timelines", {})))

# Check the initial execution sequence in .then(([d,s,session]) => { ... })
# Line by line check:
# 1. renderCards(d.summary)
# 2. renderPopulation(d.population)
# 3. renderUsers(initial)
# 4. scenarioInfo()
# 5. updateSOCSimulator()
# 6. renderAugmentation()
# 7. renderHistory()

# Let's check renderPopulation in index.html:
pop_match = re.search(r"function renderPopulation\(p\)\{(.*?)\n    function renderUserRows", script, re.DOTALL)
if pop_match:
    print("\nrenderPopulation body length:", len(pop_match.group(1)))
    # Check if there are any references in renderPopulation that might fail:
    print("renderPopulation lines:")
    print(pop_match.group(1)[:400])

# Let's check renderArch in index.html:
arch_match = re.search(r"function archContent\(key\)\{(.*?)\n    function renderArch", script, re.DOTALL)
if arch_match:
    print("\narchContent body length:", len(arch_match.group(1)))

# Let's check if there are any syntax errors or bad replacements:
for func_name in ['renderCards', 'renderPopulation', 'renderUsers', 'selectUser', 'renderEventDetail', 'drawRisk', 'exportCase', 'archContent']:
    assert f"function {func_name}" in script, f"ERROR: function {func_name} is missing from script!"
    print(f"[OK] function {func_name} is present.")
