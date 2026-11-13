"""Restore points, humanValue, riskSpark, renderEventDetail."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

functions_code = """
    function points(values,w,h,p){return values.map((d,i)=>[p+i*(w-2*p)/Math.max(values.length-1,1),h-p-d.risk*(h-2*p)/100])}

    function humanValue(v,feature){
      if(!feature) return String(Math.round(v||0));
      if(feature.key==='email_size')return v>=1048576?`${(v/1048576).toFixed(2)} МБ`:v>=1024?`${(v/1024).toFixed(1)} КБ`:`${fmt(Math.round(v))} байт`;
      return `${fmt(Math.round(v))} ${feature.unit||''}`;
    }

    function riskSpark(timeline,index){
      let from=Math.max(0,index-13),slice=timeline.slice(from,index+1),w=210,h=54,p=4;
      let pts=slice.map((d,i)=>[p+i*(w-2*p)/Math.max(slice.length-1,1),h-p-d.risk*(h-2*p)/100]);
      let th=getActiveThreshold();
      let thY = h - p - (th * 100) * (h - 2*p) / 100;
      let cur = pts[pts.length-1];
      
      return `
        <svg class="event-spark" viewBox="0 0 ${w} ${h}">
          <defs>
            <linearGradient id="corridorGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.16"/>
              <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.02"/>
            </linearGradient>
          </defs>
          <rect x="${p}" y="${h-p-25*(h-2*p)/100}" width="${w-2*p}" height="${25*(h-2*p)/100}" fill="url(#corridorGrad)" rx="3"/>
          <line class="gridline" x1="0" x2="${w}" y1="${h-4}" y2="${h-4}"/>
          <line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-dasharray="2 2" stroke-width="1" opacity="0.6"/>
          <polyline points="${pts.map(x=>x.join(',')).join(' ')}" stroke="var(--blue)" stroke-width="1.8" fill="none"/>
          <circle cx="${cur[0]}" cy="${cur[1]}" r="4" fill="${slice.at(-1).risk>=th*100?'var(--red)':'var(--cyan)'}" filter="drop-shadow(0 0 4px ${slice.at(-1).risk>=th*100?'var(--red)':'var(--cyan)'})"/>
        </svg>
      `;
    }

    function renderEventDetail(d,index,timeline){
      if(!d?.values)return;
      currentEvent={d,index,timeline,user:data.users[selected]};
      let th=getActiveThreshold();
      let isAlert = (d.risk/100) >= th;
      let features=data.event_features || [];
      
      // Calculate standard deviation across timeline for confidence intervals
      let rows=features.map((f,i)=>{
        let value=d.values[i];
        let mean=d.window_mean ? d.window_mean[i] : value;
        
        let allVals = timeline.map(t => (t.values ? t.values[i] : mean));
        let variance = allVals.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / Math.max(allVals.length, 1);
        let std = Math.sqrt(variance);
        let zScore = (value - mean) / (std + 1.0);
        let corridorHigh = Math.max(0, mean + 2 * std);
        let delta=100*(value-mean)/Math.max(Math.abs(mean),1);
        let hot = Math.abs(zScore) >= 2.0 || (Math.abs(delta) >= 100 && value > 0);
        
        return {f, value, mean, std, zScore, corridorHigh, delta, hot};
      }).sort((a,b)=>Math.abs(b.zScore)-Math.abs(a.zScore));
      
      let eventCount=d.values.reduce((sum,v,i)=>sum+(i===8||i===14?0:v),0);
      let status=isAlert?'🚨 ОПОВЕЩЕНИЕ ДЕТЕКТОРА':d.observed_anomaly?'⚠️ ИНЦИДЕНТ CERT':'✅ ПОВЕДЕНИЕ В НОРМЕ';
      
      $('#eventDetail').innerHTML=`
        <div class="panel-title event-head">
          <div>
            <div class="eyebrow">Поведенческий срез CERT · ${d.day}</div>
            <h2>${data.users[selected].display_name} · параметры события</h2>
          </div>
          <span class="badge ${isAlert||d.observed_anomaly?'red':'green'}">${status}</span>
        </div>
        <div class="event-body">
          <div class="event-summary">
            <div class="event-state ${isAlert?'alert':''}">
              <span class="label">Оценка риска</span>
              <b class="${riskClass(d.risk)}">${d.risk}/100</b>
              <span class="label">Порог срабатывания: ${Math.round(th*100)}/100</span>
            </div>
            <div class="event-state">
              <span class="label">Событий за сутки</span>
              <b>${fmt(Math.round(eventCount))}</b>
              <span class="label">по контролируемым каналам</span>
            </div>
            <div class="event-state">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
                <span class="label">Динамика 14 суток</span>
                <span class="term-tip" data-term="Z-Score" style="font-size:10px">Коридор ±2σ<i>ℹ</i></span>
              </div>
              ${riskSpark(timeline,index)}
            </div>
          </div>
          <div>
            <table class="feature-table">
              <thead>
                <tr>
                  <th>Показатель</th>
                  <th>За сутки</th>
                  <th>Коридор нормы (μ±2σ)</th>
                  <th>Отклонение (Z-Score)</th>
                </tr>
              </thead>
              <tbody>
                ${rows.map(x=>{
                  let zFormatted = (x.zScore >= 0 ? '+' : '') + x.zScore.toFixed(2) + 'σ';
                  let zColor = Math.abs(x.zScore) >= 3.0 ? 'critical' : Math.abs(x.zScore) >= 1.5 ? 'high' : 'low';
                  let barWidth = Math.min(100, Math.abs(x.zScore) * 25);
                  return `<tr class="${x.hot?'hot':''}">
                    <td><b>${x.f.label}</b><br><span class="employee-id">${x.f.key}</span></td>
                    <td><b>${humanValue(x.value,x.f)}</b></td>
                    <td style="color:#94a3b8">0 – ${humanValue(x.corridorHigh,x.f)}</td>
                    <td>
                      <span class="${zColor}" style="font-weight:700">${zFormatted}</span>
                      <div class="deviation"><i style="width:${barWidth}%;background:${Math.abs(x.zScore)>=3?'var(--red)':Math.abs(x.zScore)>=1.5?'var(--amber)':'var(--cyan)'}"></i></div>
                    </td>
                  </tr>`;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>
        <div class="raw-note">Источник: фактические суточные агрегаты скользящего окна CERT с расчётом доверительного интервала μ±2σ.</div>
        <div id="caseControls"></div>
      `;
      renderCaseControls();
      bindTermTooltips();
    }
"""

if 'function renderEventDetail' not in content:
    content = content.replace('function selectUser(i,clearFeed=true){', functions_code + '\n\n    function selectUser(i,clearFeed=true){')

html_path.write_text(content, encoding="utf-8")
print("Restored points, humanValue, riskSpark, renderEventDetail.")
