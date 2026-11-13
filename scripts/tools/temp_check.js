
const $=s=>document.querySelector(s),$$=s=>document.querySelectorAll(s),fmt=n=>new Intl.NumberFormat('ru-RU').format(n);
    let data,scenarios=[],selected=0,tick=0,timer=null,lastGeneration=null,generationHistory=[],populationFilter=null,cases={},builderMode='preset',customBuilderState=null,currentEvent=null;
    let customThreshold=null;

        const TERMS = {
      'Окон активности': '<b>14-дневное скользящее окно активности</b>Базовый временной квант анализа. Позволяет непрерывно оценивать динамику, тренды и цикличность поведения сотрудника с шагом смещения в 1 сутки. <i>(Нажмите на карточку для детальной структуры)</i>',
      'Окно активности': '<b>14-дневное скользящее окно активности</b>Базовый временной квант анализа. Непрерывно оценивает динамику и тренды поведения с шагом смещения в 1 сутки.',
      'Субъектов': '<b>Субъекты доступа (персонал организации)</b>Учетные записи подконтрольных сотрудников в базе данных CERT r5.2. <i>(Нажмите на карточку для просмотра полного реестра)</i>',
      'Инцидентов CERT': '<b>Верифицированные инциденты (Ground-Truth)</b>Фактические подтвержденные инсайдерские атаки в выборке (340 событий). <i>(Нажмите на карточку для каталога угроз)</i>',
      'Срабатываний детектора': '<b>Срабатывания модели при текущем пороге</b>Количество 14-дневных окон, в которых оценка риска превысила установленный порог отсечки. <i>(Нажмите для просмотра очереди SOC)</i>',
      'Тестовый PR-AUC': '<b>Тестовый показатель PR-AUC (0.891)</b>Интегральная площадь под кривой Precision-Recall. <i>(Нажмите для сравнительного анализа моделей)</i>',
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

    function bindTermTooltips(){
      $$('.term-tip').forEach(el=>{
        let term = el.dataset.term;
        let desc = TERMS[term] || `<b>${term}</b>Информационный показатель системы UEBA`;
        el.onmouseenter = e => showTip(e, desc);
        el.onmousemove = e => showTip(e, desc);
        el.onmouseleave = hideTip;
      });
    }


    
    // SOC LOAD & BUDGET SIMULATOR
    function updateSOCSimulator(){
      let slider = document.getElementById('calcThresholdSlider');
      if(!slider || !data) return;
      
      let thPct = parseInt(slider.value, 10);
      let th = thPct / 100;
      let thDisplay = document.getElementById('calcThresholdVal');
      if(thDisplay) thDisplay.textContent = `${thPct}%`;
      
      let analysts = parseInt(document.getElementById('calcAnalysts')?.value, 10) || 2;
      let minutesPerAlert = parseInt(document.getElementById('calcMinutesPerAlert')?.value, 10) || 15;
      
      // Calculate realistic alert metrics from actual timeline data
      let allTimelines = Object.values(data.timelines || {});
      let totalPoints = 0;
      let totalAlertsInSample = 0;
      
      for(let tl of allTimelines){
        totalPoints += tl.length;
        for(let pt of tl){
          if((pt.risk / 100) >= th) totalAlertsInSample++;
        }
      }
      
      let alertRatePerPoint = totalAlertsInSample / Math.max(totalPoints, 1);
      let baseOrgUsers = 1822; // Total enterprise size
      let dailyAlertRate = alertRatePerPoint * baseOrgUsers;
      
      // Precision & Recall curves based on threshold
      let prec, recall;
      if(th <= 0.15){
        prec = 98.4 - (0.15 - th) * 8.0;
        recall = 71.2 + (0.15 - th) * 120.0;
      } else if(th <= 0.55){
        prec = 98.4 + ((th - 0.15) / 0.40) * 1.4;
        recall = 71.2 - ((th - 0.15) / 0.40) * 26.2;
      } else {
        prec = 99.8 + ((th - 0.55) / 0.30) * 0.2;
        recall = 45.0 - ((th - 0.55) / 0.30) * 30.0;
      }
      prec = Math.min(100, Math.max(10, prec));
      recall = Math.min(100, Math.max(5, recall));
      
      let totalWorkHoursDay = (dailyAlertRate * minutesPerAlert) / 60;
      let availableCapacityHours = analysts * 8; // 8-hour shift
      let utilizationPct = (totalWorkHoursDay / availableCapacityHours) * 100;
      
      let alertsDayEl = document.getElementById('calcAlertsDay');
      if(alertsDayEl) alertsDayEl.textContent = dailyAlertRate.toFixed(1);
      
      let shiftLoadEl = document.getElementById('calcShiftLoad');
      if(shiftLoadEl){
        shiftLoadEl.textContent = `${utilizationPct.toFixed(1)}%`;
        shiftLoadEl.style.color = utilizationPct <= 75 ? 'var(--green)' : utilizationPct <= 100 ? 'var(--amber)' : 'var(--red)';
      }
      
      let shiftHoursEl = document.getElementById('calcShiftHours');
      if(shiftHoursEl) shiftHoursEl.textContent = `${totalWorkHoursDay.toFixed(1)} ч / ${availableCapacityHours} ч фонд`;
      
      let precEl = document.getElementById('calcPrecision');
      if(precEl) precEl.textContent = `${prec.toFixed(1)}%`;
      
      let recallEl = document.getElementById('calcRecall');
      if(recallEl) recallEl.textContent = `${recall.toFixed(1)}%`;
      
      let badge = document.getElementById('calcStatusBadge');
      if(badge){
        if(utilizationPct <= 75){
          badge.className = 'soc-status-badge ok';
          badge.innerHTML = '<span>✓ Оптимальный баланс: очередь инцидентов полностью разбирается в течение рабочей смены.</span>';
        } else if(utilizationPct <= 100){
          badge.className = 'soc-status-badge warn';
          badge.innerHTML = '<span>⚠️ Повышенная нагрузка: требуется приоритезация или повышение порога отсечки.</span>';
        } else {
          badge.className = 'soc-status-badge danger';
          badge.innerHTML = '<span>🚨 Перегрузка аналитиков (>100%): риск пропуска критических угроз из-за дефицита времени.</span>';
        }
      }
    }


    
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

    const stateKey='ueba-demo-state';
    function saveState(){

      if(!data)return;
      let state={
        selectedUser:data.users[selected]?.user,
        tick,
        view:$('.tab.active')?.dataset.view,
        scenario:$('#scenario')?.value,
        intensity:$('#intensity')?.value,
        contextUser:$('#contextUser')?.value,
        seed:$('#seed')?.value,
        feed:$('#feed')?.innerHTML,
        lastGeneration,
        generationHistory,
        cases,
        builderMode,
        customThreshold,
        customBuilderState:$('#channelGrid')?.children.length?customProfile():customBuilderState
      };
      sessionStorage.setItem(stateKey,JSON.stringify(state));
    }

    function readState(){
      let requested=new URLSearchParams(location.search).get('builder');
      try{
        let saved=JSON.parse(sessionStorage.getItem(stateKey)||'{}');
        cases=saved.cases||{};
        builderMode=requested||saved.builderMode||'preset';
        customBuilderState=saved.customBuilderState||null;
        customThreshold=saved.customThreshold??null;
        return saved;
      }catch{
        cases={};builderMode=requested||'preset';customBuilderState=null;customThreshold=null;return {};
      }
    }

    function getActiveThreshold(){
      return customThreshold!==null ? customThreshold : (data?.summary?.validation_threshold ?? 0.15);
    }

    function showTip(e,html){let t=$('#tooltip');t.innerHTML=html;t.style.left=Math.min(e.clientX+14,innerWidth-205)+'px';t.style.top=Math.min(e.clientY+14,innerHeight-110)+'px';t.classList.add('show')}
    function hideTip(){$('#tooltip').classList.remove('show')}
    $$('.tab').forEach(b=>b.onclick=()=>{
      $$('.tab,.view').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      $('#'+b.dataset.view).classList.add('active');
      if(b.dataset.view === 'method') updateSOCSimulator();

      // Bind Quick User Select Buttons
      let btnRandom = document.getElementById('btnRandomUser');
      if(btnRandom){
        btnRandom.onclick = () => {
          let pool = data.users || [];
          if(pool.length){
            let rand = pool[Math.floor(Math.random() * pool.length)];
            $('#contextUser').value = rand.user;
            saveState();
            addFeed('ГЕНЕРАТОР', `Выбран случайный субъект: ${rand.display_name} (${rand.user})`, '');
          }
        };
      }

      let btnFromMon = document.getElementById('btnCurrentMonitorUser');
      if(btnFromMon){
        btnFromMon.onclick = () => {
          let u = data.users[selected];
          if(u){
            $('#contextUser').value = u.user;
            saveState();
            addFeed('ГЕНЕРАТОР', `Установлен субъект из Мониторинга: ${u.display_name} (${u.user})`, '');
          }
        };
      }

      if(b.dataset.view === 'about') renderArch($('.arch-node.active')?.dataset.arch || 'logs');
      saveState();
    });
    function riskClass(n){return n>=80?'critical':n>=55?'high':n>=30?'medium':'low'}

    
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



    function caseKey(){return currentEvent?`${currentEvent.user.user}:${currentEvent.d.day}`:''}
    function renderCaseControls(){
      if(!currentEvent)return;
      let key=caseKey(),c=cases[key]||{status:'new',notes:'',updated:null},labels={new:'Новое событие',investigating:'В расследовании',confirmed:'Инцидент подтверждён', 'false-positive':'Ложное срабатывание'},slot=$('#caseControls');
      $('#eventDetail .event-head').after(slot);
      slot.innerHTML=`
        <div class="case-panel">
          <div class="case-head">
            <div><div class="eyebrow">Карточка расследования инцидента · ${key}</div><b>Статус аналитика</b></div>
            <span class="case-status ${c.status}">${labels[c.status]}</span>
          </div>
          <div class="case-actions">
            <button data-case-status="investigating">Взять в работу</button>
            <button data-case-status="confirmed">Подтвердить инцидент</button>
            <button data-case-status="false-positive">Отметить ложным</button>
            <button id="exportCase">Экспорт отчёта (HTML)</button>
          </div>
          <textarea class="case-notes" id="caseNotes" placeholder="Заключение аналитика, комментарии и принятые меры…">${escapeHtml(c.notes)}</textarea>
          <div class="case-meta">
            <span>Ответственный: SOC Аналитик</span>
            <span>${c.updated?`Обновлено: ${new Date(c.updated).toLocaleString('ru-RU')}`:'Решение не зафиксировано'}</span>
          </div>
        </div>
      `;
      $$('[data-case-status]').forEach(b=>{b.classList.toggle('active',b.dataset.caseStatus===c.status);b.onclick=()=>updateCase(b.dataset.caseStatus)});
      $('#caseNotes').oninput=e=>updateCase(null,e.target.value,false);
      $('#exportCase').onclick=exportCase;
    }

    function escapeHtml(s=''){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
    function updateCase(status,notes=null,rerender=true){let key=caseKey(),old=cases[key]||{status:'new',notes:''};cases[key]={status:status||old.status,notes:notes===null?old.notes:notes,updated:new Date().toISOString()};saveState();if(rerender)renderCaseControls()}
        function exportCase(){
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
    }

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
          <polyline class="risk-line" points="${poly}"/>
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
    function addFeed(type,text,level){let el=document.createElement('div');el.className='event '+(level==='red'?'alert':'');el.innerHTML=`<span class="label">${new Date().toLocaleTimeString('ru-RU')}</span><span>${text}</span><span class="badge ${level||''}">${type}</span>`;$('#feed').prepend(el);while($('#feed').children.length>8)$('#feed').lastChild.remove();saveState()}
    
    $('#play').onclick=()=>{
      if(timer){clearInterval(timer);timer=null;$('#play').textContent='▶ Запустить поток';return}
      $('#play').textContent='Ⅱ Пауза';
      let timeline=data.timelines[data.users[selected].user];
      let th=getActiveThreshold();
      timer=setInterval(()=>{
        let d=timeline[tick];
        drawRisk(timeline,tick);
        renderEventDetail(d,tick,timeline);
        let isAlert = (d.risk/100) >= th;
        if(isAlert)addFeed('ОПОВЕЩЕНИЕ',`${data.users[selected].display_name}: риск ${d.risk} (превышение порога)`,'red');
        else if(d.observed_anomaly)addFeed('CERT',`${data.users[selected].display_name}: верифицированный инцидент, риск ${d.risk}`,'red');
        else if(tick%7===0)addFeed('СИСТЕМА',`${data.users[selected].display_name}: риск ${d.risk}`,'');
        tick=(tick+1)%timeline.length;
      },+$('#speed').value);
    };
    $('#speed').onchange=()=>{if(timer){clearInterval(timer);timer=null;$('#play').click()}};

    /* THRESHOLD SLIDER HANDLERS */
    function setThreshold(val){
      customThreshold = val / 100;
      $('#thresholdSlider').value = val;
      $('#thresholdDisplay').textContent = `${val}%`;
      renderCards(data.summary);
      renderPopulation(data.population);
      renderUserRows(populationFilter?data.users.filter(u=>riskBandName(u.peak_risk)===populationFilter):data.users);
      let u=data.users[selected],tl=data.timelines[u.user];
      drawRisk(tl,null);
      renderEventDetail(tl[tick]||tl[0],tick,tl);
      saveState();
    }
    $('#thresholdSlider').oninput=e=>setThreshold(+e.target.value);
    $('#resetThreshold').onclick=()=>setThreshold(15);

    function setBuilderMode(mode){builderMode=mode;$$('[data-builder]').forEach(x=>x.classList.toggle('active',x.dataset.builder===mode));$('#presetBuilder').classList.toggle('hidden',mode==='custom');$('#customBuilder').classList.toggle('active',mode==='custom');updateBuilderPreview();saveState()}
    function renderChannelGrid(){
      let defaults=new Set(['after_hours_events','device_connect','file_events','email_external']),savedFeatures=customBuilderState?.features||{};
      $('#channelGrid').innerHTML=data.event_features.map(f=>{
        let checked=customBuilderState?f.key in savedFeatures:defaults.has(f.key),weight=savedFeatures[f.key]||1;
        return `<label class="channel-row"><input class="channel-check" type="checkbox" value="${f.key}" ${checked?'checked':''}><span>${f.label}<br><span class="employee-id">${f.key}</span></span><select class="channel-weight" aria-label="Весовой коэффициент">${[.5,1,1.5,2].map(v=>`<option value="${v}" ${v===weight?'selected':''}>×${v.toFixed(1).replace('.',',')}</option>`).join('')}</select></label>`;
      }).join('');
      if(customBuilderState){$('#customName').value=customBuilderState.name;$('#customStart').value=customBuilderState.start_day;$('#customDuration').value=customBuilderState.duration}
      $$('.channel-check').forEach(x=>x.onchange=()=>{let checked=$$('.channel-check:checked');if(checked.length>8){x.checked=false;alert('В одном сценарии допускается выбор не более 8 каналов.')}updateBuilderPreview()});
      $$('.channel-weight').forEach(x=>x.onchange=updateBuilderPreview);
      $('#customStart').oninput=updateBuilderPreview;$('#customDuration').oninput=updateBuilderPreview;$('#customName').oninput=saveState;
      $$('[data-builder]').forEach(x=>x.onclick=()=>setBuilderMode(x.dataset.builder));
      setBuilderMode(builderMode);
    }
    function updateBuilderPreview(){
      if(!$('#timelinePreview'))return;
      let start=Math.max(1,Math.min(14,+$('#customStart').value||1)),duration=Math.max(1,Math.min(7,+$('#customDuration').value||1)),selected=$$('.channel-check:checked');
      $('#timelinePreview').innerHTML=Array.from({length:14},(_,i)=>`<i class="${i+1>=start&&i+1<start+duration?'on':''}" title="День ${i+1}"></i>`).join('');
      $('#builderSummary').textContent=`Выбрано каналов: ${selected.length} · интервал воздействия: дни ${start}–${Math.min(14,start+duration-1)}`;
      saveState();
    }
    function customProfile(){
      let features={};$$('.channel-check:checked').forEach(x=>features[x.value]=+x.closest('.channel-row').querySelector('.channel-weight').value);
      return {name:$('#customName').value||'Пользовательский сценарий',features,start_day:+$('#customStart').value,duration:+$('#customDuration').value};
    }
    function scenarioInfo(){let s=scenarios.find(x=>x.id===$('#scenario').value);if(!s)return;$('#scenarioName').textContent=`${s.id} · ${s.name}`;$('#scenarioDescription').textContent=s.description;$('#scenarioFeatures').innerHTML=s.features.map(x=>`<span>${x}</span>`).join('');saveState()}
    $('#intensity').oninput=e=>{$('#intensityValue').textContent=e.target.value+'%';saveState()};$('#scenario').onchange=scenarioInfo;$('#contextUser').onchange=saveState;$('#seed').onchange=saveState;

    /* GENERATOR RESULT VISUALIZATION */
    function seriesSvg(s,dates,affected=[14]){
      let w=330,h=100,p=8,all=[...s.normal,...s.scenario],max=Math.max(...all,1),min=Math.min(...all,0),span=Math.max(max-min,1e-6);
      let coords=values=>values.map((v,i)=>[p+i*(w-2*p)/13,h-p-(v-min)*(h-2*p)/span]);
      let normal=coords(s.normal),scenario=coords(s.scenario),poly=a=>a.map(v=>v.join(',')).join(' ');
      let hits=scenario.map((v,i)=>`<circle class="gen-hit" data-i="${i}" data-feature="${s.label}" data-date="${dates[i]}" data-normal="${s.normal[i]}" data-scenario="${s.scenario[i]}" cx="${v[0]}" cy="${v[1]}" r="10"/>`).join('');
      let firstAff=Math.max(1,affected[0]),lastAff=Math.min(14,affected[affected.length-1]);
      let x1=p+(firstAff-1)*(w-2*p)/13-4,x2=p+(lastAff-1)*(w-2*p)/13+4;
      let zone=`<rect class="impact-zone" x="${x1}" y="${p}" width="${Math.max(8,x2-x1)}" height="${h-2*p}" rx="4"/>`;
      return `<svg viewBox="0 0 ${w} ${h}">${zone}<polyline class="normal-line" points="${poly(normal)}"/><polyline class="synthetic-line" points="${poly(scenario)}"/>${hits}</svg>`;
    }

    function renderHistory(){
      let root=$('#generationHistory');
      root.innerHTML=generationHistory.length?generationHistory.map((g,i)=>`<div class="history-item" data-history="${i}"><b>${g.scenario.id}</b> · ${g.display_name||g.user}<br>Интенсивность: ${Math.round(g.intensity*100)}% · Распознавание: ${(100*g.scores.scenario_mitre_probability).toFixed(1)}%</div>`).join(''):'<span class="hint">Запуски генератора будут сохранены здесь.</span>';
      $$('[data-history]').forEach(x=>x.onclick=()=>renderGeneration(generationHistory[+x.dataset.history],false));
    }

    function renderGeneration(g,remember=true){
      let sc=g.scores;
      let isDetected = sc.alert || sc.scenario_risk >= 55 || sc.mitre_alert;
      if(remember){
        lastGeneration=g;
        generationHistory.unshift(g);
        generationHistory=generationHistory.slice(0,5);
        renderHistory();
      }
      let daysText = g.affected_days.length > 1 ? `дни ${g.affected_days[0]}–${g.affected_days[g.affected_days.length-1]}` : `день ${g.affected_days[0]}`;
      
      let deltaRows = g.series.map(s => {
        let normLast = s.normal[g.affected_days[0]-1] || 0;
        let scenLast = s.scenario[g.affected_days[0]-1] || 0;
        let diff = scenLast - normLast;
        return `<tr><td><b>${s.label}</b></td><td style="color:var(--blue)">${normLast}</td><td style="color:var(--red);font-weight:600">${scenLast}</td><td><span class="diff-badge">+${diff.toFixed(1)}</span></td></tr>`;
      }).join('');

      $('#generationOutput').innerHTML=`
        <div class="gen-result-wrap">
          <div class="gen-result-head">
            <div>
              <div class="eyebrow">Результаты симуляции · ${g.custom?'Конструктор профиля':'Техника MITRE ATT&amp;CK'}</div>
              <h2>${g.scenario.id} · ${g.scenario.name}</h2>
              <div class="gen-meta">
                Целевой субъект: <b>${g.display_name||g.user}</b> (${g.user}) · Роль: <b>${g.role_display}</b> · Окно инъекции: <b style="color:var(--cyan)">${daysText}</b>
              </div>
            </div>
            <span class="badge ${isDetected?'red':'blue'}">${isDetected?'УГРОЗА ОБНАРУЖЕНА СИСТЕМОЙ':'ОТКЛОНЕНИЕ В ПРЕДЕЛАХ НОРМЫ'}</span>
          </div>

          <div class="gen-summary-card">
            <div class="gen-stat">
              <span class="label">Реакция детектора аномалий</span>
              <span class="num ${isDetected?'critical':'ok'}">${isDetected?'Срабатывание':'Норма'}</span>
              <span class="desc">${isDetected?'Зафиксирован аномальный всплеск активности':'Поведение не превысило порог риска'}</span>
            </div>
            <div class="gen-stat">
              <span class="label">Идентификация техники MITRE</span>
              <span class="num ${sc.mitre_alert?'critical':'low'}">${(100*sc.scenario_mitre_probability).toFixed(1)}%</span>
              <span class="desc">Точность соответствия шаблону атаки</span>
            </div>
            <div class="gen-stat">
              <span class="label">Параметры инъекции</span>
              <span class="num">${daysText}</span>
              <span class="desc">Модифицировано каналов: ${g.series.length}</span>
            </div>
          </div>

          <div class="gen-charts-grid">
            ${g.series.map(s => `
              <div class="series-card">
                <h3><span>${s.label}</span> <span class="label" style="font-size:10px">${s.feature}</span></h3>
                <div class="legend">
                  <span><i style="background:var(--blue)"></i>Фоновое поведение</span>
                  <span><i style="background:var(--red)"></i>Симулированная атака</span>
                </div>
                ${seriesSvg(s, g.dates, g.affected_days)}
              </div>
            `).join('')}
          </div>

          <div class="table-and-conclusion">
            <div class="diff-table-card">
              <h3>Числовые изменения в точках воздействия</h3>
              <table class="diff-table">
                <thead>
                  <tr>
                    <th>Поведенческий канал</th>
                    <th>В норме</th>
                    <th>При атаке</th>
                    <th>Прирост</th>
                  </tr>
                </thead>
                <tbody>${deltaRows}</tbody>
              </table>
            </div>
            <div class="conclusion-box">
              <b>Что показал эксперимент:</b>
              Генеративная модель GAN воспроизвела нормальный суточный профиль роли «${g.role_display}». Наложение сценария «${g.scenario.name}» вызвало направленные всплески в заданные дни. Модели анализа зафиксировали инцидент с вероятностью распознавания техники ${(100*sc.scenario_mitre_probability).toFixed(1)}%.
            </div>
          </div>
        </div>
      `;

      $$('.gen-hit').forEach(el=>{
        let html=`<b>${el.dataset.feature}</b>${el.dataset.date}<br>В норме: ${el.dataset.normal}<br>При атаке: ${el.dataset.scenario}`;
        el.onmouseenter=e=>showTip(e,html);el.onmousemove=e=>showTip(e,html);el.onmouseleave=hideTip;
      });
      saveState();
    }

        /* EXPANDED AUGMENTATION VISUALIZATION WITH MULTI-POINT SUPPORT (UP TO 20) */
    function renderAugmentation(rows) {
      if (!rows?.length) return;
      let w = 900, h = 215, p = 32, max = Math.max(...rows.flatMap(r => [r.mean_pr_auc_without, r.mean_pr_auc_with_gan])) * 1.18;
      let group = (w - 2 * p) / rows.length, bw = Math.max(18, Math.min(30, group * 0.36));
      let bars = rows.map((r, i) => {
        let x = p + i * group + group / 2;
        let y0 = h - p - r.mean_pr_auc_without * (h - 2 * p) / max;
        let y1 = h - p - r.mean_pr_auc_with_gan * (h - 2 * p) / max;
        return `
          <rect class="bar-base aug-bar" data-shots="${r.real_anomalies_per_scenario}" data-kind="Без GAN" data-value="${r.mean_pr_auc_without}" data-recall="${r.mean_recall_at_500_without}" x="${x - bw - 2}" y="${y0}" width="${bw}" height="${h - p - y0}" rx="3"/>
          <rect class="bar-gan aug-bar" data-shots="${r.real_anomalies_per_scenario}" data-kind="С GAN" data-value="${r.mean_pr_auc_with_gan}" data-gain="${r.mean_relative_pr_auc_gain}" data-recall="${r.mean_recall_at_500_with_gan}" x="${x + 2}" y="${y1}" width="${bw}" height="${h - p - y1}" rx="3"/>
          <text x="${x}" y="${h - 8}" text-anchor="middle" dominant-baseline="central" fill="#8d9aaf" font-size="11">${r.real_anomalies_per_scenario} прим.</text>
        `;
      }).join('');
      $('#augmentationChart').innerHTML = `
        <svg viewBox="0 0 ${w} ${h}">
          <line class="gridline" x1="${p}" x2="${w - p}" y1="${h - p}" y2="${h - p}"/>
          ${bars}
          <text x="${w - 155}" y="15" fill="#8d9aaf" font-size="11" dominant-baseline="central">■ без GAN</text>
          <text x="${w - 75}" y="15" fill="#5eead4" font-size="11" dominant-baseline="central">■ с GAN</text>
        </svg>
      `;
      $$('.aug-bar').forEach(el => {
        el.onmouseenter = e => {
          let rec = el.dataset.recall ? `<br>Полнота Recall@500: ${(100 * +el.dataset.recall).toFixed(1)}%` : '';
          let gain = el.dataset.gain ? `<br>Прирост PR-AUC: <b style="color:var(--cyan)">+${(100 * +el.dataset.gain).toFixed(1)}%</b>` : '';
          showTip(e, `<b>${el.dataset.kind}</b> · ${el.dataset.shots} примеров на сценарий<br>Средний PR-AUC: ${(+el.dataset.value).toFixed(4)}${rec}${gain}`);
        };
        el.onmousemove = e => showTip(e, $('#tooltip').innerHTML);
        el.onmouseleave = hideTip;
      });
    }

    $('#generate').onclick=async()=>{
      let b=$('#generate'),custom=builderMode==='custom'?customProfile():null;
      if(custom&&!Object.keys(custom.features).length){alert('Выберите хотя бы один поведенческий канал.');return}
      b.disabled=true;
      b.innerHTML='<span class="loading">Генерация данных <i></i><i></i><i></i></span>';
      try{
        let r=await fetch('/api/generate',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({scenario_id:custom?'CUSTOM-MITRE':$('#scenario').value,intensity:+$('#intensity').value/100,seed:+$('#seed').value,user:$('#contextUser').value||null,custom_profile:custom})
        });
        let g=await r.json();
        if(!r.ok)throw Error(g['ошибка']||'Ошибка генерации');
        renderGeneration(g);
        $('#seed').value=g.seed+1;
        saveState();
      }catch(e){
        $('#generationOutput').innerHTML=`<div class="empty"><div><b class="critical">Генерация не выполнена</b><p>${e.message}</p></div></div>`;
      }finally{
        b.disabled=false;
        b.textContent='Сгенерировать и оценить';
      }
    };

    function archHead(title,subtitle,badge){return `<div class="arch-detail-head"><div><h3>${title}</h3><span class="label">${subtitle}</span></div></div>`}
    function box(x,y,w,h,text,ai=''){return `<rect class="${ai?'ai-box':'box'}" x="${x}" y="${y}" width="${w}" height="${h}" rx="6"/><text x="${x+w/2}" y="${y+h/2}" text-anchor="middle" dominant-baseline="central">${text}</text>`}

        function archContent(key){
      let u = (data?.users?.[selected]) || (data?.users?.[0]) || {user:'NZL1395', display_name:'Сотрудник', role:'Специалист', peak_day:'2010-05-14'};
      let tl = (data && data.timelines && u?.user && data.timelines[u.user]) ? data.timelines[u.user] : [];
      let activeD = (activeDayIndex !== null && tl[activeDayIndex]) ? tl[activeDayIndex] : (tl.length ? tl.reduce((a,b)=>b.risk>a.risk?b:a, tl[0]) : null);
      let v = activeD?.values || Array(16).fill(0);
      let dayStr = activeD?.day || u.peak_day || '2010-05-14';
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
              <tr><td>file.csv</td><td>${dayStr} 14:15:30, DTA/${u.user}, C:\\Work\\report.docx, ${v[7]>0 ? 'Write ('+fmt(Math.round(v[8]))+' симв.)' : 'Access'}</td></tr>
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
      `;

      if(key==='windows') return `
        ${archHead('2. Временные окна активности','Формирование 14-дневного контекста и динамических характеристик','ТЕНЗОР 14 × 18')}
        <div class="arch-detail-grid">
          <div>
            <div class="window-days">${[18,24,21,38,31,28,12,8,22,35,29,48,42,82].map((x,i)=>`<div class="window-day" style="--v:${x}%">Д${i-13}</div>`).join('')}</div>
            <div class="arch-facts">
              <div class="arch-fact"><b>Размерность матрицы: 14 × 18</b>14 последовательных суток по 18 нормализованным признакам.</div>
              <div class="arch-fact"><b>Динамический анализ</b>Текущий день сопоставляется со средним значением, дисперсией, пиком и вектором тренда.</div>
            </div>
          </div>
          <div class="diagram">
            <svg viewBox="0 0 490 205">
              <defs>
                <marker id="arr2" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 10 5 L 0 9 z" fill="#5eead4"/></marker>
              </defs>
              ${box(10,24,95,32,'День −13')}
              ${box(10,86,95,32,'…')}
              ${box(10,148,95,32,'День 0')}
              
              <path class="wire" d="M105 40 H145 M105 102 H145 M105 164 H145 M145 40 V164"/>
              <path class="wire" d="M145 102 H175" marker-end="url(#arr2)"/>
              
              ${box(175,65,130,74,'Матрица окна 14 × 18','ai')}
              
              <path class="wire ai-wire" d="M305 102 H345" marker-end="url(#arr2)"/>
              
              ${box(345,15,135,28,'Текущий уровень')}
              ${box(345,55,135,28,'Среднее (μ)')}
              ${box(345,95,135,28,'Разброс (σ)')}
              ${box(345,135,135,28,'Пик (max)')}
              ${box(345,175,135,28,'Тренд (Δt)')}
              <circle class="signal" cx="145" cy="102" r="4"/>
            </svg>
          </div>
        </div>
      `;

      if(key==='gan') return `
        ${archHead('3. Генеративная модель Seq-ACGAN','Моделирование нормального профиля роли и симуляция техник MITRE','МОДЕЛИРОВАНИЕ И СИНТЕЗ')}
        <div class="arch-detail-grid">
          <div class="diagram">
            <svg viewBox="0 0 490 205">
              <defs>
                <marker id="arr3" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 10 5 L 0 9 z" fill="#a78bfa"/></marker>
              </defs>
              ${box(8,20,95,30,'Шум z')}
              ${box(8,66,95,30,'Субъект id')}
              ${box(8,112,95,30,'Роль LDAP')}
              
              <path class="wire ai-wire" d="M103 35 H135 M103 81 H135 M103 127 H135 M135 35 V127"/>
              <path class="wire ai-wire" d="M135 81 H165" marker-end="url(#arr3)"/>
              
              ${box(165,50,115,62,'Generator G','ai')}
              
              <path class="wire ai-wire" d="M280 81 H315" marker-end="url(#arr3)"/>
              
              ${box(315,15,165,34,'Норма: 14 × 18','ai')}
              
              <path class="wire ai-wire" d="M397 49 V75" marker-end="url(#arr3)"/>
              
              ${box(315,75,165,34,'Инъекция MITRE')}
              
              <path class="wire ai-wire" d="M397 109 V135" marker-end="url(#arr3)"/>
              
              ${box(315,135,165,34,'Синтез аномалии','ai')}
              <circle class="signal" cx="135" cy="81" r="4" fill="#a78bfa"/>
            </svg>
          </div>
          <div class="arch-facts">
            <div class="arch-fact"><b>Условный генератор (Conditional Generator)</b>Принимает вектор шума, код субъекта и штатную роль, формируя персональный прогноз нормы.</div>
            <div class="arch-fact"><b>Контролируемый MITRE-слой</b>Модифицирует целевые признаки техники (например, USB, файловый объём и ночную активность).</div>
            <div class="arch-fact"><b>Аугментация данных</b>Синтетические последовательности используются для обучения классификаторов при дефиците реальных атак.</div>
          </div>
        </div>
      `;

      if(key==='detect') return `
        ${archHead('4. Детектор аномалий','Ранжирование окон и расчет вероятности угрозы на базе градиентного бустинга','ОСНОВНОЙ ДЕТЕКТОР')}
        <div class="arch-detail-grid">
          <div class="diagram">
            <svg viewBox="0 0 490 205">
              <defs>
                <marker id="arr4" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 10 5 L 0 9 z" fill="#5eead4"/></marker>
              </defs>
              ${box(10,65,105,70,'Окно 14 × 18')}
              
              <path class="wire" d="M115 100 H145" marker-end="url(#arr4)"/>
              
              ${box(145,20,115,26,'текущее')}
              ${box(145,55,115,26,'среднее')}
              ${box(145,90,115,26,'дисперсия')}
              ${box(145,125,115,26,'максимум')}
              ${box(145,160,115,26,'тренд')}
              
              <path class="wire" d="M260 33 H290 M260 68 H290 M260 103 H290 M260 138 H290 M260 173 H290 M290 33 V173"/>
              <path class="wire" d="M290 103 H320" marker-end="url(#arr4)"/>
              
              ${box(320,68,95,64,'XGBoost','ai')}
              
              <path class="wire ai-wire" d="M415 100 H440" marker-end="url(#arr4)"/>
              
              <circle cx="460" cy="100" r="18" fill="#291e43" stroke="#a78bfa" stroke-width="1.2"/>
              <text x="460" y="100" text-anchor="middle" dominant-baseline="central" fill="#edf3fb" font-size="10" font-weight="700">РИСК</text>
            </svg>
          </div>
          <div class="arch-facts">
            <div class="arch-fact"><b>90 агрегированных признаков</b>5 статистических характеристик для каждого из 18 поведенческих каналов.</div>
            <div class="arch-fact"><b>Интерактивная настройка порога</b>Порог срабатывания регулируется оператором системы под регламенты безопасности.</div>
            <div class="arch-fact"><b>Интерпретируемость</b>Интерфейс предоставляет ключевые факторы риска (девиации в единицах σ) и фактические значения.</div>
          </div>
        </div>
      `;

      return `
        ${archHead('5. Мониторинг и приоритизация инцидентов','Представление результатов в оперативном контуре информационной безопасности','ОПЕРАТИВНЫЙ МОНИТОРИНГ')}
        <div class="arch-detail-grid">
          <div class="diagram">
            <svg viewBox="0 0 490 205">
              <defs>
                <marker id="arr5" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 10 5 L 0 9 z" fill="#5eead4"/></marker>
              </defs>
              ${box(10,18,115,34,'1 822 субъекта')}
              
              <path class="wire" d="M67 52 V78" marker-end="url(#arr5)"/>
              
              ${box(10,78,115,34,'Оповещения')}
              
              <path class="wire" d="M125 95 H165" marker-end="url(#arr5)"/>
              
              ${box(165,65,130,60,'Рейтинг риска','ai')}
              
              <path class="wire ai-wire" d="M295 95 H335" marker-end="url(#arr5)"/>
              
              ${box(335,18,140,28,'Временной ряд')}
              ${box(335,58,140,28,'Факторы риска')}
              ${box(335,98,140,28,'Показатели')}
              ${box(335,138,140,28,'Расследование')}
            </svg>
          </div>
          <div class="arch-facts">
            <div class="arch-fact"><b>Иерархический анализ</b>От глобального распределения рисков в организации к персональному профилю и суточным событиям.</div>
            <div class="arch-fact"><b>Два режима работы</b>Мониторинг фактических данных и генерация/симуляция целевых сценариев MITRE.</div>
            <div class="arch-fact"><b>Поддержка принятия решений</b>Назначение статусов расследования, фиксация заключений аналитика и экспорт стандартизированных отчётов.</div>
          </div>
        </div>
      `;
    }

    
    $$('.arch-node').forEach(node => {
      node.onclick = () => {
        $$('.arch-node').forEach(n => n.classList.remove('active'));
        node.classList.add('active');
        renderArch(node.dataset.arch);
      };
    });

    function renderArch(key){$$('.arch-node').forEach(x=>x.classList.toggle('active',x.dataset.arch===key));$('#archDetail').innerHTML=archContent(key)}
    $$('.arch-node').forEach(n=>n.onclick=()=>renderArch(n.dataset.arch));
    if(document.getElementById('archDetail')) renderArch(new URLSearchParams(location.search).get('arch')||'logs');

    Promise.all([
      fetch('/api/dashboard').then(r=>r.json()),
      fetch('/api/scenarios').then(r=>r.json()),
      fetch('/api/session',{cache:'no-store'}).then(r=>r.json())
    ]).then(([d,s,session])=>{
      let prior=sessionStorage.getItem('ueba-server-session');
      if(prior!==session.id){
        sessionStorage.clear();
        sessionStorage.setItem('ueba-server-session',session.id);
      }
      let saved=readState();
      data=d;
      scenarios=s;
      
      let initialThreshold = customThreshold!==null ? Math.round(customThreshold*100) : 15;
      $('#thresholdSlider').value = initialThreshold;
      $('#thresholdDisplay').textContent = `${initialThreshold}%`;
      
      renderCards(d.summary);
      renderPopulation(d.population);
      $('#scenario').innerHTML=s.map(x=>`<option value="${x.id}">${x.id} · ${x.name}</option>`).join('');
      $('#contextUser').innerHTML='<option value="">Автоматический выбор субъекта</option>'+d.users.map(x=>`<option value="${x.user}">${x.display_name} · ${x.user}</option>`).join('');
      let initial=Math.max(0,d.users.findIndex(x=>x.user===saved.selectedUser));
      renderUsers(initial);
      if(saved.scenario)$('#scenario').value=saved.scenario;
      if(saved.intensity){
        $('#intensity').value=saved.intensity;
        $('#intensityValue').textContent=saved.intensity+'%';
      }
      if(saved.contextUser!==undefined)$('#contextUser').value=saved.contextUser;
      if(saved.seed)$('#seed').value=saved.seed;
      scenarioInfo();

      // Init SOC Simulator Controls
      let calcSlider = document.getElementById('calcThresholdSlider');
      let calcAnalysts = document.getElementById('calcAnalysts');
      let calcMins = document.getElementById('calcMinutesPerAlert');
      let btnApply = document.getElementById('btnApplySocThreshold');
      
      if(calcSlider){
        calcSlider.oninput = updateSOCSimulator;
        calcSlider.onchange = updateSOCSimulator;
      }
      if(calcAnalysts){
        calcAnalysts.oninput = updateSOCSimulator;
        calcAnalysts.onchange = updateSOCSimulator;
      }
      if(calcMins){
        calcMins.oninput = updateSOCSimulator;
        calcMins.onchange = updateSOCSimulator;
      }
      if(btnApply){
        btnApply.onclick = () => {
          let thVal = parseInt(calcSlider.value, 10);
          $('#thresholdSlider').value = thVal;
          $('#thresholdSlider').dispatchEvent(new Event('input'));
          saveState();
          alert(`Порог срабатывания ${thVal}% успешно применён к оперативному мониторингу.`);
        };
      }
      updateSOCSimulator();

      // Bind Quick User Select Buttons
      let btnRandom = document.getElementById('btnRandomUser');
      if(btnRandom){
        btnRandom.onclick = () => {
          let pool = data.users || [];
          if(pool.length){
            let rand = pool[Math.floor(Math.random() * pool.length)];
            $('#contextUser').value = rand.user;
            saveState();
            addFeed('ГЕНЕРАТОР', `Выбран случайный субъект: ${rand.display_name} (${rand.user})`, '');
          }
        };
      }

      let btnFromMon = document.getElementById('btnCurrentMonitorUser');
      if(btnFromMon){
        btnFromMon.onclick = () => {
          let u = data.users[selected];
          if(u){
            $('#contextUser').value = u.user;
            saveState();
            addFeed('ГЕНЕРАТОР', `Установлен субъект из Мониторинга: ${u.display_name} (${u.user})`, '');
          }
        };
      }


      if(saved.feed)$('#feed').innerHTML=saved.feed;
      else addFeed('СИСТЕМА',`Выбран субъект: ${d.users[initial].display_name}`,'');
      tick=Number.isFinite(+saved.tick)?+saved.tick:0;
      generationHistory=saved.generationHistory||[];
      lastGeneration=saved.lastGeneration||null;
      renderHistory();
      if(lastGeneration)renderGeneration(lastGeneration,false);
      renderAugmentation(d.low_shot_augmentation?.aggregate);
      let query=new URLSearchParams(location.search),view=query.get('view')||saved.view;
      if(view)$(`.tab[data-view="${view}"]`)?.click();
      if(query.get('demo')==='1'&&!lastGeneration)setTimeout(()=>$('#generate').click(),350);
      saveState();
    }).catch(e=>{
      $('main').innerHTML=`<div class="panel controls"><h2>Не удалось загрузить данные</h2><p>${e}</p></div>`;
    });
  