"""Make risk line between data points solid and thin."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update CSS for .risk-line
content = re.sub(
    r'\.risk-line\{.*?\}\s*\.risk-line\.reveal\{.*?\}',
    '.risk-line{fill:none;stroke:var(--cyan);stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:none;filter:drop-shadow(0 0 3px rgba(94,234,212,.35))}',
    content
)

# 2. In SVG drawRisk, change <polyline class="risk-line reveal" to <polyline class="risk-line"
content = content.replace('<polyline class="risk-line reveal"', '<polyline class="risk-line"')

html_path.write_text(content, encoding="utf-8")
print("Risk line between points made solid and thin.")
