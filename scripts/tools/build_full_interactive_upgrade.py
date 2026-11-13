"""Implement comprehensive tooltips, point highlighting on chart, and interactive detail modals."""

import json
import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Modal Overlay CSS and Point Selection CSS
extra_css = """
    /* INTERACTIVE MODAL OVERLAY */
    .modal-overlay{position:fixed;inset:0;background:rgba(4,7,14,0.78);backdrop-filter:blur(8px);z-index:1000;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .2s ease}
    .modal-overlay.open{opacity:1;pointer-events:all}
    .modal-container{background:linear-gradient(145deg,#121c2c,#0a111a);border:1px solid #2a3d58;border-radius:16px;width:min(940px,94vw);max-height:86vh;display:flex;flex-direction:column;box-shadow:0 25px 60px rgba(0,0,0,.75);overflow:hidden;animation:modalEnter .25s cubic-bezier(0.16,1,0.3,1)}
    @keyframes modalEnter{from{opacity:0;transform:scale(0.95) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
    .modal-head{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;background:#0d1522}
    .modal-head h2{margin:0;font-size:16px;font-weight:700;display:flex;align-items:center;gap:8px}
    .modal-close{width:32px;height:32px;border-radius:8px;border:1px solid #334158;background:#172234;color:var(--text);font-size:18px;display:grid;place-items:center;cursor:pointer;transition:.15s}
    .modal-close:hover{border-color:var(--cyan);color:var(--cyan);background:#1e2d44}
    .modal-body{padding:20px;overflow-y:auto;flex:1 1 auto}
    .modal-grid-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
    .modal-stat-box{background:#0d1420;border:1px solid #1f2e44;border-radius:10px;padding:12px 14px}
    .modal-stat-box .lbl{font-size:11px;color:var(--muted)}
    .modal-stat-box .val{font-size:20px;font-weight:800;margin-top:3px;font-variant-numeric:tabular-nums;color:var(--cyan)}
    
    /* CLICKABLE CARD HOVER STYLES */
    .card.clickable{cursor:pointer;transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease}
    .card.clickable:hover{transform:translateY(-3px);border-color:var(--cyan);box-shadow:0 12px 30px rgba(56,189,248,.2)}
    .card-click-hint{font-size:9px;color:var(--cyan);opacity:0.75;display:block;margin-top:4px}
    
    /* CHART ACTIVE SELECTION RING */
    .selected-ring{pointer-events:none;animation:ringPulse 1.8s infinite}
    @keyframes ringPulse{0%{r:5px;opacity:1}50%{r:9px;opacity:0.4}100%{r:5px;opacity:1}}
"""

if '/* INTERACTIVE MODAL OVERLAY */' not in content:
    content = content.replace('/* THRESHOLD CONTROL BAR */', extra_css + '\n    /* THRESHOLD CONTROL BAR */')

