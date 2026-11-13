"""Ensure only 1 clean style tag in index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# Find all style tags
styles = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
print(f"Original style tags count: {len(styles)}")

# Take the first clean style
primary_style = styles[0]

# Remove all style tags from content
content_no_styles = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)

# Insert the single clean style back inside <head>
content_clean = content_no_styles.replace('</head>', f'  <style>{primary_style}</style>\n</head>')

html_path.write_text(content_clean, encoding="utf-8")

# Verify
new_styles = re.findall(r'<style>.*?</style>', content_clean, re.DOTALL)
print(f"New style tags count: {len(new_styles)}")
print(f"Clean HTML size: {len(content_clean)} bytes")
