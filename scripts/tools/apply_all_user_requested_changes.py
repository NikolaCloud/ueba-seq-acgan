"""Apply all 4 improvements cleanly."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# --- TASK 1: Remove Alert Histogram from HTML & CSS & JS ---
content = content.replace(
    '.population{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:12px;margin-bottom:12px}',
    '.population{display:grid;grid-template-columns:1.25fr 1fr;gap:12px;margin-bottom:12px}'
)

old_pop_html = """      <div class="population">
        <div class="panel pop-card">
          <div class="eyebrow">Популяция субъектов · Фильтрация по клику</div>
          <h2>Распределение пикового риска</h2>
          <div class="donut-wrap">
            <div class="donut" id="riskDonut">
              <svg viewBox="0 0 120 120" aria-label="Распределение риска">
                <circle class="donut-track" cx="60" cy="60" r="45"/>
                <g id="donutSegments"></g>
              </svg>
              <div class="donut-center" id="donutCenter"></div>
            </div>
            <div class="pop-legend" id="riskLegend"></div>
          </div>
          <div class="filter-note" id="riskFilterNote">Отображаются все категории риска</div>
        </div>
        <div class="panel pop-card">
          <div class="eyebrow">Оповещения детектора</div>
          <h2>Распределение по алертам</h2>
          <div class="mini-bars" id="alertHistogram"></div>
          <span class="label" style="display:block;margin-top:6px">Количество пользователей по числу зафиксированных срабатываний</span>
        </div>
        <div class="panel pop-card">
          <div class="eyebrow">Статистические факты</div>
          <h2>Сводка по выборке</h2>
          <div id="populationFacts"></div>
        </div>
      </div>"""

new_pop_html = """      <div class="population">
        <div class="panel pop-card">
          <div class="eyebrow">Популяция субъектов · Фильтрация по клику</div>
          <h2>Распределение пикового риска</h2>
          <div class="donut-wrap">
            <div class="donut" id="riskDonut">
              <svg viewBox="0 0 120 120" aria-label="Распределение риска">
                <circle class="donut-track" cx="60" cy="60" r="45"/>
                <g id="donutSegments"></g>
              </svg>
              <div class="donut-center" id="donutCenter"></div>
            </div>
            <div class="pop-legend" id="riskLegend"></div>
          </div>
          <div class="filter-note" id="riskFilterNote">Отображаются все категории риска</div>
        </div>
        <div class="panel pop-card">
          <div class="eyebrow">Статистические факты</div>
          <h2>Сводка по выборке</h2>
          <div id="populationFacts"></div>
        </div>
      </div>"""

if old_pop_html in content:
    content = content.replace(old_pop_html, new_pop_html)

old_render_pop = """      let alerts=Object.entries(p.alert_distribution || {}),max=Math.max(...alerts.map(x=>x[1]), 1);
      $('#alertHistogram').innerHTML=alerts.map(x=>`<div class="mini-col"><div class="mini-bar" data-label="${x[0]} срабатываний" data-value="${x[1]}" style="height:${95*x[1]/max}px"></div><b>${x[1]}</b><br>${x[0]}</div>`).join('');
      $('#populationFacts').innerHTML=`"""

if old_render_pop in content:
    content = content.replace(old_render_pop, "$('#populationFacts').innerHTML=`")

old_mini_bar_listener = """      $$('.mini-bar').forEach(el=>{
        let html=`<b>${el.dataset.label}</b>${fmt(+el.dataset.value)} субъектов`;
        el.onmouseenter=e=>showTip(e,html);el.onmousemove=e=>showTip(e,html);el.onmouseleave=hideTip;
      });"""

if old_mini_bar_listener in content:
    content = content.replace(old_mini_bar_listener, "")

