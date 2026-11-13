"""Debug why application broke."""

import json
import re
import urllib.request
from pathlib import Path

html = Path("src/ueba_seq_acgan/web/index.html").read_text(encoding="utf-8")
script_match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
assert script_match, "No script tag found!"
script = script_match.group(1)

print(f"HTML size: {len(html)} bytes")
print(f"Script size: {len(script)} bytes")
print(f"Braces: {{ = {script.count('{')}, }} = {script.count('}')}")
print(f"Parens: ( = {script.count('(')}, ) = {script.count(')')}")
print(f"Brackets: [ = {script.count('[')}, ] = {script.count(']')}")

# Check all IDs in HTML markup
html_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_-]+)["\']', html))

# Find all $('#id') and document.getElementById('id') from JavaScript
js_query_ids = set(re.findall(r"\$\(['\"]#([a-zA-Z0-9_-]+)['\"]\)", script))
js_get_ids = set(re.findall(r"getElementById\(['\"]([a-zA-Z0-9_-]+)['\"]\)", script))
all_js_ids = js_query_ids.union(js_get_ids)

missing_ids = all_js_ids - html_ids
print("\nMissing IDs referenced in JS but not in HTML:")
for mid in sorted(missing_ids):
    print(" -", mid)
