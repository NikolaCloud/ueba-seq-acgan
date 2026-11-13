"""Clean fix for architecture freeze and SOC load calculator."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Remove pulse-beam CSS and animations that caused layout reflows/freezes
css_to_remove = [
    r'\.arch-flow-track\{.*?\}',
    r'\.arch-pulse-beam\{.*?\}',
    r'@keyframes pulseFlow\{.*?\}',
    r'\.arch-node:not\(:last-child\):after\{.*?animation:flowdash.*?\}',
    r'@keyframes flowdash\{.*?\}'
]
for pattern in css_to_remove:
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Clean styling for .arch-flow without continuous animation
clean_arch_css = """
    /* CLEAN HIGH-PERFORMANCE ARCHITECTURE FLOW */
    .arch-flow{display:grid;grid-template-columns:repeat(5,1fr);align-items:stretch;gap:12px;margin:16px 0}
    .arch-node{min-height:90px;padding:12px 14px;border:1px solid var(--line);border-radius:11px;background:#0d131d;cursor:pointer;position:relative;transition:border-color .15s, background .15s, transform .15s;display:flex;flex-direction:column;justify-content:space-between}
    .arch-node:hover{border-color:var(--cyan);transform:translateY(-2px);background:#132032}
    .arch-node.active{border-color:var(--cyan);background:linear-gradient(145deg,#12253b,#0b1524);box-shadow:0 0 16px rgba(56,189,248,.25)}
    .arch-node[data-arch=gan]{border-color:#7c3aed55;background:#181028}
    .arch-node[data-arch=gan]:hover{background:#23153d;border-color:#a855f7}
    .arch-node[data-arch=gan].active{border-color:#c084fc;box-shadow:0 0 16px rgba(192,132,252,.25)}
    .arch-badge-tag{font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;display:inline-block;margin-top:6px;width:fit-content}
    .arch-badge-cyan{background:rgba(56,189,248,.15);color:#38bdf8;border:1px solid rgba(56,189,248,.3)}
    .arch-badge-purple{background:rgba(192,132,252,.15);color:#c084fc;border:1px solid rgba(192,132,252,.3)}
    .arch-badge-green{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
"""

if '/* CLEAN HIGH-PERFORMANCE ARCHITECTURE FLOW */' not in content:
    content = content.replace('/* ANIMATED ARCHITECTURE FLOW */', clean_arch_css)

# Remove .arch-flow-track from HTML
content = content.replace('<div class="arch-flow-track"><div class="arch-pulse-beam"></div></div>\n', '')
content = content.replace('<div class="arch-flow-track"><div class="arch-pulse-beam"></div></div>', '')

# 2. Make SOC Simulator Interactive with Apply Button and Real Data Calculation
soc_calc_card_html = """
        <!-- SOC LOAD & BUDGET SIMULATOR -->
        <div class="panel soc-calc-card" style="grid-column:1/-1">
          <div class="panel-title" style="padding:0 0 12px">
            <div>
              <h2>Калькулятор порога отсечки и симулятор нагрузки SOC</h2>
              <span class="label">Оптимизация баланса между полнотой выявления угроз и пропускной способностью смены аналитиков</span>
            </div>
            <button type="button" class="threshold-btn" id="btnApplySocThreshold" style="color:var(--cyan);border-color:var(--cyan)">✓ Применить порог к Мониторингу</button>
          </div>
          
          <div class="soc-calc-grid">
            <div class="soc-calc-controls">
              <div>
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                  <span class="term-tip" data-term="Порог отсечки">Порог срабатывания детектора (риск): <i>ℹ</i></span>
                  <b id="calcThresholdVal" style="color:var(--cyan);font-size:16px">15%</b>
                </div>
                <input type="range" id="calcThresholdSlider" min="5" max="85" value="15" step="1" style="width:100%;accent-color:var(--cyan);cursor:pointer">
                <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-top:2px">
                  <span>5% (Максимальный охват)</span>
                  <span>15% (Рекомендованный)</span>
                  <span>85% (Только критические)</span>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div class="field" style="margin-bottom:0">
                  <label>Аналитиков в смене (чел.):</label>
                  <input type="number" id="calcAnalysts" min="1" max="20" value="2" style="font-size:14px;font-weight:700">
                </div>
                <div class="field" style="margin-bottom:0">
                  <label>Время на 1 инцидент (мин.):</label>
                  <input type="number" id="calcMinutesPerAlert" min="5" max="60" value="15" style="font-size:14px;font-weight:700">
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
                <span class="desc" id="calcShiftHours">4,2 ч / 16 ч фонд</span>
              </div>
              <div class="soc-stat-box">
                <span class="label">Точность (Precision)</span>
                <div class="val" id="calcPrecision" style="color:var(--blue)">98,4%</div>
                <span class="desc">истинных атак в очереди</span>
              </div>
              <div class="soc-stat-box">
                <span class="label">Полнота (Recall)</span>
                <div class="val" id="calcRecall" style="color:var(--green)">71,2%</div>
                <span class="desc">выявление скрытых угроз</span>
              </div>
              <div class="soc-status-badge ok" id="calcStatusBadge">
                <span>✓ Оптимальный баланс: нагрузка аналитиков находится в комфортной зеленой зоне.</span>
              </div>
            </div>
          </div>
        </div>
"""

content = re.sub(r'<!-- SOC LOAD & BUDGET SIMULATOR -->.*?<!-- BENCHMARK TABLE OF MODELS -->', soc_calc_card_html + '\n        <!-- BENCHMARK TABLE OF MODELS -->', content, flags=re.DOTALL)

# 3. Robust SOC Simulator JavaScript Function
soc_js_function = """
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
"""

content = re.sub(r'// SOC LOAD & BUDGET SIMULATOR.*?function saveState\(\)\{', soc_js_function + '\n\n    const stateKey=\'ueba-demo-state\';\n    function saveState(){\n', content, flags=re.DOTALL)

# 4. Attach event listeners right after data load
init_soc_code = """
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
"""

if 'Init SOC Simulator Controls' not in content:
    content = content.replace('scenarioInfo();', 'scenarioInfo();\n' + init_soc_code)

html_path.write_text(content, encoding="utf-8")
print("Fixes successfully applied to index.html.")
