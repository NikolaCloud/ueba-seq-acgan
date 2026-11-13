"""Fix scale hit target boundaries to perfectly align with cursor position."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

new_draw_risk_js = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let t = all;
      let w = 720, h = 245, p = 16, graphH = 185;
      let step = (w - 2 * p) / Math.max(t.length - 1, 1);
      
      // Determine active selected day
      let activeIdx = selectedIndex !== undefined && selectedIndex !== null ? selectedIndex : (activeDayIndex !== null ? activeDayIndex : (all.length - 1));
      if(activeIdx < 0 || activeIdx >= all.length) activeIdx = all.length - 1;
      activeDayIndex = activeIdx;
      
      // Compute data point coordinates: X mapped from p to w-p, Y mapped within graphH
      let pts = t.map((d, i) => [
        p + i * step,
        graphH - p - d.risk * (graphH - 2 * p) / 100
      ]);
      
      let th = getActiveThreshold();
      let thY = graphH - p - (th * 100) * (graphH - 2 * p) / 100;
      
      let activeDay = all[activeIdx];
      let activePt = pts[activeIdx];
      let isActiveAlert = (activeDay.risk / 100) >= th;
      
      let grid = [0, 25, 50, 75, 100].map(v => {
        let gy = graphH - p - v * (graphH - 2 * p) / 100;
        return `<line class="gridline" x1="${p}" x2="${w-p}" y1="${gy}" y2="${gy}"/>`;
      }).join('');
      
      let thLine = `<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-width="1" opacity="0.8"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;
      let poly = pts.map(x => x.join(',')).join(' ');
      
      let dots = all.map((d, i) => {
        let isAl = (d.risk / 100) >= th;
        let isSel = (i === activeIdx);
        return `
          <circle class="hitpoint" data-i="${i}" cx="${pts[i][0]}" cy="${pts[i][1]}" r="16"/>
          <circle class="point ${isSel?'active-point':''}" cx="${pts[i][0]}" cy="${pts[i][1]}" r="${isSel?4.5:2.5}" fill="${isSel?'#ffffff':isAl?'var(--red)':'var(--cyan)'}"/>
          ${d.observed_anomaly ? `<circle class="anomaly" cx="${pts[i][0]}" cy="${pts[i][1]}" r="4"/>` : ''}
        `;
      }).join('');

      // Build 14-day Scale Elements with 100% continuous contiguous hit sectors
      let scaleY = 212;
      let scaleTrack = `<line x1="${p}" x2="${w-p}" y1="${scaleY}" y2="${scaleY}" stroke="#1f2d42" stroke-width="2" stroke-linecap="round"/>`;
      
      let scaleElements = all.map((d, i) => {
        let isSel = (i === activeIdx);
        let rCls = riskClass(d.risk);
        let color = rCls==='critical'?'#fb7185':rCls==='high'?'#f59e0b':rCls==='medium'?'#3b82f6':'#0f766e';
        let x = pts[i][0];
        
        // Exact contiguous sector bounds for flawless click hit-testing
        let xLeft = (i === 0) ? (p - step / 2) : (x - step / 2);
        let hitW = step;
        
        return `
          <line class="scale-tick ${isSel?'active':''}" data-day-i="${i}" x1="${x}" x2="${x}" y1="${scaleY-7}" y2="${scaleY+7}" stroke="${color}" stroke-width="${isSel?3.5:2}" stroke-linecap="round"/>
          <rect class="scale-hit" data-day-i="${i}" x="${xLeft}" y="${scaleY-15}" width="${hitW}" height="30" fill="transparent" cursor="pointer"/>
        `;
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
          <polygon class="area" points="${p},${graphH-p} ${poly} ${pts[pts.length-1][0]},${graphH-p}"/>
          <polyline class="risk-line reveal" points="${poly}"/>
          ${dots}
          <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${scaleY+8}"/>
          <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="8" fill="none" stroke="#5eead4" stroke-width="2"/>
          <circle cx="${activePt[0]}" cy="${activePt[1]}" r="4" fill="#ffffff"/>
          <!-- Integrated 14-Day Timeline Scale (Contiguous aligned sectors) -->
          ${scaleTrack}
          ${scaleElements}
        </svg>
        <div class="now ${isActiveAlert?'alert':''}">
          <span class="label">${activeDay.day}:</span>
          <b class="${riskClass(activeDay.risk)}">${activeDay.risk}</b>
          <span class="label">/ 100</span>
        </div>
        <div class="chart-caption">Шкала 14 суток активности субъекта · выберите день для детального анализа</div>
      `;

      function attachDayInteraction(el, i){
        let d = all[i];
        let isAl = (d.risk / 100) >= th;
        let evLabels = data?.event_features || [];
        let devRows = evLabels.slice(0, 4).map((f, fi) => {
          let v = d.values ? d.values[fi] : 0;
          return `<div style="display:flex;justify-content:space-between;gap:8px;font-size:10px;color:#cbd5e1"><span>${f.label}:</span><b>${humanValue(v, f)}</b></div>`;
        }).join('');
        
        let tipHtml = `
          <b>📅 День ${i+1} (${d.day}) · Риск: <span class="${riskClass(d.risk)}">${d.risk}/100</span></b>
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
      $$('#riskChart .scale-hit').forEach(sh => attachDayInteraction(sh, +sh.dataset.dayI));
      $$('#riskChart .scale-tick').forEach(st => attachDayInteraction(st, +st.dataset.dayI));
      bindTermTooltips();
    }"""

content = re.sub(r'let activeDayIndex = null;.*?function attachDayInteraction\(el, i\)\{.*?\$\$\(\'#riskChart \.scale-tick\'\)\.forEach\(st => attachDayInteraction\(st, \+st\.dataset\.dayI\)\);\s*bindTermTooltips\(\);\s*\}', new_draw_risk_js, content, flags=re.DOTALL)

html_path.write_text(content, encoding="utf-8")
print("Contiguous scale click hit sectors applied successfully.")