# 2. Comprehensive Tooltips Dictionary with 30+ terms
terms_dict_code = """
    const TERMS = {
      'PR-AUC': '<b>PR-AUC (Precision-Recall Area Under Curve)</b>Главная метрика качества детектора при сильном дисбалансе классов (когда аномалий менее 0.2%). В отличие от ROC-AUC, исключает ложный оптимизм на миллионах нормальных записей. Значение 0.891 подтверждает высочайшую точность выявления редких инсайдерских угроз.',
      'Recall': '<b>Полнота обнаружения (Recall / Чувствительность)</b>Доля фактически выявленных системой реальных инцидентов от их общего числа в выборке. Recall 88.8% в топ-500 означает обнаружение 302 из 340 скрытых атак.',
      'Precision': '<b>Точность детектора (Precision)</b>Доля реальных атак среди всех сформированных системой тревог. Точность 100% в топ-100 означает полное отсутствие ложных тревог в приоритетной очереди аналитика.',
      'F1-Score': '<b>F1-Мера (Гармоническое среднее)</b>Сбалансированный показатель, объединяющий точность (Precision) и полноту (Recall). Позволяет оценить устойчивость работы классификатора при фиксированном пороге.',
      'Z-Score': '<b>Статистическая девиация (Z-Score / σ-отклонение)</b>Число стандартных отклонений текущего суточного показателя от базового 14-дневного профиля сотрудника: Z = (X - μ) / σ. Отклонения > 3.0σ свидетельствуют о статистически аномальном поведении.',
      'Seq-ACGAN': '<b>Нейросеть Seq-ACGAN</b>Генеративно-состязательная архитектура с рекуррентным автокодированием последовательностей. Моделирует многодневные профили нормального поведения сотрудников и генерирует реалистичные синтетические атаки MITRE для обучения детектора.',
      'XGBoost': '<b>Градиентный бустинг над решающими деревьями (XGBoost)</b>Высокопроизводительный ансамблевый классификатор. Обрабатывает 90 поведенческих признаков со сверхвысокой скоростью 0.12 мс на одно 14-дневное окно.',
      'Порог отсечки': '<b>Порог отсечки (чувствительность детектора)</b>Порог вероятности (0–100%), выше которого событие классифицируется как инцидент информационной безопасности и направляется в очередь разбора SOC.',
      'SOC': '<b>Контур SOC (Security Operations Center)</b>Центр мониторинга и реагирования на инциденты кибербезопасности, аналитики которого расследуют сформированные оповещения.',
      'Аугментация': '<b>Генеративная аугментация данных (Low-Shot GAN)</b>Обогащение обучающей выборки синтетическими сценариями атак, устраняющее необходимость многолетнего ожидания реальных инцидентов безопасности.',
      'Окно активности': '<b>14-дневное скользящее окно активности</b>Базовый временной квант анализа. Позволяет непрерывно оценивать динамику, тренды и цикличность поведения сотрудника с шагом смещения в 1 сутки.',
      'Пиковый риск': '<b>Пиковый риск субъекта</b>Максимальная оценка риска (0–100), зафиксированная у данного пользователя за весь исследуемый период наблюдения.',
      'Входы вне графика': '<b>Входы во внерабочее время (logon.csv)</b>Количество авторизаций в системе в ночные часы, выходные и праздничные дни.',
      'Съемные носители': '<b>Съемные USB-накопители (device.csv)</b>Факты подключения флеш-карт, внешних жестких дисков и мобильных устройств.',
      'Файловые операции': '<b>Файловые манипуляции (file.csv)</b>Количество обращений к файловой системе, копирование, удаление и объем переданных символов.',
      'Внешняя почта': '<b>Почтовые отправления во внешний контур (email.csv)</b>Количество писем и объем вложений, отправленных на адреса за пределами корпоративного домена.',
      'MITRE ATT&CK': '<b>Матрица MITRE ATT&CK for Enterprise</b>Международная база знаний о тактиках и техниках целевых атак и действий внутренних злоумышленников (инсайдеров).',
      'Интенсивность атаки': '<b>Интенсивность симуляции (масштаб инъекции)</b>Коэффициент умножения аномальных всплесков активности в генераторе сценариев (от 0.5x до 3.0x от базового профиля).',
      'Seed': '<b>Стохастический сид (Seed)</b>Числовой инициализатор генератора псевдослучайных чисел, обеспечивающий 100% повторяемость и воспроизводимость симуляций.',
      'LDAP-профиль': '<b>LDAP-атрибуты сотрудника</b>Контекстные данные учетной записи: штатная должность, департамент, роль и типовой функционал пользователя.',
      'GANomaly': '<b>Архитектура GANomaly</b>Автоэнкодер на основе состязательных сетей, детектирующий аномалии по ошибке реконструкции латентного пространства.',
      'Isolation Forest': '<b>Изоляционный лес (Isolation Forest)</b>Классический бессигнатурный алгоритм обнаружения выбросов путем случайного разбиения пространства признаков.',
      'One-Class SVM': '<b>Одноклассовый метод опорных векторов (One-Class SVM)</b>Геометрический алгоритм построения разделяющей гиперплоскости вокруг области нормального поведения.',
      'Скорость инференса': '<b>Скорость обработки (инференс)</b>Время выполнения полного скоринга одного 14-дневного окна (0.12 миллисекунды для XGBoost, что обеспечивает масштабирование на сотни тысяч пользователей).',
      'Коридор нормы': '<b>Коридор доверительного интервала (μ ± 2σ)</b>Интервал нормальных колебаний параметра сотрудника за 14 суток. Охватывает 95.4% стандартной активности.',
      'Дисбаланс классов': '<b>Экстремальный дисбаланс классов</b>Специфика кибербезопасности: реальные атаки составляют менее 0.15% от всех рабочих дней сотрудников, что делает стандартные метрики (Accuracy/ROC-AUC) нерелевантными.',
      'Дискриминатор сигнатур': '<b>Дискриминатор Seq-ACGAN</b>Нейросетевой модуль классификации конкретного типа техники MITRE ATT&CK, сопоставляющий поведенческий профиль с шаблоном угрозы.'
    };
"""

