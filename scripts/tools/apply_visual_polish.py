"""Apply visual polish for modal close button, term-tips inline display, and spacious risk chart."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Clean and fix CSS
# Fix .modal-close button centering
content = content.replace(
    '.modal-close{width:32px;height:32px;border-radius:8px;border:1px solid #334158;background:#172234;color:var(--text);font-size:18px;display:grid;place-items:center;cursor:pointer;transition:.15s}',
    '.modal-close{width:32px;height:32px;border-radius:8px;border:1px solid #334158;background:#172234;color:var(--text);font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;transition:.15s}'
)

# Fix .term-tip to prevent text overlay / breakages in headers and tables
term_tip_css = """
    /* TERM TOOLTIPS - CLEAN INLINE TEXT FLOW */
    .term-tip{display:inline;border-bottom:1px dashed rgba(94,234,212,.6);cursor:help;white-space:normal;transition:color .15s,border-color .15s}
    .term-tip:hover{color:var(--cyan);border-bottom-color:var(--cyan)}
    .term-tip i{font-style:normal;font-size:9px;background:#1e293b;color:var(--cyan);border-radius:3px;padding:1px 4px;margin-left:3px;vertical-align:1px;display:inline-block;line-height:1.2}
"""

content = re.sub(r'/\* TERM TOOLTIPS \*/.*?/\* TIMELINE DAY CELLS \*/', term_tip_css + '\n    /* TIMELINE DAY CELLS */', content, flags=re.DOTALL)

# Fix chart layout CSS
chart_layout_css = """
    /* CLEAN SPACIOUS RISK CHART & TIMELINE GRID */
    .chart{height:auto;min-height:300px;padding:14px 16px;display:flex;flex-direction:column;gap:8px;position:relative}
    .chart-top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:8px}
    .chart-active-badge{display:flex;align-items:center;gap:8px;background:#0d1420;border:1px solid #203046;padding:4px 10px;border-radius:8px;font-size:12px}
    .chart-active-badge .score-val{font-size:15px;font-weight:800;color:var(--cyan);font-variant-numeric:tabular-nums}
    .chart-active-badge.alert{border-color:rgba(251,113,133,.4);background:rgba(251,113,133,.08)}
    .chart-active-badge.alert .score-val{color:var(--red)}
    .chart-svg-wrap{position:relative;width:100%;height:180px}
    .chart-svg-wrap svg{width:100%;height:100%;overflow:visible}
    .chart-bottom-strip{margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,.06)}
    .timeline-strip-grid{display:grid;grid-template-columns:repeat(14,1fr);gap:5px;margin-top:6px}
    .day-cell{height:32px;border-radius:6px;background:#131c2a;border:1px solid #223247;cursor:pointer;position:relative;transition:all .18s ease;display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:3px 2px;font-size:9px;color:#94a3b8}
    .day-cell .day-num{font-size:8px;opacity:.7}
    .day-cell .day-score{font-size:9px;font-weight:700}
    .day-cell:hover{transform:translateY(-2px);border-color:var(--cyan);box-shadow:0 4px 12px rgba(56,189,248,.3);color:#fff;z-index:5}
    .day-cell.active-day{border-color:#fff;box-shadow:0 0 14px rgba(56,189,248,.5);background:#1a283c;color:#fff;transform:translateY(-2px)}
    .day-cell.critical .day-score{color:var(--red)}
    .day-cell.high .day-score{color:var(--amber)}
    .day-cell.medium .day-score{color:var(--blue)}
    .day-cell.low .day-score{color:var(--cyan)}
"""

if '/* CLEAN SPACIOUS RISK CHART & TIMELINE GRID */' not in content:
    content = content.replace('/* TIMELINE DAY CELLS */', chart_layout_css + '\n    /* TIMELINE DAY CELLS */')

# 2. Update drawRisk in JavaScript
new_draw_risk_js = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let w=720, h=180, p=16;
      let pts = points(all, w, h, p);
      let th = getActiveThreshold();
      let thY = h - p - (th * 100) * (h - 2*p) / 100;
      
      // Determine active selected day
      let activeIdx = selectedIndex !== undefined && selectedIndex !== null ? selectedIndex : (activeDayIndex !== null ? activeDayIndex : (all.length - 1));
      if(activeIdx < 0 || activeIdx >= all.length) activeIdx = all.length - 1;
      activeDayIndex = activeIdx;
      
      let activeDay = all[activeIdx];
      let activePt = pts[activeIdx];
      let isActiveAlert = (activeDay.risk / 100) >= th;
      
      let grid = [0,25,50,75,100].map(v=>`<line class="gridline" x1="${p}" x2="${w-p}" y1="${h-p-v*(h-2*p)/100}" y2="${h-p-v*(h-2*p)/100}"/>`).join('');
      let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-dasharray="4 4" stroke-width="1.2" opacity="0.85"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;
      let poly = pts.map(x=>x.join(',')).join(' ');
      
      let dots = all.map((d,i)=>{
        let isAl = (d.risk/100) >= th;
        let isSel = (i === activeIdx);
        return `
          <circle class="hitpoint" data-i="${i}" cx="${pts[i][0]}" cy="${pts[i][1]}" r="12"/>
          <circle class="point ${isSel?'active-point':''}" cx="${pts[i][0]}" cy="${pts[i][1]}" r="${isSel?4.5:2.5}" fill="${isSel?'#ffffff':isAl?'var(--red)':'var(--cyan)'}"/>
          ${d.observed_anomaly?`<circle class="anomaly" cx="${pts[i][0]}" cy="${pts[i][1]}" r="4"/>`:''}
        `;
      }).join('');

      let dayCells = all.map((d, i) => {
        let isAl = (d.risk / 100) >= th;
        let rCls = riskClass(d.risk);
        let isSel = (i === activeIdx);
        return `
          <div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" tabindex="0" title="${d.day}">
            <span class="day-num">д.${i+1}</span>
            <span class="day-score">${d.risk}</span>
          </div>
        `;
      }).join('');
      
      $('#riskChart').innerHTML = `
        <div class="chart-top-bar">
          <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)">
            <span>Шкала риска: <b>0 – 100%</b></span>
            <span>·</span>
            <span style="color:#fb7185">Порог отсечки: <b>${Math.round(th*100)}%</b></span>
          </div>
          <div class="chart-active-badge ${isActiveAlert?'alert':''}">
            <span class="label">Выбранный день: <b>${activeDay.day}</b></span>
            <span>·</span>
            <span class="label">Оценка:</span>
            <span class="score-val ${riskClass(activeDay.risk)}">${activeDay.risk}/100</span>
          </div>
        </div>
        <div class="chart-svg-wrap">
          <svg viewBox="0 0 ${w} ${h}">
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#5eead4" stop-opacity="0.32"/>
                <stop offset="100%" stop-color="#5eead4" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            ${grid}
            ${thLine}
            <polygon class="area" points="${p},${h-p} ${poly} ${pts[pts.length-1][0]},${h-p}"/>
            <polyline class="risk-line reveal" points="${poly}"/>
            ${dots}
            <!-- Vertical cursor line at selected point -->
            <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${h-p}"/>
            <!-- Outer glowing pulse ring -->
            <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="8" fill="none" stroke="#5eead4" stroke-width="2"/>
            <!-- Inner bright dot -->
            <circle cx="${activePt[0]}" cy="${activePt[1]}" r="4" fill="#ffffff"/>
          </svg>
        </div>
        <div class="chart-bottom-strip">
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted)">
            <span class="term-tip" data-term="Окно активности">Лента 14 суток активности субъекта: <i>ℹ</i></span>
            <span style="font-size:10px;color:var(--cyan)">Кликните на день для выбора</span>
          </div>
          <div class="timeline-strip-grid" id="timelineStrip">${dayCells}</div>
        </div>
      `;

      function attachDayInteraction(el, i){
        let d = all[i];
        let isAl = (d.risk/100) >= th;
        let evLabels = data?.event_features || [];
        let devRows = evLabels.slice(0, 4).map((f, fi) => {
          let v = d.values ? d.values[fi] : 0;
          return `<div style="display:flex;justify-content:space-between;gap:8px;font-size:10px;color:#cbd5e1"><span>${f.label}:</span><b>${humanValue(v, f)}</b></div>`;
        }).join('');
        
        let tipHtml = `
          <b>📅 ${d.day} · Риск: <span class="${riskClass(d.risk)}">${d.risk}/100</span></b>
          <div style="font-size:11px;margin:3px 0;font-weight:600;color:${isAl?'#fb7185':'#34d399'}">
            ${isAl?'🚨 Превышение порога риска':'✅ Поведение в пределах нормы'}
          </div>
          <div style="border-top:1px solid rgba(255,255,255,.1);margin:4px 0 2px;padding-top:4px">
            ${devRows}
          </div>
          <span style="font-size:9px;color:var(--cyan);margin-top:2px;display:block">Кликните для выбора этой даты</span>
        `;
        el.onmouseenter = e => showTip(e, tipHtml);
        el.onmousemove = e => showTip(e, tipHtml);
        el.onmouseleave = hideTip;
        el.onclick = () => {
          activeDayIndex = i;
          drawRisk(all, i);
          renderEventDetail(all[i], i, all);
          addFeed(isAl?'ОПОВЕЩЕНИЕ':'СОБЫТИЕ',`${data.users[selected].display_name} · ${d.day} · риск ${d.risk}`,isAl?'red':'');
          saveState();
        };
      }

      $$('#riskChart .hitpoint').forEach(pt => attachDayInteraction(pt, +pt.dataset.i));
      $$('#riskChart .day-cell').forEach(dc => attachDayInteraction(dc, +dc.dataset.dayI));
      bindTermTooltips();
    }"""

content = re.sub(r'let activeDayIndex = null;.*?function attachDayInteraction\(el, i\)\{.*?\$\$\(\'#riskChart \.day-cell\'\)\.forEach\(dc => attachDayInteraction\(dc, \+dc\.dataset\.dayI\)\);\s*bindTermTooltips\(\);\s*\}', new_draw_risk_js, content, flags=re.DOTALL)

html_path.write_text(content, encoding="utf-8")
print("Visual polish applied successfully.")
