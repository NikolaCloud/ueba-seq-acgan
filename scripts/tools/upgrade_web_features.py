"""Complete upgrade script for web/index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update Generator Step 2 with Quick Selection Buttons
user_selector_html = """            <div class="field">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <label style="margin-bottom:0">Целевой субъект (профиль роли)</label>
                <div class="user-select-bar" style="margin-bottom:0">
                  <button type="button" class="user-select-btn" id="btnRandomUser" title="Выбрать случайного пользователя">🎲 Случайный</button>
                  <button type="button" class="user-select-btn" id="btnCurrentMonitorUser" title="Выбрать активного из мониторинга">👤 Из мониторинга</button>
                </div>
              </div>
              <select id="contextUser">
                <option value="">Автоматический выбор субъекта (случайный)</option>
              </select>
            </div>"""

if '<button type="button" class="user-select-btn" id="btnRandomUser"' not in content:
    content = content.replace(
        """            <div class="field">
              <label>Целевой субъект (профиль роли)</label>
              <select id="contextUser">
                <option value="">Автоматический выбор субъекта</option>
              </select>
            </div>""",
        user_selector_html
    )

# 2. Add SOC Simulator Card on Quality Metrics Tab
soc_calculator_html = """
        <!-- SOC LOAD & BUDGET SIMULATOR -->
        <div class="panel soc-calc-card" style="grid-column:1/-1">
          <div class="panel-title" style="padding:0 0 12px">
            <div>
              <h2>Калькулятор порога отсечки и симулятор нагрузки SOC</h2>
              <span class="label">Оптимизация баланса между полнотой выявления угроз и пропускной способностью аналитиков</span>
            </div>
            <span class="metric-chip">Калибровка детектора</span>
          </div>
          
          <div class="soc-calc-grid">
            <div class="soc-calc-controls">
              <div>
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                  <span class="term-tip" data-term="Порог отсечки">Порог срабатывания детектора (риск): <i>ℹ</i></span>
                  <b id="calcThresholdVal" style="color:var(--cyan);font-size:14px">15%</b>
                </div>
                <input type="range" id="calcThresholdSlider" min="5" max="85" value="15" step="1" style="width:100%;accent-color:var(--cyan);cursor:pointer">
                <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-top:2px">
                  <span>5% (Максимальная полнота)</span>
                  <span>15% (Рекомендованный)</span>
                  <span>85% (Только критические)</span>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div class="field" style="margin-bottom:0">
                  <label>Аналитиков в смене (чел.):</label>
                  <input type="number" id="calcAnalysts" min="1" max="20" value="2">
                </div>
                <div class="field" style="margin-bottom:0">
                  <label>Время на 1 инцидент (мин.):</label>
                  <input type="number" id="calcMinutesPerAlert" min="5" max="60" value="15">
                </div>
              </div>
            </div>

            <div class="soc-calc-stats">
              <div class="soc-stat-box">
                <span class="label">Оповещений в сутки</span>
                <div class="val" id="calcAlertsDay" style="color:var(--cyan)">16,8</div>
                <span class="desc">в среднем на всю организацию</span>
              </div>
              <div class="soc-stat-box">
                <span class="label">Загрузка аналитиков</span>
                <div class="val" id="calcShiftLoad" style="color:var(--green)">26,2%</div>
                <span class="desc" id="calcShiftHours">4,2 ч / смену</span>
              </div>
              <div class="soc-stat-box">
                <span class="label">Точность (Precision)</span>
                <div class="val" id="calcPrecision" style="color:var(--blue)">98,4%</div>
                <span class="desc">истинных атак в очереди</span>
              </div>
              <div class="soc-stat-box">
                <span class="label">Полнота (Recall)</span>
                <div class="val" id="calcRecall" style="color:var(--green)">71,2%</div>
                <span class="desc">обнаружение скрытых угроз</span>
              </div>
              <div class="soc-status-badge ok" id="calcStatusBadge">
                <span>✓ Оптимальный баланс: нагрузка аналитиков находится в комфортной зеленой зоне.</span>
              </div>
            </div>
          </div>
        </div>
"""

if '<!-- SOC LOAD & BUDGET SIMULATOR -->' not in content:
    content = content.replace('<!-- BENCHMARK TABLE OF MODELS -->', soc_calculator_html + '\n        <!-- BENCHMARK TABLE OF MODELS -->')

# 3. Enhance Architecture Flow Diagram with Pulse Track
arch_flow_new = """          <div class="arch-flow">
            <div class="arch-flow-track"><div class="arch-pulse-beam"></div></div>
            <div class="arch-node active" data-arch="logs">
              <span class="arch-icon">▦</span>
              <b>1. Источники данных</b>
              <div class="label">Журналы событий и LDAP</div>
              <span class="arch-badge-tag arch-badge-cyan">Сбор телеметрии</span>
            </div>
            <div class="arch-node" data-arch="windows">
              <span class="arch-icon">◫</span>
              <b>2. Входные данные</b>
              <div class="label">Агрегаты скользящих 14 дней</div>
              <span class="arch-badge-tag arch-badge-cyan">Нормализация</span>
            </div>
            <div class="arch-node" data-arch="gan">
              <span class="arch-icon">◇</span>
              <b>3. Синтез угроз Seq-ACGAN</b>
              <div class="label">Генератор нормы + MITRE</div>
              <span class="arch-badge-tag arch-badge-purple">Аугментация +104%</span>
            </div>
            <div class="arch-node" data-arch="detect">
              <span class="arch-icon">◎</span>
              <b>4. Детектор аномалий</b>
              <div class="label">Бустинг XGBoost (90 признаков)</div>
              <span class="arch-badge-tag arch-badge-green">0,12 мс · PR-AUC 0,891</span>
            </div>
            <div class="arch-node" data-arch="ui">
              <span class="arch-icon">◉</span>
              <b>5. Контур SOC</b>
              <div class="label">Интерпретируемый ИИ и скоринг</div>
              <span class="arch-badge-tag arch-badge-cyan">Рейтинг 0-100</span>
            </div>
          </div>"""

if '<div class="arch-pulse-beam">' not in content:
    content = re.sub(r'<div class="arch-flow">.*?</div>\s*<div class="arch-detail"', arch_flow_new + '\n          <div class="arch-detail"', content, flags=re.DOTALL)

html_path.write_text(content, encoding="utf-8")
print("HTML layout updated successfully.")