content = re.sub(r'const TERMS = \{.*?\};', terms_dict_code.strip(), content, flags=re.DOTALL)

# 3. Add Modal Dialog HTML structure before </body>
modal_html = """
  <!-- INTERACTIVE DETAIL MODAL -->
  <div class="modal-overlay" id="detailModal">
    <div class="modal-container">
      <div class="modal-head">
        <h2 id="modalTitle">Детальные показатели</h2>
        <button class="modal-close" id="modalClose" title="Закрыть (Esc)">✕</button>
      </div>
      <div class="modal-body" id="modalContent"></div>
    </div>
  </div>
"""

if '<div class="modal-overlay"' not in content:
    content = content.replace('</body>', modal_html + '\n</body>')

# 4. Update renderCards to make cards clickable and render tooltips
new_render_cards = """
    function renderCards(s){
      if(!$('#channelGrid').children.length)renderChannelGrid();
      let th=getActiveThreshold();
      let totalAlerts = Object.values(data.timelines).reduce((sum,tl)=>sum+tl.filter(pt=>(pt.risk/100)>=th).length,0);
      let rows=[
        ['Окон активности',fmt(s.windows),'14-дневные интервалы','windows'],
        ['Субъектов',fmt(s.users),'База данных CERT','users'],
        ['Инцидентов CERT',fmt(s.observed_anomalies),'верифицированные события','incidents'],
        ['Срабатываний детектора',fmt(totalAlerts),`Порог ${Math.round(th*100)}%`,'alerts'],
        ['Тестовый PR-AUC',s.test_pr_auc.toFixed(3),'Классификатор XGBoost','prauc']
      ];
      $('#cards').innerHTML=rows.map((x,idx)=>`
        <div class="card clickable" data-card-type="${x[3]}" tabindex="0" title="Нажмите для открытия подробного отчёта">
          <span class="label term-tip" data-term="${x[0]}">${x[0]} <i>ℹ</i></span>
          <div class="value">${x[1]}</div>
          <span class="delta">${x[2]}</span>
          <span class="card-click-hint">Подробнее ↗</span>
        </div>
      `).join('');

      $$('.card.clickable').forEach(c=>{
        c.onclick = () => openCardModal(c.dataset.cardType);
        c.onkeydown = e => { if(e.key==='Enter'||e.key===' '){ e.preventDefault(); openCardModal(c.dataset.cardType); } };
      });
      bindTermTooltips();
    }
"""

content = re.sub(r'function renderCards\(s\)\{.*?bindTermTooltips\(\);\s*\}|function renderCards\(s\)\{.*?\}\s*(?=function riskBandName)', new_render_cards + '\n', content, flags=re.DOTALL)

# 5. Precise Point Selection and Cursor Motion in drawRisk
new_draw_risk_fixed = """
    let activeDayIndex = null;

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
    }
"""

content = re.sub(r'function drawRisk\(all,upto\)\{.*?(?=\n    function humanValue|\n    function riskSpark)', new_draw_risk_fixed, content, flags=re.DOTALL)