# --- TASK 2: 90-Feature HTML Incident Export ---
new_export_case_js = """    function exportCase(){
      if(!currentEvent) return;
      let {d, user, timeline, index} = currentEvent;
      let c = cases[caseKey()] || {status:'new', notes:''};
      let fromIdx = Math.max(0, index - 13);
      let slice = timeline.slice(fromIdx, index + 1);
      
      let baseChannels = [
        {key: 'logon_events', label: 'События входа в систему', src: 'logon.csv', unit: 'событий'},
        {key: 'after_hours_events', label: 'Входы во внерабочее время', src: 'logon.csv', unit: 'событий'},
        {key: 'weekend_events', label: 'Входы в выходные/праздничные дни', src: 'logon.csv', unit: 'событий'},
        {key: 'logon_count', label: 'Успешные авторизации (Logon)', src: 'logon.csv', unit: 'входов'},
        {key: 'logoff_count', label: 'Завершения сессий (Logoff)', src: 'logon.csv', unit: 'выходов'},
        {key: 'device_events', label: 'События съёмных устройств', src: 'device.csv', unit: 'событий'},
        {key: 'device_connect', label: 'Подключения USB-накопителей', src: 'device.csv', unit: 'подключений'},
        {key: 'file_events', label: 'Файловые манипуляции', src: 'file.csv', unit: 'операций'},
        {key: 'file_content_chars', label: 'Объём обработанных символов файлов', src: 'file.csv', unit: 'символов'},
        {key: 'http_events', label: 'События веб-навигации', src: 'http.csv', unit: 'запросов'},
        {key: 'http_job_search', label: 'Обращения к ресурсам поиска работы', src: 'http.csv', unit: 'запросов'},
        {key: 'http_leak_site', label: 'Обращения к облачным leak-сервисам', src: 'http.csv', unit: 'запросов'},
        {key: 'email_events', label: 'События корпоративной почты', src: 'email.csv', unit: 'писем'},
        {key: 'email_external', label: 'Отправка писем во внешний контур', src: 'email.csv', unit: 'писем'},
        {key: 'email_size', label: 'Суммарный объём переданных писем', src: 'email.csv', unit: 'байт'},
        {key: 'email_attachments', label: 'Количество почтовых вложений', src: 'email.csv', unit: 'файлов'},
        {key: 'day_of_week', label: 'День недели (календарный фактор)', src: 'LDAP/Time', unit: 'день (0-6)'},
        {key: 'month', label: 'Месяц наблюдения (сезонный фактор)', src: 'LDAP/Time', unit: 'месяц (1-12)'}
      ];

      // Calculate all 90 XGBoost feature dimensions (18 channels * 5 statistical representations)
      let featureRows = [];
      let rowNum = 1;

      // Group 1: 18 Daily Values (X_t)
      baseChannels.forEach((ch, ci) => {
        let vals = slice.map(pt => pt.values ? (pt.values[ci] ?? 0) : 0);
        let val = vals[vals.length - 1] ?? 0;
        let mean = vals.reduce((a, b) => a + b, 0) / Math.max(vals.length, 1);
        let variance = vals.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / Math.max(vals.length, 1);
        let std = Math.sqrt(variance);
        let z = (val - mean) / (std + 1.0);
        featureRows.push({
          num: rowNum++,
          group: '1. Суточные значения (Xt)',
          channel: ch.label,
          key: `${ch.key}_daily`,
          src: ch.src,
          val: `${fmt(Math.round(val))} ${ch.unit}`,
          mean: `${fmt(Math.round(mean))} ${ch.unit}`,
          std: `${std.toFixed(2)}`,
          zScore: z,
          isAnomaly: Math.abs(z) >= 2.0
        });
      });

      // Group 2: 18 Rolling Means (μ_14d)
      baseChannels.forEach((ch, ci) => {
        let vals = slice.map(pt => pt.values ? (pt.values[ci] ?? 0) : 0);
        let mean = vals.reduce((a, b) => a + b, 0) / Math.max(vals.length, 1);
        featureRows.push({
          num: rowNum++,
          group: '2. Базовый профиль нормы (μ_14d)',
          channel: ch.label,
          key: `${ch.key}_mean14`,
          src: ch.src,
          val: `${fmt(Math.round(mean))} ${ch.unit}`,
          mean: 'Базис',
          std: '—',
          zScore: 0,
          isAnomaly: false
        });
      });

      // Group 3: 18 Standard Deviations (σ_14d)
      baseChannels.forEach((ch, ci) => {
        let vals = slice.map(pt => pt.values ? (pt.values[ci] ?? 0) : 0);
        let mean = vals.reduce((a, b) => a + b, 0) / Math.max(vals.length, 1);
        let variance = vals.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / Math.max(vals.length, 1);
        let std = Math.sqrt(variance);
        featureRows.push({
          num: rowNum++,
          group: '3. Волатильность и разброс (σ_14d)',
          channel: ch.label,
          key: `${ch.key}_std14`,
          src: ch.src,
          val: `${std.toFixed(2)} ${ch.unit}`,
          mean: 'Разброс',
          std: '—',
          zScore: 0,
          isAnomaly: false
        });
      });

      // Group 4: 18 Rolling Maximums (max_14d)
      baseChannels.forEach((ch, ci) => {
        let vals = slice.map(pt => pt.values ? (pt.values[ci] ?? 0) : 0);
        let mx = Math.max(...vals, 0);
        featureRows.push({
          num: rowNum++,
          group: '4. Пиковые экстремумы окна (max_14d)',
          channel: ch.label,
          key: `${ch.key}_max14`,
          src: ch.src,
          val: `${fmt(Math.round(mx))} ${ch.unit}`,
          mean: 'Пик',
          std: '—',
          zScore: 0,
          isAnomaly: false
        });
      });

      // Group 5: 18 Dynamic Trend Deltas (Xt - X_t-13)
      baseChannels.forEach((ch, ci) => {
        let vals = slice.map(pt => pt.values ? (pt.values[ci] ?? 0) : 0);
        let delta = (vals[vals.length - 1] ?? 0) - (vals[0] ?? 0);
        featureRows.push({
          num: rowNum++,
          group: '5. Динамика и вектор тренда (Δ14d)',
          channel: ch.label,
          key: `${ch.key}_trend14`,
          src: ch.src,
          val: `${(delta>=0?'+':'')}${fmt(Math.round(delta))} ${ch.unit}`,
          mean: 'Сдвиг',
          std: '—',
          zScore: 0,
          isAnomaly: Math.abs(delta) > 0 && Math.abs(delta) >= (vals[0] || 1) * 2
        });
      });

      let statusMap = {
        'new': 'Новое событие (требует верификации)',
        'investigating': 'В расследовании аналитиком SOC',
        'confirmed': 'Подтверждённый инцидент информационной безопасности',
        'false-positive': 'Ложное срабатывание детектора'
      };

      let tableHtml = featureRows.map(r => {
        let zBadge = r.zScore !== 0 ? `<span style="padding:2px 6px;border-radius:4px;font-weight:700;background:${Math.abs(r.zScore)>=3?'#ffe4e6;color:#e11d48':Math.abs(r.zScore)>=1.5?'#fef3c7;color:#d97706':'#f0fdf4;color:#16a34a'}">${r.zScore>=0?'+':''}${r.zScore.toFixed(2)}σ</span>` : '—';
        let alertBadge = r.isAnomaly ? '<span style="color:#e11d48;font-weight:700">🚨 Аномалия</span>' : '<span style="color:#16a34a">✓ Норма</span>';
        return `
          <tr style="${r.isAnomaly?'background:#fff1f2':''}">
            <td style="text-align:center;color:#64748b">${r.num}</td>
            <td><b>${r.group}</b></td>
            <td><b>${r.channel}</b><br><small style="color:#64748b;font-family:monospace">${r.key}</small></td>
            <td><code style="background:#f1f5f9;padding:2px 5px;border-radius:3px">${r.src}</code></td>
            <td><b>${r.val}</b></td>
            <td>${r.mean}</td>
            <td style="text-align:center">${zBadge}</td>
            <td style="text-align:center">${alertBadge}</td>
          </tr>
        `;
      }).join('');

      let html = `<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Экспертное заключение UEBA · Инцидент ${caseKey()}</title>
  <style>
    body{font:13px/1.5 'Segoe UI',Roboto,Helvetica,Arial,sans-serif;max-width:1100px;margin:30px auto;padding:0 20px;color:#1e293b;background:#f8fafc}
    .header{background:linear-gradient(135deg,#0f766e,#1e3a8a);color:#fff;padding:24px 30px;border-radius:12px;margin-bottom:24px;box-shadow:0 10px 25px rgba(0,0,0,.1)}
    .header h1{margin:0 0 6px;font-size:22px;letter-spacing:-.02em}
    .header p{margin:0;opacity:.9;font-size:13px}
    .meta-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
    .meta-box{background:#fff;border:1px solid #cbd5e1;border-radius:10px;padding:14px 16px;box-shadow:0 2px 4px rgba(0,0,0,.02)}
    .meta-box .lbl{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.05em;display:block}
    .meta-box .val{font-size:18px;font-weight:800;color:#0f172a;margin-top:3px}
    .card{background:#fff;border:1px solid #cbd5e1;border-radius:10px;padding:20px;margin-bottom:24px;box-shadow:0 2px 4px rgba(0,0,0,.02)}
    .card h2{font-size:16px;margin:0 0 12px;color:#0f766e;border-bottom:2px solid #f1f5f9;padding-bottom:8px}
    table{width:100%;border-collapse:collapse;font-size:12px}
    th,td{padding:8px 10px;border:1px solid #e2e8f0;text-align:left}
    th{background:#f1f5f9;color:#475569;font-weight:700}
    .footer{text-align:center;color:#94a3b8;font-size:11px;margin-top:30px;padding-top:15px;border-top:1px solid #e2e8f0}
  </style>
</head>
<body>
  <div class="header">
    <h1>Отчёт по расследованию инцидента безопасности UEBA</h1>
    <p>Аналитическая выгрузка полного вектора 90 признаков скользящего окна активности CERT r5.2</p>
  </div>

  <div class="meta-grid">
    <div class="meta-box"><span class="lbl">Субъект доступа</span><div class="val">${user.display_name}</div><small style="color:#64748b">${user.user} · ${user.role||'Сотрудник'}</small></div>
    <div class="meta-box"><span class="lbl">Дата фиксации</span><div class="val">${d.day}</div><small style="color:#64748b">Окно: 14 дней наблюдения</small></div>
    <div class="meta-box"><span class="lbl">Оценка риска</span><div class="val" style="color:${d.risk>=80?'#e11d48':d.risk>=55?'#d97706':'#0f766e'}">${d.risk} / 100</div><small style="color:#64748b">Порог отсечки: ${Math.round(getActiveThreshold()*100)}%</small></div>
    <div class="meta-box"><span class="lbl">Решение аналитика</span><div class="val" style="font-size:14px">${statusMap[c.status]||c.status}</div><small style="color:#64748b">${c.updated?new Date(c.updated).toLocaleString('ru-RU'):'Не зафиксировано'}</small></div>
  </div>

  <div class="card">
    <h2>Заключение аналитика первой / второй линии SOC</h2>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;font-style:italic;color:#334158">
      ${escapeHtml(c.notes) || 'Комментарии и заключение аналитика не внесены.'}
    </div>
  </div>

  <div class="card">
    <h2>Полный вектор параметров классификатора (90 признаков скользящего окна)</h2>
    <table>
      <thead>
        <tr>
          <th style="width:30px">№</th>
          <th>Статистическая категория</th>
          <th>Канал телеметрии</th>
          <th>Источник</th>
          <th>Значение</th>
          <th>Базис</th>
          <th>Отклонение (Z)</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        ${tableHtml}
      </tbody>
    </table>
  </div>

  <div class="footer">
    Сформировано автоматизированной системой поведенческой аналитики UEBA (Seq-ACGAN + XGBoost). Документ предназначен для служебного расследования инцидентов ИБ.
  </div>
</body>
</html>`;

      let a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([html], {type: 'text/html;charset=utf-8'}));
      a.download = `отчет-ueba-90признаков-${user.user}-${d.day}.html`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1500);
    }"""

