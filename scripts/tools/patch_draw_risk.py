"""Patch drawRisk precisely in index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

new_draw_risk = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let w=720, h=215, p=16;
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
        let isAl = (d.risk/100) >= th;
        let rCls = riskClass(d.risk);
        let isSel = (i === activeIdx);
        return `<div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" title="${d.day}"><i></i></div>`;
      }).join('');
      
      $('#riskChart').innerHTML = `
        <svg viewBox="0 0 ${w} ${h}">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#5eead4" stop-opacity="0.38"/>
              <stop offset="100%" stop-color="#5eead4" stop-opacity="0"/>
            </linearGradient>
          </defs>
          ${grid}
          ${thLine}
          <polygon class="area" points="${p},${h-p} ${poly} ${pts[pts.length-1][0]},${h-p}"/>
          <polyline class="risk-line reveal" points="${poly}"/>
          ${dots}
          <!-- Interactive cursor line at the exact clicked/selected day -->
          <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${h-p}"/>
          <!-- Highlight selection ring around active point -->
          <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="7" fill="none" stroke="#5eead4" stroke-width="2"/>
        </svg>
        <div class="now ${isActiveAlert?'alert':''}">
          <span class="label">Выбранный день: ${activeDay.day}</span>
          <b class="${riskClass(activeDay.risk)}">${activeDay.risk}</b>
          <span class="label"> / 100</span>
        </div>
        <div style="padding:0 8px 6px">
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted);margin-bottom:2px">
            <span class="term-tip" data-term="Окно активности">Интерактивная лента активности субъекта (14 дней): <i>ℹ</i></span>
            <span style="font-size:10px;color:var(--cyan)">Кликните на точку/день для детального среза</span>
          </div>
          <div class="timeline-strip" id="timelineStrip">${dayCells}</div>
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

content = re.sub(r'function drawRisk\(all,upto\)\{.*?(?=\n    function addFeed|\n    function points)', new_draw_risk, content, flags=re.DOTALL)

html_path.write_text(content, encoding="utf-8")
print("drawRisk patched successfully.")
