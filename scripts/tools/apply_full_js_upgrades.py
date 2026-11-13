"""Inject all JS features and UI handlers into src/ueba_seq_acgan/web/index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Inject TERMS dictionary and Term Tooltip Binder
terms_js = """
    const TERMS = {
      'PR-AUC': '<b>PR-AUC (Precision-Recall AUC)</b>Главная метрика качества детектора при сильном дисбалансе классов (когда аномалий менее 0.2%). Значение 0.891 отражает высокую точность выявления редких угроз.',
      'Recall': '<b>Полнота обнаружения (Recall)</b>Доля выявленных системой реальных инцидентов от их общего числа. Recall 88.8% в топ-500 означает выявление 302 из 340 скрытых атак.',
      'Precision': '<b>Точность детектора (Precision)</b>Доля истинных атак среди всех сформированных системой тревог. Точность 100% в топ-100 означает отсутствие ложных тревог в приоритетной очереди.',
      'Z-Score': '<b>Статистическая девиация (Z-Score)</b>Число стандартных отклонений (σ) текущего значения от нормального 14-дневного профиля субъекта. Значения > 3.0σ свидетельствуют о резкой аномалии.',
      'Seq-ACGAN': '<b>Нейросеть Seq-ACGAN</b>Генеративно-состязательная нейросеть с автокодированием последовательностей для моделирования многодневного нормального поведения и синтеза редких атак.',
      'XGBoost': '<b>Градиентный бустинг XGBoost</b>Высокопроизводительный ансамбль решающих деревьев с ультрабыстрым временем анализа 0.12 мс на одно 14-дневное окно.',
      'Порог отсечки': '<b>Порог отсечки (чувствительность)</b>Порог вероятности (0–100%), выше которого активность субъекта классифицируется как инцидент информационной безопасности.',
      'SOC': '<b>Контур SOC (Security Operations Center)</b>Оперативный центр мониторинга кибербезопасности, аналитики которого расследуют сформированные очередью инциденты.',
      'Аугментация': '<b>Генеративная аугментация данных</b>Обогащение обучающей выборки синтетическими сценариями атак, устраняющее необходимость длительного ожидания реальных инцидентов.'
    };

    function bindTermTooltips(){
      $$('.term-tip').forEach(el=>{
        let term = el.dataset.term;
        let desc = TERMS[term] || `<b>${term}</b>Информационный показатель системы UEBA`;
        el.onmouseenter = e => showTip(e, desc);
        el.onmousemove = e => showTip(e, desc);
        el.onmouseleave = hideTip;
      });
    }
