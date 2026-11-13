"""Script to inject all UI/UX improvements into src/ueba_seq_acgan/web/index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Add Favicon in <head>
if '<link rel="icon"' not in content:
    content = content.replace(
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n  <link rel="icon" type="image/png" href="icon.png">\n  <link rel="shortcut icon" href="icon.ico">'
    )

# 2. Add Enhanced CSS for Term Tooltips, SOC Simulator, Animated Architecture, Timeline tooltips
extra_css = """
    /* TERM TOOLTIPS */
    .term-tip{border-bottom:1px dashed rgba(94,234,212,.6);cursor:help;display:inline-flex;align-items:center;gap:2px;transition:color .15s}
    .term-tip:hover{color:var(--cyan);border-bottom-color:var(--cyan)}
    .term-tip i{font-style:normal;font-size:9px;background:#1e293b;color:var(--cyan);border-radius:3px;padding:0 3px;margin-left:2px}

    /* TIMELINE DAY CELLS */
    .timeline-strip{display:flex;gap:3px;align-items:center;overflow-x:auto;padding:8px 0;margin:6px 0}
    .day-cell{width:18px;height:24px;border-radius:3px;background:#1b2636;border:1px solid #28374d;cursor:pointer;position:relative;transition:all .18s ease;display:flex;align-items:flex-end;justify-content:center;font-size:8px;color:#cbd5e1;padding-bottom:1px}
    .day-cell:hover{transform:translateY(-3px) scale(1.15);z-index:10;box-shadow:0 4px 14px rgba(94,234,212,.4);border-color:var(--cyan)}
    .day-cell.active-day{border-color:#fff;box-shadow:0 0 10px var(--cyan);transform:translateY(-2px)}
    .day-cell.critical{background:linear-gradient(to top,#fb7185 85%,#fda4af);border-color:#fb7185}
    .day-cell.high{background:linear-gradient(to top,#f59e0b 70%,#fbbf24);border-color:#f59e0b}
    .day-cell.medium{background:linear-gradient(to top,#3b82f6 50%,#60a5fa);border-color:#3b82f6}
    .day-cell.low{background:linear-gradient(to top,#0f766e 30%,#14b8a6);border-color:#0f766e}

    /* ANIMATED ARCHITECTURE FLOW */
    .arch-flow{display:grid;grid-template-columns:repeat(5,1fr);align-items:center;gap:16px;margin:20px 0 16px;position:relative}
    .arch-flow-track{position:absolute;left:40px;right:40px;top:50%;height:3px;background:#162438;z-index:0}
    .arch-pulse-beam{position:absolute;left:0;top:0;height:100%;width:35%;background:linear-gradient(90deg,transparent,#38bdf8,#2dd4bf,transparent);animation:pulseFlow 2.8s linear infinite}
    @keyframes pulseFlow{0%{left:-35%}100%{left:100%}}
    .arch-node{min-height:96px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:#0d131d;cursor:pointer;position:relative;z-index:1;transition:all .22s cubic-bezier(0.4,0,0.2,1)}
    .arch-node:hover{border-color:var(--cyan);transform:translateY(-4px);box-shadow:0 10px 30px rgba(56,189,248,.25)}
    .arch-node.active{border-color:var(--cyan);background:linear-gradient(145deg,#12253b,#0b1524);box-shadow:0 0 25px rgba(56,189,248,.35);transform:translateY(-2px)}
    .arch-node[data-arch=gan]{border-color:#7c3aed55;background:#1b122e}
    .arch-node[data-arch=gan].active{border-color:#c084fc;box-shadow:0 0 25px rgba(192,132,252,.35)}
    .arch-badge-tag{font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;display:inline-block;margin-top:4px}
    .arch-badge-cyan{background:rgba(56,189,248,.15);color:#38bdf8;border:1px solid rgba(56,189,248,.3)}
    .arch-badge-purple{background:rgba(192,132,252,.15);color:#c084fc;border:1px solid rgba(192,132,252,.3)}
    .arch-badge-green{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3)}

    /* SOC SIMULATOR CARD */
    .soc-calc-card{background:linear-gradient(145deg,#0e1a2b,#09121d);border:1px solid #283d5a;border-radius:13px;padding:18px;margin-top:14px;box-shadow:0 16px 40px rgba(0,0,0,.45)}
    .soc-calc-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:20px;margin-top:14px;align-items:center}
    .soc-calc-controls{display:grid;gap:14px}
    .soc-calc-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
    .soc-stat-box{background:#0a111a;border:1px solid #203047;border-radius:9px;padding:10px 14px}
    .soc-stat-box .label{font-size:11px;color:var(--muted)}
    .soc-stat-box .val{font-size:22px;font-weight:800;margin-top:2px;font-variant-numeric:tabular-nums}
    .soc-stat-box .desc{font-size:10px;color:var(--muted);margin-top:2px}
    .soc-status-badge{padding:8px 12px;border-radius:8px;font-size:12px;font-weight:700;display:flex;align-items:center;gap:8px;grid-column:1/-1}
    .soc-status-badge.ok{background:rgba(34,197,94,.12);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
    .soc-status-badge.warn{background:rgba(251,191,36,.12);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
    .soc-status-badge.danger{background:rgba(251,113,133,.12);color:#fb7185;border:1px solid rgba(251,113,133,.3)}

    /* QUICK USER ACTION BUTTONS IN GENERATOR */
    .user-select-bar{display:flex;gap:6px;margin-bottom:6px}
    .user-select-btn{flex:1;padding:5px 8px;font-size:11px;background:#142233;border:1px solid #2a3c54;color:var(--muted);border-radius:6px;cursor:pointer;transition:.15s}
    .user-select-btn:hover{color:var(--cyan);border-color:var(--cyan)}
"""

if '/* TERM TOOLTIPS */' not in content:
    content = content.replace('/* THRESHOLD CONTROL BAR */', extra_css + '\n    /* THRESHOLD CONTROL BAR */')

html_path.write_text(content, encoding="utf-8")
print("CSS updates injected.")
