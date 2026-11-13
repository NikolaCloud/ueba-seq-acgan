"""Inject term tips across all tabs in index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Monitoring table headers
content = content.replace(
    '<th>Субъект доступа</th><th>Пиковый риск</th><th>Оповещения</th><th>Инциденты</th>',
    '<th><span class="term-tip" data-term="Субъектов">Субъект доступа <i>ℹ</i></span></th><th><span class="term-tip" data-term="Пиковый риск">Пиковый риск <i>ℹ</i></span></th><th><span class="term-tip" data-term="Порог отсечки">Оповещения <i>ℹ</i></span></th><th><span class="term-tip" data-term="Инцидентов CERT">Инциденты <i>ℹ</i></span></th>'
)

# 2. Generator fields
content = content.replace(
    '<label>Сценарий угрозы (MITRE ATT&amp;CK)</label>',
    '<label><span class="term-tip" data-term="MITRE ATT&CK">Сценарий угрозы (MITRE ATT&amp;CK) <i>ℹ</i></span></label>'
)
content = content.replace(
    '<label>Интенсивность воздействия (масштаб): <b id="intensityValue">100%</b></label>',
    '<label><span class="term-tip" data-term="Интенсивность атаки">Интенсивность воздействия (масштаб): <i>ℹ</i></span> <b id="intensityValue">100%</b></label>'
)
content = content.replace(
    '<label>Случайный сид генератора</label>',
    '<label><span class="term-tip" data-term="Seed">Случайный сид генератора (Seed) <i>ℹ</i></span></label>'
)
content = content.replace(
    '<label style="margin-bottom:0">Целевой субъект (профиль роли)</label>',
    '<label style="margin-bottom:0"><span class="term-tip" data-term="LDAP-профиль">Целевой субъект (профиль роли) <i>ℹ</i></span></label>'
)

# 3. Quality & Metrics tab cards
content = content.replace(
    '<h2>Модель градиентного бустинга</h2>\n          <div class="metric ok">0,891</div>\n          <div class="label">PR-AUC на тестовой выборке</div>',
    '<h2><span class="term-tip" data-term="XGBoost">Модель градиентного бустинга (XGBoost) <i>ℹ</i></span></h2>\n          <div class="metric ok">0,891</div>\n          <div class="label"><span class="term-tip" data-term="PR-AUC">PR-AUC на тестовой выборке <i>ℹ</i></span></div>'
)
content = content.replace(
    '<h2>Полнота в Top-500 (Recall)</h2>\n          <div class="metric ok">88,8%</div>\n          <div class="label">Выявление инцидентов в топ-500</div>',
    '<h2><span class="term-tip" data-term="Recall">Полнота в Top-500 (Recall) <i>ℹ</i></span></h2>\n          <div class="metric ok">88,8%</div>\n          <div class="label"><span class="term-tip" data-term="Recall">Выявление инцидентов в топ-500 <i>ℹ</i></span></div>'
)
content = content.replace(
    '<h2>Прирост качества с GAN</h2>\n          <div class="metric ok">+104,8%</div>\n          <div class="label">Максимальный рост PR-AUC (Low-Shot)</div>',
    '<h2><span class="term-tip" data-term="Аугментация">Прирост качества с GAN <i>ℹ</i></span></h2>\n          <div class="metric ok">+104,8%</div>\n          <div class="label"><span class="term-tip" data-term="Аугментация">Максимальный рост PR-AUC (Low-Shot) <i>ℹ</i></span></div>'
)

# 4. Benchmark table headers
content = content.replace(
    '<th>Архитектура / Алгоритм</th>\n                <th>PR-AUC</th>\n                <th>Recall@500</th>\n                <th>Precision@100</th>\n                <th>Скорость инференса</th>\n                <th>Назначение в тракте</th>',
    '<th>Архитектура / Алгоритм</th>\n                <th><span class="term-tip" data-term="PR-AUC">PR-AUC <i>ℹ</i></span></th>\n                <th><span class="term-tip" data-term="Recall">Recall@500 <i>ℹ</i></span></th>\n                <th><span class="term-tip" data-term="Precision">Precision@100 <i>ℹ</i></span></th>\n                <th><span class="term-tip" data-term="Скорость инференса">Скорость инференса <i>ℹ</i></span></th>\n                <th>Назначение в тракте</th>'
)

# 5. Benchmark table model rows
content = content.replace(
    '<b>Модель градиентного бустинга (XGBoost)</b>',
    '<b class="term-tip" data-term="XGBoost">Модель градиентного бустинга (XGBoost) <i>ℹ</i></b>'
)
content = content.replace(
    '<b>Нейросетевой дискриминатор Seq-ACGAN</b>',
    '<b class="term-tip" data-term="Seq-ACGAN">Нейросетевой дискриминатор Seq-ACGAN <i>ℹ</i></b>'
)
content = content.replace(
    '<b>Генеративно-состязательный автоэнкодер (GANomaly)</b>',
    '<b class="term-tip" data-term="GANomaly">Генеративно-состязательный автоэнкодер (GANomaly) <i>ℹ</i></b>'
)
content = content.replace(
    '<b>Изоляционный лес (Isolation Forest)</b>',
    '<b class="term-tip" data-term="Isolation Forest">Изоляционный лес (Isolation Forest) <i>ℹ</i></b>'
)
content = content.replace(
    '<b>Одноклассовый метод опорных векторов (One-Class SVM)</b>',
    '<b class="term-tip" data-term="One-Class SVM">Одноклассовый метод опорных векторов (One-Class SVM) <i>ℹ</i></b>'
)

html_path.write_text(content, encoding="utf-8")
print("Term tooltips injected across all pages.")
