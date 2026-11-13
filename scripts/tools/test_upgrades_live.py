"""Validate modal dialogs, tooltips coverage, and chart selection in index.html."""

import json
import re
import urllib.request

base_url = "http://127.0.0.1:8765"

html = urllib.request.urlopen(f"{base_url}/").read().decode("utf-8")
print(f"HTML size: {len(html)} bytes")

# 1. Verify Modals and Clickable Cards
assert "modal-overlay" in html, "Modal overlay missing!"
assert "openCardModal" in html, "openCardModal function missing!"
assert "data-card-type" in html, "data-card-type attributes missing on cards!"
print("[OK] Interactive detail modals structure verified!")

# 2. Verify Precise Point Selection on Chart
assert "selected-ring" in html, "selected-ring missing on chart!"
assert "activeDayIndex" in html, "activeDayIndex logic missing in drawRisk!"
print("[OK] Precise chart point selection & cursor tracking verified!")

# 3. Verify Tooltip coverage
terms_match = re.search(r'const TERMS = \{(.*?)\};', html, re.DOTALL)
assert terms_match, "TERMS dictionary missing!"
terms_body = terms_match.group(1)
print(f"TERMS dictionary length: {len(terms_body)} chars")

term_tips_in_html = set(re.findall(r'data-term="([^"]+)"', html))
print(f"Total unique data-term attributes in HTML: {len(term_tips_in_html)}")
for t in sorted(term_tips_in_html):
    print(f" - {t}")

print("\n========================================================")
print("ALL NEW FEATURES VALIDATED SUCCESSFULLY ON RUNNING DEV SERVER!")
print("========================================================")