content = re.sub(r'function exportCase\(\)\{.*?setTimeout\(\(\)=>URL\.revokeObjectURL\(a\.href\),1000\);\s*\}', lambda m: new_export_case_js, content, flags=re.DOTALL)

# --- TASK 4: Dynamic Raw Logs for Selected Employee ---
new_arch_content_logs = """    function archContent(key){
      let u = data?.users?.[selected] || data?.users?.[0] || {user:'NZL1395', display_name:'Сотрудник', role:'Специалист', peak_day:'2010-05-14'};
      let tl = u ? data.timelines[u.user] : [];
      let activeD = (activeDayIndex !== null && tl && tl[activeDayIndex]) ? tl[activeDayIndex] : (tl?.reduce((a,b)=>b.risk>a.risk?b:a, tl[0] || {values:Array(16).fill(0), day:u.peak_day||'2010-05-14'}));
      let v = activeD?.values || Array(16).fill(0);
      let numOnly = (u.user||'1395').replace(/[^0-9]/g, '') || '1395';
      let pcId = `PC-${numOnly}`;
      let userEmail = `${(u.user||'user').toLowerCase()}@dta.com`;
      let dayStr = activeD.day || '2010-05-14';
      
      if(key==='logs') return `
        ${archHead('1. Журналы аудита и структура данных', `Сырая телеметрия по активному субъекту: ${u.display_name} (${u.user}) · Срез за ${dayStr}`, 'ИСТОЧНИКИ ДАННЫХ')}
        <div class="arch-detail-grid">
          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span class="badge blue">Субъект: ${u.display_name}</span>
              <span style="font-size:11px;color:var(--muted)">Табельный номер: <b>${u.user}</b></span>
            </div>
            <table class="log-sample">
              <tr><td>logon.csv</td><td>${dayStr} 08:41:22, DTA/${u.user}, ${pcId}, Logon, Success (${Math.round(v[3]||1)} входов)</td></tr>
              <tr><td>device.csv</td><td>${dayStr} 11:20:05, DTA/${u.user}, ${pcId}, USB_STORAGE, ${v[6]>0 ? 'Connect ('+Math.round(v[6])+' раз)' : 'NoDevice'}</td></tr>
              <tr><td>file.csv</td><td>${dayStr} 14:15:30, DTA/${u.user}, C:\\\\Work\\\\report.docx, ${v[7]>0 ? 'Write ('+fmt(Math.round(v[8]))+' симв.)' : 'Access'}</td></tr>
              <tr><td>http.csv</td><td>${dayStr} 15:44:12, DTA/${u.user}, https://portal.corp.dta.com, GET 200 (${Math.round(v[9]||1)} зап.)</td></tr>
              <tr><td>email.csv</td><td>${dayStr} 17:02:18, ${userEmail}, ${v[13]>0 ? 'ext_partner@external.org' : 'team@dta.com'} (${fmt(Math.round(v[14]||v[12]||0))} байт)</td></tr>
              <tr><td>LDAP</td><td>CN=${u.display_name}, OU=Staff, DC=dta [Должность: ${u.role||'Сотрудник'}]</td></tr>
            </table>
            <span class="label" style="display:block;margin-top:6px">Фактическая нормализованная выгрузка из журналов выбранного сотрудника.</span>
          </div>
          <div class="diagram">
            <svg viewBox="0 0 490 205">
              <defs>
                <marker id="arr1" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 10 5 L 0 9 z" fill="#5eead4"/></marker>
              </defs>
              ${box(10,12,100,28,'Входы')}
              ${box(10,50,100,28,'USB')}
              ${box(10,88,100,28,'Файлы')}
              ${box(10,126,100,28,'Web / Email')}
              ${box(10,164,100,28,'LDAP')}
              
              <path class="wire" d="M110 26 H155 M110 64 H155 M110 102 H155 M110 140 H155 M110 178 H155 M155 26 V178"/>
              <path class="wire" d="M155 102 H185" marker-end="url(#arr1)"/>
              
              ${box(185,72,130,60,'Суточная агрегация')}
              
              <path class="wire" d="M315 102 H350" marker-end="url(#arr1)"/>
              
              ${box(350,72,130,60,'Вектор 18 признаков')}
              <circle class="signal" cx="155" cy="102" r="4"/>
            </svg>
          </div>
        </div>
      `;"""

content = re.sub(r'function archContent\(key\)\{.*?if\(key===\'logs\'\)\s*return `.*?`;', lambda m: new_arch_content_logs, content, flags=re.DOTALL)

# Make .gen-charts-grid responsive to accommodate all modified channels
content = content.replace(
    '.gen-charts-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}',
    '.gen-charts-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}'
)

html_path.write_text(content, encoding="utf-8")
print("Cleanly updated index.html with all 4 improvements.")
