"""Fix timeline strip width containment and change dashed lines to thin solid lines."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update CSS: solid thin cursor and perfectly contained 14-day grid
old_timeline_css = """    /* COMPACT SLEEK TIMELINE STRIP */
    .timeline-strip-wrap{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:6px;padding:4px 2px 2px;border-top:1px solid rgba(255,255,255,.05)}
    .timeline-strip{display:flex;gap:4px;align-items:center}
    .day-cell{width:15px;height:16px;border-radius:3px;background:#182232;border:1px solid #27374e;cursor:pointer;position:relative;transition:all .15s ease}
    .day-cell:hover{transform:scale(1.25);border-color:var(--cyan);box-shadow:0 0 8px rgba(94,234,212,.5);z-index:10}
    .day-cell.active-day{border-color:#ffffff;box-shadow:0 0 10px var(--cyan);transform:scale(1.2);background:#22334a;z-index:9}
    .day-cell.critical{background:#fb7185;border-color:#fda4af}
    .day-cell.high{background:#f59e0b;border-color:#fbbf24}
    .day-cell.medium{background:#3b82f6;border-color:#60a5fa}
    .day-cell.low{background:#0f766e;border-color:#14b8a6}"""

new_timeline_css = """    /* COMPACT SLEEK TIMELINE STRIP (CONTAINED) */
    .timeline-strip-wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:6px;padding:5px 2px 2px;border-top:1px solid rgba(255,255,255,.06);width:100%}
    .timeline-strip{display:grid;grid-template-columns:repeat(14,1fr);gap:4px;flex:1 1 auto;max-width:360px}
    .day-cell{height:14px;border-radius:3px;background:#182232;border:1px solid #27374e;cursor:pointer;position:relative;transition:all .15s ease}
    .day-cell:hover{transform:scale(1.2);border-color:var(--cyan);box-shadow:0 0 8px rgba(94,234,212,.5);z-index:10}
    .day-cell.active-day{border-color:#ffffff;box-shadow:0 0 8px var(--cyan);transform:scale(1.15);background:#22334a;z-index:9}
    .day-cell.critical{background:#fb7185;border-color:#fda4af}
    .day-cell.high{background:#f59e0b;border-color:#fbbf24}
    .day-cell.medium{background:#3b82f6;border-color:#60a5fa}
    .day-cell.low{background:#0f766e;border-color:#14b8a6}"""

content = content.replace(old_timeline_css, new_timeline_css)

# Update cursor to solid line
content = content.replace(
    '.cursor{stroke:#ffffff;stroke-width:1;stroke-dasharray:3 3;opacity:.7;pointer-events:none}',
    '.cursor{stroke:rgba(255,255,255,.75);stroke-width:1;stroke-dasharray:none;pointer-events:none}'
)

# 2. In JavaScript drawRisk, make threshold line a thin solid line
content = content.replace(
    'let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-dasharray="4 4" stroke-width="1.2" opacity="0.85"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;',
    'let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-width="1" opacity="0.8"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;'
)

html_path.write_text(content, encoding="utf-8")
print("Timeline width constrained and lines made solid thin.")