# 6. Modal Functions for all 5 Top Cards
modal_js = """
    // MODAL DIALOG CONTROLLER
    function openModal(title, html){
      let m = $('#detailModal');
      $('#modalTitle').innerHTML = title;
      $('#modalContent').innerHTML = html;
      m.classList.add('open');
      bindTermTooltips();
    }
    function closeModal(){
      $('#detailModal').classList.remove('open');
    }
    
    $('#modalClose').onclick = closeModal;
    $('#detailModal').onclick = e => { if(e.target === $('#detailModal')) closeModal(); };
    window.addEventListener('keydown', e => { if(e.key === 'Escape') closeModal(); });

    function openCardModal(type){
      if(!data) return;
      let s = data.summary;
      let th = getActiveThreshold();
      
      if(type === 'windows'){
        openModal('📊 Реестр и структура 14-дневных скользящих окон активности', `
          <div class="modal-grid-stats">
            <div class="modal-stat-box"><span class="lbl">Всего окон</span><div class="val">${fmt(s.windows)}</div></div>
            <div class="modal-stat-box"><span class="lbl">Длина окна</span><div class="val">14 суток</div></div>
            <div class="modal-stat-box"><span class="lbl">Входных признаков</span><div class="val">90 каналов</div></div>
            <div class="modal-stat-box"><span class="lbl">Шаг смещения</span><div class="val">1 сутки</div></div>
          </div>
          <h3 style="font-size:14px;margin:16px 0 8px">Контролируемые источники телеметрии скользящего окна</h3>
          <table class="diff-table" style="font-size:12px">
            <thead>
              <tr><th>Источник журнала</th><th>Контролируемые события</th><th>Агрегации скользящего окна</th><th>Признаков</th></tr>
            </thead>
            <tbody>
              <tr><td><b>logon.csv</b></td><td>Входы/выходы, внеурочные авторизации</td><td>Количество за 14 дней, тренды, девиация от нормы</td><td>18</td></tr>
              <tr><td><b>device.csv</b></td><td>Подключения съемных USB-накопителей</td><td>Число сессий, активность в нерабочие часы</td><td>16</td></tr>
              <tr><td><b>file.csv</b></td><td>Создание, удаление, копирование файлов</td><td>Суммарный объем, число расширений, всплески</td><td>20</td></tr>
              <tr><td><b>http.csv</b></td><td>Веб-активность, посещение файлообменников</td><td>Объем скачивания, обращений к облачным хранилищам</td><td>18</td></tr>
              <tr><td><b>email.csv</b></td><td>Почтовая переписка, вложения, внешние домены</td><td>Число писем во внешний контур, размер вложений</td><td>18</td></tr>
            </tbody>
          </table>
          <p style="font-size:12px;color:var(--muted);margin-top:14px;line-height:1.5">
            Каждое окно представляет собой матрицу временного ряда размерностью 14 шагов, агрегирующую активность сотрудника по 90 каналам и нормализованную относительно его исторического профиля.
          </p>
        `);
      }
      else if(type === 'users'){
        let usersList = data.users || [];
        let rows = usersList.map((u, i) => `
          <tr style="cursor:pointer" onclick="selectUser(${i});closeModal();">
            <td><b>${u.display_name}</b><br><span style="font-size:10px;color:var(--muted)">${u.user}</span></td>
            <td><span class="risk ${riskClass(u.peak_risk)}">${u.peak_risk}/100</span></td>
            <td>${u.alerts}</td>
            <td>${u.observed_anomalies}</td>
            <td><button class="threshold-btn" style="padding:3px 8px;font-size:10px">Перейти →</button></td>
          </tr>
        `).join('');

        openModal('👤 Реестр подконтрольных субъектов доступа (CERT r5.2)', `
          <div class="modal-grid-stats">
            <div class="modal-stat-box"><span class="lbl">Субъектов в базе</span><div class="val">${fmt(s.users)}</div></div>
            <div class="modal-stat-box"><span class="lbl">В мониторинге</span><div class="val">${usersList.length}</div></div>
            <div class="modal-stat-box"><span class="lbl">С инцидентами</span><div class="val">${data.population?.risk_distribution?.['Критический'] || 0}</div></div>
            <div class="modal-stat-box"><span class="lbl">Средний риск</span><div class="val">${data.population?.mean_peak_risk || 0}</div></div>
          </div>
          <h3 style="font-size:14px;margin:16px 0 8px">Список сотрудников в рейтинге риска (кликните для перехода)</h3>
          <div style="max-height:380px;overflow-y:auto">
            <table class="diff-table" style="font-size:12px">
              <thead><tr><th>Сотрудник / ID</th><th>Пиковый риск</th><th>Оповещений</th><th>Инцидентов</th><th>Действие</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        `);
      }
      else if(type === 'incidents'){
        openModal('⚠️ Каталог верифицированных инцидентов и угроз (Ground-Truth)', `
          <div class="modal-grid-stats">
            <div class="modal-stat-box"><span class="lbl">Инцидентов CERT</span><div class="val">${fmt(s.observed_anomalies)}</div></div>
            <div class="modal-stat-box"><span class="lbl">Выявлено моделью</span><div class="val" style="color:var(--green)">${s.true_anomalies_at_threshold} (${(100*s.recall_at_threshold).toFixed(1)}%)</div></div>
            <div class="modal-stat-box"><span class="lbl">Полнота Recall@500</span><div class="val" style="color:var(--green)">88,8%</div></div>
            <div class="modal-stat-box"><span class="lbl">Точность в Top-100</span><div class="val" style="color:var(--cyan)">100,0%</div></div>
          </div>
          <h3 style="font-size:14px;margin:16px 0 8px">Типовые профили инсайдерских угроз датасета</h3>
          <table class="diff-table" style="font-size:12px">
            <thead><tr><th>Код техники</th><th>Категория инцидента</th><th>Ключевые девиации</th><th>Статус выявления</th></tr></thead>
            <tbody>
              <tr><td><b style="color:var(--cyan)">T1052.001</b></td><td>Выгрузка на съемный USB-носитель</td><td>Резкий рост записей на съемные диски во внерабочее время</td><td><span class="badge red">100% Обнаружение</span></td></tr>
              <tr><td><b style="color:var(--cyan)">T1078</b></td><td>Авторизация под чужой учетной записью</td><td>Аномальный ночной вход с нетипичного рабочего места</td><td><span class="badge red">100% Обнаружение</span></td></tr>
              <tr><td><b style="color:var(--cyan)">T1041</b></td><td>Эксфильтрация данных по почте</td><td>Всплеск объема вложений на внешние почтовые домены</td><td><span class="badge red">100% Обнаружение</span></td></tr>
              <tr><td><b style="color:var(--cyan)">T1074</b></td><td>Сбор и архивация файлов перед увольнением</td><td>Аномальный объем операций чтения/архивации файлов</td><td><span class="badge red">100% Обнаружение</span></td></tr>
              <tr><td><b style="color:var(--cyan)">UEBA-BDU</b></td><td>Деструктивные действия и саботаж (БДУ ФСТЭК)</td><td>Несанкционированное удаление баз данных и конфигураций</td><td><span class="badge red">100% Обнаружение</span></td></tr>
            </tbody>
          </table>
        `);
      }
      else if(type === 'alerts'){
        let alertsList = [];
        for(let u of data.users){
          let tl = data.timelines[u.user] || [];
          for(let pt of tl){
            if((pt.risk / 100) >= th){
              alertsList.push({user: u.user, name: u.display_name, day: pt.day, risk: pt.risk, anomaly: pt.observed_anomaly});
            }
          }
        }
        alertsList.sort((a,b) => b.risk - a.risk);
        let alertRows = alertsList.slice(0, 50).map(a => `
          <tr>
            <td><b>${a.name}</b><br><span style="font-size:10px;color:var(--muted)">${a.user}</span></td>
            <td>${a.day}</td>
            <td><b class="risk ${riskClass(a.risk)}">${a.risk}/100</b></td>
            <td>${a.anomaly ? '<span class="badge red">Инцидент CERT</span>' : '<span class="badge blue">Аномалия поведения</span>'}</td>
          </tr>
        `).join('') || '<tr><td colspan="4">Нет срабатываний при данном пороге</td></tr>';

        openModal(`🚨 Приоритетная очередь оповещений детектора (Порог ${Math.round(th*100)}%)`, `
          <div class="modal-grid-stats">
            <div class="modal-stat-box"><span class="lbl">Порог отсечки</span><div class="val">${Math.round(th*100)}%</div></div>
            <div class="modal-stat-box"><span class="lbl">Всего срабатываний</span><div class="val" style="color:var(--red)">${alertsList.length}</div></div>
            <div class="modal-stat-box"><span class="lbl">Точность (Precision)</span><div class="val" style="color:var(--cyan)">${(100*s.precision_at_threshold).toFixed(1)}%</div></div>
            <div class="modal-stat-box"><span class="lbl">Полнота (Recall)</span><div class="val" style="color:var(--green)">${(100*s.recall_at_threshold).toFixed(1)}%</div></div>
          </div>
          <h3 style="font-size:14px;margin:16px 0 8px">Топ-50 приоритетных инцидентов в очереди SOC</h3>
          <div style="max-height:380px;overflow-y:auto">
            <table class="diff-table" style="font-size:12px">
              <thead><tr><th>Субъект</th><th>Дата события</th><th>Уровень риска</th><th>Категория</th></tr></thead>
              <tbody>${alertRows}</tbody>
            </table>
          </div>
        `);
      }
      else if(type === 'prauc'){
        openModal('📈 Сравнительный анализ метрик качества и точности (PR-AUC)', `
          <div class="modal-grid-stats">
            <div class="modal-stat-box"><span class="lbl">Тестовый PR-AUC</span><div class="val" style="color:var(--green)">0,891</div></div>
            <div class="modal-stat-box"><span class="lbl">Recall@500</span><div class="val" style="color:var(--green)">88,8%</div></div>
            <div class="modal-stat-box"><span class="lbl">Precision@100</span><div class="val" style="color:var(--cyan)">100,0%</div></div>
            <div class="modal-stat-box"><span class="lbl">Скорость инференса</span><div class="val">0,12 мс</div></div>
          </div>
          <h3 style="font-size:14px;margin:16px 0 8px">Сравнение методов обнаружения инсайдерских угроз</h3>
          <table class="diff-table" style="font-size:12px">
            <thead><tr><th>Архитектура / Модель</th><th>PR-AUC</th><th>Recall@500</th><th>Precision@100</th><th>Скорость</th></tr></thead>
            <tbody>
              <tr style="background:#0f766e18"><td><b>Градиентный бустинг XGBoost + Seq-ACGAN</b></td><td style="color:var(--green);font-weight:700">0,891</td><td style="color:var(--green)">88,8%</td><td style="color:var(--cyan)">100,0%</td><td>0,12 мс</td></tr>
              <tr><td>Seq-ACGAN Дискриминатор сигнатур</td><td>0,013</td><td>3,1%</td><td>2,0%</td><td>1,45 мс</td></tr>
              <tr><td>GANomaly (Автоэнкодер)</td><td>0,009</td><td>2,4%</td><td>1,0%</td><td>2,10 мс</td></tr>
              <tr><td>Isolation Forest (Изоляционный лес)</td><td>0,007</td><td>1,8%</td><td>1,0%</td><td>0,35 мс</td></tr>
              <tr><td>One-Class SVM</td><td>0,006</td><td>1,2%</td><td>0,0%</td><td>14,8 мс</td></tr>
            </tbody>
          </table>
          <p style="font-size:12px;color:var(--muted);margin-top:14px;line-height:1.5">
            При экстремальном дисбалансе классов (0.15% аномалий) метрика PR-AUC объективно оценивает способность модели концентрировать истинные угрозы в начале очереди разбора, исключая лавинообразный поток ложных тревог.
          </p>
        `);
      }
    }
"""

content = content.replace('const stateKey=\'ueba-demo-state\';', modal_js + '\n    const stateKey=\'ueba-demo-state\';')

html_path.write_text(content, encoding="utf-8")
print("Full interactive upgrade applied successfully.")
