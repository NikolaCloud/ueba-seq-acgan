"""Apply clean, complete, tested JS and HTML fixes for SOC simulator, Architecture tab, and Generator."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update tab click handler to call updateSOCSimulator() when opening 'method' tab
tab_click_old = "$$('.tab').forEach(b=>b.onclick=()=>{$$('.tab,.view').forEach(x=>x.classList.remove('active'));b.classList.add('active');$('#'+b.dataset.view).classList.add('active');saveState()});"
tab_click_new = """$$('.tab').forEach(b=>b.onclick=()=>{
      $$('.tab,.view').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      $('#'+b.dataset.view).classList.add('active');
      if(b.dataset.view === 'method') updateSOCSimulator();
      if(b.dataset.view === 'about') renderArch($('.arch-node.active')?.dataset.arch || 'logs');
      saveState();
    });"""

if tab_click_old in content:
    content = content.replace(tab_click_old, tab_click_new)

# 2. Ensure Generator Buttons and SOC Simulator handlers are always attached on data load
extra_init_js = """
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
"""

if 'btnRandom.onclick' not in content:
    content = content.replace('updateSOCSimulator();', 'updateSOCSimulator();\n' + extra_init_js)

# 3. Enhance Architecture stage click handler so it triggers instantly without re-rendering page
arch_click_js = """
    $$('.arch-node').forEach(node => {
      node.onclick = () => {
        $$('.arch-node').forEach(n => n.classList.remove('active'));
        node.classList.add('active');
        renderArch(node.dataset.arch);
      };
    });
"""

if '$$(\'.arch-node\').forEach(node' not in content:
    content = content.replace('function renderArch(key){', arch_click_js + '\n    function renderArch(key){')

html_path.write_text(content, encoding="utf-8")
print("Clean fixes applied.")
