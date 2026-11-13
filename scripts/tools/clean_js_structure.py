"""Clean up and ensure 100% robust JavaScript execution in index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# Clean tab click handler
bad_tab_block = """    $$('.tab').forEach(b=>b.onclick=()=>{
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
    });"""

clean_tab_block = """    $$('.tab').forEach(b=>b.onclick=()=>{
      $$('.tab,.view').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      let targetView = $('#' + b.dataset.view);
      if(targetView) targetView.classList.add('active');
      if(b.dataset.view === 'method') updateSOCSimulator();
      if(b.dataset.view === 'about') renderArch($('.arch-node.active')?.dataset.arch || 'logs');
      saveState();
    });"""

if bad_tab_block in content:
    content = content.replace(bad_tab_block, clean_tab_block)

html_path.write_text(content, encoding="utf-8")
print("Cleaned up JS structure.")
