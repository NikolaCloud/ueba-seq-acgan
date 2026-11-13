"""Verify all referenced DOM IDs in index.html exist in HTML markup."""

import re
from pathlib import Path

html = Path("src/ueba_seq_acgan/web/index.html").read_text(encoding="utf-8")

# Extract all IDs defined in HTML
html_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_-]+)["\']', html))
print(f"Total HTML IDs found in markup: {len(html_ids)}")
print(sorted(html_ids))

# Extract all $('#id') and document.getElementById('id') from JavaScript
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
assert script_match, "No script tag found!"
script = script_match.group(1)

js_query_ids = set(re.findall(r"\$\(['\"]#([a-zA-Z0-9_-]+)['\"]\)", script))
js_get_ids = set(re.findall(r"getElementById\(['\"]([a-zA-Z0-9_-]+)['\"]\)", script))

all_js_ids = js_query_ids.union(js_get_ids)
print(f"\nTotal unique IDs referenced in JavaScript: {len(all_js_ids)}")
print(sorted(all_js_ids))

missing_ids = all_js_ids - html_ids
if missing_ids:
    print(f"\n[WARNING] Found {len(missing_ids)} ID(s) referenced in JS but NOT defined in HTML:")
    for mid in sorted(missing_ids):
        print(f" - #{mid}")
else:
    print("\n[OK] 100% of all JavaScript-referenced IDs exist in HTML markup!")
