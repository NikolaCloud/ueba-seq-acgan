"""Update chart to larger size and place timeline scale directly under chart with centered label."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update CSS: larger chart SVG height (240px) and scale styling
old_scale_css = """    /* COMPACT SLEEK TIMELINE STRIP (CONTAINED) */
    .timeline-strip-wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:6px;padding:5px 2px 2px;border-top:1px solid rgba(255,255,255,.06);width:100%}
    .timeline-strip{display:grid;grid-template-columns:repeat(14,1fr);gap:4px;flex:1 1 auto;max-width:360px}
    .day-cell{height:14px;border-radius:3px;background:#182232;border:1px solid #27374e;cursor:pointer;position:relative;transition:all .15s ease}
    .day-cell:hover{transform:scale(1.2);border-color:var(--cyan);box-shadow:0 0 8px rgba(94,234,212,.5);z-index:10}
    .day-cell.active-day{border-color:#ffffff;box-shadow:0 0 8px var(--cyan);transform:scale(1.15);background:#22334a;z-index:9}
    .day-cell.critical{background:#fb7185;border-color:#fda4af}
    .day-cell.high{background:#f59e0b;border-color:#fbbf24}
    .day-cell.medium{background:#3b82f6;border-color:#60a5fa}
    .day-cell.low{background:#0f766e;border-color:#14b8a6}"""

new_scale_css = """    /* TIMELINE SCALE DIRECTLY UNDER CHART (ALIGNED) */
    .timeline-scale-wrap{padding:8px 16px 4px;width:100%;box-sizing:border-box}
    .timeline-scale-grid{display:grid;grid-template-columns:repeat(14,1fr);gap:4px;width:100%}
    .day-cell{height:14px;border-radius:3px;background:#182232;border:1px solid #27374e;cursor:pointer;position:relative;transition:all .15s ease}
    .day-cell:hover{transform:scale(1.2);border-color:var(--cyan);box-shadow:0 0 8px rgba(94,234,212,.5);z-index:10}
    .day-cell.active-day{border-color:#ffffff;box-shadow:0 0 8px var(--cyan);transform:scale(1.15);background:#22334a;z-index:9}
    .day-cell.critical{background:#fb7185;border-color:#fda4af}
    .day-cell.high{background:#f59e0b;border-color:#fbbf24}
    .day-cell.medium{background:#3b82f6;border-color:#60a5fa}
    .day-cell.low{background:#0f766e;border-color:#14b8a6}
    .timeline-scale-label{text-align:center;font-size:11px;color:var(--muted);margin-top:6px}"""

content = content.replace(old_scale_css, new_scale_css)

# Update .chart svg height from 190px to 240px
content = content.replace('.chart svg{width:100%;height:190px;overflow:visible;display:block}', '.chart svg{width:100%;height:240px;overflow:visible;display:block}')

# 2. Update JavaScript drawRisk
old_draw_risk = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let t = all;
      let w = 720, h = 190, p = 16;
      let pts = points(t, w, h, p);
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
      let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-width="1" opacity="0.8"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;
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
        return `<div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" tabindex="0" title="${d.day} · Риск ${d.risk}/100"></div>`;
      }).join('');
      
      $('#riskChart').innerHTML = `
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
          <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${h-p}"/>
          <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="8" fill="none" stroke="#5eead4" stroke-width="2"/>
          <circle cx="${activePt[0]}" cy="${activePt[1]}" r="4" fill="#ffffff"/>
        </svg>
        <div class="now ${isActiveAlert?'alert':''}">
          <span class="label">${activeDay.day}:</span>
          <b class="${riskClass(activeDay.risk)}">${activeDay.risk}</b>
          <span class="label">/ 100</span>
        </div>
        <div class="timeline-strip-wrap">
          <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)">
            <span class="term-tip" data-term="Окно активности">Лента 14 дней: <i>ℹ</i></span>
          </div>
          <div class="timeline-strip" id="timelineStrip">${dayCells}</div>
        </div>
      `;"""

new_draw_risk = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let t = all;
      let w = 720, h = 240, p = 16;
      let pts = points(t, w, h, p);
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
      let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-width="1" opacity="0.8"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;
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
        return `<div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" tabindex="0" title="${d.day} · Риск ${d.risk}/100"></div>`;
      }).join('');
      
      $('#riskChart').innerHTML = `
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
          <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${h-p}"/>
          <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="8" fill="none" stroke="#5eead4" stroke-width="2"/>
          <circle cx="${activePt[0]}" cy="${activePt[1]}" r="4" fill="#ffffff"/>
        </svg>
        <div class="now ${isActiveAlert?'alert':''}">
          <span class="label">${activeDay.day}:</span>
          <b class="${riskClass(activeDay.risk)}">${activeDay.risk}</b>
          <span class="label">/ 100</span>
        </div>
        <div class="timeline-scale-wrap">
          <div class="timeline-scale-grid" id="timelineStrip">${dayCells}</div>
          <div class="timeline-scale-label">Шкала 14 суток активности субъекта · выберите день для детального анализа</div>
        </div>
      `;"""

content = content.replace(old_draw_risk, new_draw_risk)

html_path.write_text(content, encoding="utf-8")
print("Chart enlarged and timeline scale positioned strictly under graph.")
