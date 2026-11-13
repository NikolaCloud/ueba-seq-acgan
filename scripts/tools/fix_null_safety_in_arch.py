"""Fix data null safety in archContent and init script."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

old_arch_start = """    function archContent(key){
      let u = data?.users?.[selected] || data?.users?.[0] || {user:'NZL1395', display_name:'Сотрудник', role:'Специалист', peak_day:'2010-05-14'};
      let tl = u ? data.timelines[u.user] : [];
      let activeD = (activeDayIndex !== null && tl && tl[activeDayIndex]) ? tl[activeDayIndex] : (tl?.reduce((a,b)=>b.risk>a.risk?b:a, tl[0] || {values:Array(16).fill(0), day:u.peak_day||'2010-05-14'}));
      let v = activeD?.values || Array(16).fill(0);"""

new_arch_start = """    function archContent(key){
      let u = (data?.users?.[selected]) || (data?.users?.[0]) || {user:'NZL1395', display_name:'Сотрудник', role:'Специалист', peak_day:'2010-05-14'};
      let tl = (data && data.timelines && u?.user && data.timelines[u.user]) ? data.timelines[u.user] : [];
      let activeD = (activeDayIndex !== null && tl[activeDayIndex]) ? tl[activeDayIndex] : (tl.length ? tl.reduce((a,b)=>b.risk>a.risk?b:a, tl[0]) : null);
      let v = activeD?.values || Array(16).fill(0);
      let dayStr = activeD?.day || u.peak_day || '2010-05-14';"""

content = content.replace(old_arch_start, new_arch_start)

# Also ensure top-level renderArch call does not crash before data
old_init_arch = "    $$('.arch-node').forEach(n=>n.onclick=()=>renderArch(n.dataset.arch));renderArch(new URLSearchParams(location.search).get('arch')||'logs');"
new_init_arch = "    $$('.arch-node').forEach(n=>n.onclick=()=>renderArch(n.dataset.arch));\n    if(document.getElementById('archDetail')) renderArch(new URLSearchParams(location.search).get('arch')||'logs');"

content = content.replace(old_init_arch, new_init_arch)

html_path.write_text(content, encoding="utf-8")
print("Null safety in archContent fixed successfully.")
