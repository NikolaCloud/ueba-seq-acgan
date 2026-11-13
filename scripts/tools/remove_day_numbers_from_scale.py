"""Remove day number labels from the scale."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# Remove scale day text element from drawRisk
old_scale_elem = """        return `
          <line class="scale-tick ${isSel?'active':''}" data-day-i="${i}" x1="${x}" x2="${x}" y1="${scaleY-6}" y2="${scaleY+6}" stroke="${color}" stroke-width="${isSel?3.5:2}" stroke-linecap="round"/>
          <text class="scale-day-text ${isSel?'active':''}" x="${x}" y="${scaleY+18}" text-anchor="middle" fill="${isSel?'#5eead4':'#64748b'}" font-size="9.5">${i+1}</text>
          <rect class="scale-hit" data-day-i="${i}" x="${x-18}" y="${scaleY-12}" width="36" height="34" fill="transparent" cursor="pointer"/>
        `;"""

new_scale_elem = """        return `
          <line class="scale-tick ${isSel?'active':''}" data-day-i="${i}" x1="${x}" x2="${x}" y1="${scaleY-6}" y2="${scaleY+6}" stroke="${color}" stroke-width="${isSel?3.5:2}" stroke-linecap="round"/>
          <rect class="scale-hit" data-day-i="${i}" x="${x-18}" y="${scaleY-12}" width="36" height="24" fill="transparent" cursor="pointer"/>
        `;"""

content = content.replace(old_scale_elem, new_scale_elem)

html_path.write_text(content, encoding="utf-8")
print("Day number labels removed from scale successfully.")
