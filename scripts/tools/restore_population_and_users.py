"""Restore renderPopulation, renderUsers, selectUser, renderUserRows, applyRiskFilter."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

functions_to_insert = """
    function riskBandName(n){return n>=80?'Критический':n>=55?'Высокий':n>=30?'Средний':'Низкий'}
    
    function applyRiskFilter(name){
      populationFilter=populationFilter===name?null:name;
      let users=populationFilter?data.users.filter(u=>riskBandName(u.peak_risk)===populationFilter):data.users;
      $$('.donut-segment,.legend-row').forEach(x=>x.classList.toggle('active',x.dataset.name===populationFilter));
      $('#riskFilterNote').textContent=populationFilter?`Фильтр «${populationFilter}»: ${users.length} субъектов в рейтинге · клик для сброса`:'Отображаются все категории риска';
      renderUserRows(users);
    }

    function renderPopulation(p){
      if(!p || !p.risk_distribution) return;
      let colors=['#34d399','#60a5fa','#fbbf24','#fb7185'],entries=Object.entries(p.risk_distribution),total=entries.reduce((a,x)=>a+x[1],0),offset=0;
      $('#donutSegments').innerHTML=entries.map((x,i)=>{
        let length=100*x[1]/total,html=`<circle class="donut-segment" tabindex="0" data-name="${x[0]}" data-value="${x[1]}" cx="60" cy="60" r="45" pathLength="100" stroke="${colors[i]}" stroke-dasharray="${length} ${100-length}" stroke-dashoffset="${-offset}"/>`;
        offset+=length;return html;
      }).join('');
      $('#donutCenter').innerHTML=`${fmt(total)}<small>субъектов</small>`;
      $('#riskLegend').innerHTML=entries.map((x,i)=>`<div class="legend-row" tabindex="0" data-name="${x[0]}" data-value="${x[1]}"><span><i style="background:${colors[i]}"></i>${x[0]}</span><b>${fmt(x[1])}</b></div>`).join('');
      
      let th=getActiveThreshold();
      let totalAlerts = Object.values(data.timelines).reduce((sum,tl)=>sum+tl.filter(pt=>(pt.risk/100)>=th).length,0);
      let usersWithAlerts = Object.values(data.timelines).filter(tl=>tl.some(pt=>(pt.risk/100)>=th)).length;

      let alerts=Object.entries(p.alert_distribution || {}),max=Math.max(...alerts.map(x=>x[1]), 1);
      $('#alertHistogram').innerHTML=alerts.map(x=>`<div class="mini-col"><div class="mini-bar" data-label="${x[0]} срабатываний" data-value="${x[1]}" style="height:${95*x[1]/max}px"></div><b>${x[1]}</b><br>${x[0]}</div>`).join('');
      $('#populationFacts').innerHTML=`
        <div class="score-box" style="padding:10px 12px;background:#0d131d;border:1px solid var(--line);border-radius:8px">
          <span class="label">Субъекты с превышением порога</span>
          <b style="font-size:20px;display:block">${fmt(usersWithAlerts)}</b>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
          <div class="score-box" style="padding:10px 12px;background:#0d131d;border:1px solid var(--line);border-radius:8px">
            <span class="label">Средний пик</span>
            <b style="font-size:18px;display:block">${p.mean_peak_risk || 0}</b>
          </div>
          <div class="score-box" style="padding:10px 12px;background:#0d131d;border:1px solid var(--line);border-radius:8px">
            <span class="label">Всего срабатываний</span>
            <b style="font-size:18px;display:block">${fmt(totalAlerts)}</b>
          </div>
        </div>
      `;
      $$('.donut-segment,.legend-row').forEach(el=>{
        let html=`<b>${el.dataset.name} риск</b>${fmt(+el.dataset.value)} субъектов · ${(100*el.dataset.value/total).toFixed(1)}%<br><span class="label">Нажмите для фильтрации рейтинга</span>`;
        el.onmouseenter=e=>showTip(e,html);el.onmousemove=e=>showTip(e,html);el.onmouseleave=hideTip;
        el.onclick=()=>applyRiskFilter(el.dataset.name);
        el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();applyRiskFilter(el.dataset.name)}};
      });
      $$('.mini-bar').forEach(el=>{
        let html=`<b>${el.dataset.label}</b>${fmt(+el.dataset.value)} субъектов`;
        el.onmouseenter=e=>showTip(e,html);el.onmousemove=e=>showTip(e,html);el.onmouseleave=hideTip;
      });
    }

    function renderUserRows(users){
      let th=getActiveThreshold();
      if($('#userCountBadge')) $('#userCountBadge').textContent = users.length;
      $('#users').innerHTML=users.map(u=>{
        let i=data.users.indexOf(u);
        let userAlerts = (data.timelines[u.user]||[]).filter(pt=>(pt.risk/100)>=th).length;
        return `<tr data-i="${i}" class="${u.peak_risk>=80?'danger':''}"><td><b class="employee-name">${u.display_name}</b><br><span class="employee-id">${u.user} · ${u.peak_day}</span></td><td class="risk ${riskClass(u.peak_risk)}">${u.peak_risk}</td><td>${userAlerts}</td><td>${u.observed_anomalies}</td></tr>`;
      }).join('')||'<tr><td colspan="4" class="label">В загруженном рейтинге нет записей этой категории</td></tr>';
      $$('#users tr[data-i]').forEach(r=>r.onclick=()=>selectUser(+r.dataset.i));
    }

    function renderUsers(initial=0){
      renderUserRows(data.users);
      selectUser(initial,false);
      renderArch($('.arch-node.active')?.dataset.arch||'logs');
    }

    function selectUser(i,clearFeed=true){
      selected=i;tick=0;
      let u=data.users[i],timeline=data.timelines[u.user],peak=timeline.reduce((best,x,j)=>x.risk>timeline[best].risk?j:best,0);
      let th=getActiveThreshold();
      let userAlerts = timeline.filter(pt=>(pt.risk/100)>=th).length;
      $$('#users tr').forEach(r=>r.classList.toggle('active',+r.dataset.i===i));
      $('#contextUser').value=u.user;
      activeDayIndex = peak;
      drawRisk(timeline,peak);
      renderEventDetail(timeline[peak],peak,timeline);
      $('#userSummary').innerHTML=`<span class="chip"><b>${u.display_name}</b> · ${u.user}</span><span class="chip">пик риска: <b>${u.peak_risk}/100</b></span><span class="chip">срабатываний: <b>${userAlerts}</b></span>`+u.drivers.map(d=>`<span class="chip">${d.feature}: <b>${d.relative_deviation.toFixed(2)}σ</b></span>`).join('');
      if(clearFeed){$('#feed').innerHTML='';addFeed('СИСТЕМА',`Выбран субъект: ${u.display_name}`,'')}
      saveState();
    }
"""

if 'function renderPopulation' not in content:
    content = content.replace('function caseKey(){', functions_to_insert + '\n\n    function caseKey(){')

html_path.write_text(content, encoding="utf-8")
print("Restored renderPopulation and all associated user functions.")