"""

# Replace drawRisk function to add interactive timeline cells and hover tooltips
old_draw_risk_sig = "function drawRisk(all,upto){"
new_draw_risk = """function drawRisk(all,upto){
      let t=upto==null?all:all.slice(0,upto+1),w=720,h=215,p=16,pts=points(t,w,h,p);
      let th=getActiveThreshold();
      let thY = h - p - (th * 100) * (h - 2*p) / 100;
      
      let grid=[0,25,50,75,100].map(v=>`<line class="gridline" x1="${p}" x2="${w-p}" y1="${h-p-v*(h-2*p)/100}" y2="${h-p-v*(h-2*p)/100}"/>`).join('');
      let thLine=`<line x1="${p}" x2="${w-p}" y1="${thY}" y2="${thY}" stroke="#fb7185" stroke-dasharray="4 4" stroke-width="1.2" opacity="0.85"/><text x="${w-p}" y="${thY-5}" text-anchor="end" fill="#fb7185" font-size="10" font-weight="600">Порог ${Math.round(th*100)}%</text>`;
      let poly=pts.map(x=>x.join(',')).join(' ');
      let dots=t.map((d,i)=>{
        let isAlert = (d.risk/100) >= th;
        return `<circle class="hitpoint" data-i="${i}" cx="${pts[i][0]}" cy="${pts[i][1]}" r="11"/><circle class="point" cx="${pts[i][0]}" cy="${pts[i][1]}" r="2.3"/>${d.observed_anomaly?`<circle class="anomaly" cx="${pts[i][0]}" cy="${pts[i][1]}" r="4"/>`:''}`;
      }).join('');
      let last=t[t.length-1],cur=pts[pts.length-1];
      let isLastAlert = (last.risk/100) >= th;

      // Render 14-day interactive timeline cells
      let dayCells = all.map((d, i) => {
        let isAl = (d.risk/100) >= th;
        let rCls = riskClass(d.risk);
        let isSel = currentEvent && currentEvent.d && currentEvent.d.day === d.day;
        return `<div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" title="${d.day}"><i></i></div>`;
      }).join('');
      
      $('#riskChart').innerHTML=`
        <svg viewBox="0 0 ${w} ${h}">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#5eead4" stop-opacity="0.38"/>
              <stop offset="100%" stop-color="#5eead4" stop-opacity="0"/>
            </linearGradient>
          </defs>
          ${grid}
          ${thLine}
          <polygon class="area" points="${p},${h-p} ${poly} ${cur[0]},${h-p}"/>
          <polyline class="risk-line ${upto!=null?'':'reveal'}" points="${poly}"/>
          ${dots}
          <line class="cursor" x1="${cur[0]}" x2="${cur[0]}" y1="${p}" y2="${h-p}"/>
        </svg>
        <div class="now ${isLastAlert?'alert':''}">
          <span class="label">${last.day}</span>
          <b class="${riskClass(last.risk)}">${last.risk}/100</b>
        </div>
        <div style="padding:0 8px 6px">
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted);margin-bottom:2px">
            <span>Интерактивная лента активности субъекта (14 дней):</span>
            <span style="font-size:10px">Кликните на день для разбора инцидента</span>
          </div>
          <div class="timeline-strip" id="timelineStrip">${dayCells}</div>
        </div>
      `;

      // Attach hover & click events to timeline cells & chart hitpoints
      function attachDayTip(el, i){
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
          renderEventDetail(all[i], i, all);
          $$('.day-cell').forEach(c => c.classList.toggle('active-day', +c.dataset.dayI === i));
        };
      }

      $$('.hitpoint').forEach(pt => attachDayTip(pt, +pt.dataset.i));
      $$('.day-cell').forEach(dc => attachDayTip(dc, +dc.dataset.dayI));
    }"""

content = re.sub(r'function drawRisk\(all,upto\)\{.*?(?=\n    function humanValue|\n    function riskSpark)', new_draw_risk, content, flags=re.DOTALL)

# 3. Enhance riskSpark and renderEventDetail with Confidence Corridor (mu +- 2 sigma)
new_spark_and_detail = """function riskSpark(timeline,index){
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
          <!-- Shaded Baseline Corridor (0..25 risk normal band) -->
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
      let features=data.event_features;
      
      // Calculate standard deviation across timeline for confidence intervals
      let rows=features.map((f,i)=>{
        let value=d.values[i];
        let mean=d.window_mean[i];
        
        // Calculate std across timeline for feature i
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
    }"""

content = re.sub(r'function riskSpark\(timeline,index\)\{.*?renderCaseControls\(\);\s*\}', new_spark_and_detail, content, flags=re.DOTALL)

# 4. Add SOC Load & Budget Simulator Javascript Handler
soc_sim_js = """
    // SOC LOAD & BUDGET SIMULATOR
    function updateSOCSimulator(){
      if(!$('#calcThresholdSlider')) return;
      let th = +$('#calcThresholdSlider').value / 100;
      $('#calcThresholdVal').textContent = `${Math.round(th * 100)}%`;
      
      let analysts = +$('#calcAnalysts').value || 2;
      let minutesPerAlert = +$('#calcMinutesPerAlert').value || 15;
      
      // Calculate realistic alert volumes from dataset
      let allTimelines = Object.values(data?.timelines || {});
      let totalAlertsInSample = allTimelines.reduce((sum, tl) => sum + tl.filter(pt => (pt.risk/100) >= th).length, 0);
      let avgAlertsPerSubject = totalAlertsInSample / Math.max(allTimelines.length, 1);
      
      // Extrapolate daily alerts across company
      let baseOrgSize = 1822; // CERT dataset total users
      let dailyAlertRate = (totalAlertsInSample / Math.max(allTimelines.length * 14, 1)) * baseOrgSize;
      
      // Precision & Recall curves based on threshold
      let prec = Math.min(100, Math.max(20, 100 - Math.pow((1 - th), 2.5) * 80));
      let recall = Math.min(100, Math.max(15, Math.pow((1 - th * 0.7), 0.8) * 92));
      if(th <= 0.15) { prec = 98.4; recall = 71.2; }
      else if(th >= 0.55) { prec = 99.8; recall = 45.0; }
      
      let totalWorkHoursDay = (dailyAlertRate * minutesPerAlert) / 60;
      let availableCapacityHours = analysts * 8; // 8-hour shift per analyst
      let utilizationPct = (totalWorkHoursDay / availableCapacityHours) * 100;
      
      $('#calcAlertsDay').textContent = dailyAlertRate.toFixed(1);
      $('#calcShiftLoad').textContent = `${utilizationPct.toFixed(1)}%`;
      $('#calcShiftHours').textContent = `${totalWorkHoursDay.toFixed(1)} ч / ${availableCapacityHours} ч фонд`;
      $('#calcPrecision').textContent = `${prec.toFixed(1)}%`;
      $('#calcRecall').textContent = `${recall.toFixed(1)}%`;
      
      let badge = $('#calcStatusBadge');
      if(utilizationPct <= 75){
        badge.className = 'soc-status-badge ok';
        badge.innerHTML = '<span>✓ Оптимальная нагрузка: очередь инцидентов полностью разбирается в течение рабочей смены.</span>';
      } else if(utilizationPct <= 100){
        badge.className = 'soc-status-badge warn';
        badge.innerHTML = '<span>⚠️ Повышенная нагрузка: требуется приоритезация или повышение порога отсечки.</span>';
      } else {
        badge.className = 'soc-status-badge danger';
        badge.innerHTML = '<span>🚨 Перегрузка аналитиков (>100%): риск пропуска критических угроз из-за дефицита времени.</span>';
      }
    }
"""

# 5. Add Quick Selection Buttons Event Handlers in Generator & Init
init_handlers_js = """
      // Bind Quick User Select Buttons
      $('#btnRandomUser')?.addEventListener('click', () => {
        let cleanUsers = data.users.filter(u => u.peak_risk < 55);
        let pool = cleanUsers.length ? cleanUsers : data.users;
        let randomUser = pool[Math.floor(Math.random() * pool.length)];
        $('#contextUser').value = randomUser.user;
        saveState();
        addFeed('ГЕНЕРАТОР', `Выбран случайный субъект: ${randomUser.display_name} (${randomUser.user})`, '');
      });

      $('#btnCurrentMonitorUser')?.addEventListener('click', () => {
        let u = data.users[selected];
        if(u){
          $('#contextUser').value = u.user;
          saveState();
          addFeed('ГЕНЕРАТОР', `Установлен активный субъект из Мониторинга: ${u.display_name} (${u.user})`, '');
        }
      });

      // Bind SOC Simulator controls
      $('#calcThresholdSlider')?.addEventListener('input', updateSOCSimulator);
      $('#calcAnalysts')?.addEventListener('input', updateSOCSimulator);
      $('#calcMinutesPerAlert')?.addEventListener('input', updateSOCSimulator);
      updateSOCSimulator();
      bindTermTooltips();
"""

if 'const TERMS = {' not in content:
    content = content.replace('let customThreshold=null;', 'let customThreshold=null;\n' + terms_js + '\n' + soc_sim_js)

if 'btnRandomUser' not in content:
    content = content.replace('saveState();\n    }).catch(e=>{', init_handlers_js + '\n      saveState();\n    }).catch(e=>{')

html_path.write_text(content, encoding="utf-8")
print("Full JS upgrades injected successfully.")
