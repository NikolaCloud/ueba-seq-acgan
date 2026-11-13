"""Restore compact, sleek timeline strip and eliminate all overlapping CSS."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Clean the entire CSS from <style> to </style>
# Let's inspect the entire head/style block and make it clean and non-redundant.

clean_style = """  <style>
    :root{color-scheme:dark;--bg:#070a10;--panel:#111722;--panel2:#161e2b;--line:#263145;--text:#edf3fb;--muted:#8d9aaf;--cyan:#5eead4;--blue:#60a5fa;--amber:#fbbf24;--red:#fb7185;--green:#34d399}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% -10%,#15354a 0,transparent 30%),radial-gradient(circle at 95% 10%,#25183f 0,transparent 25%),var(--bg);color:var(--text);font:14px/1.45 Inter,"Segoe UI",sans-serif;min-height:100vh}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;background:linear-gradient(transparent 95%,rgba(94,234,212,.025) 95%);background-size:100% 5px;z-index:10}
    header,main{width:min(1380px,95vw);margin:auto}header{padding:22px 0 14px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:14px}
    
    /* ANIMATED LOGO */
    .logo{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;position:relative;flex:none;cursor:pointer;transition:transform .3s ease,filter .3s ease}
    .logo:hover{transform:scale(1.06);filter:drop-shadow(0 0 16px rgba(94,234,212,.45))}
    .logo-svg{width:44px;height:44px;display:block}
    .logo-frame{transition:stroke .3s ease}
    .logo-spin-ring{transform-origin:22px 22px;animation:logoSpinReverse 10s linear infinite}
    .logo-radar{transform-origin:22px 22px;animation:logoRadarSpin 2.8s linear infinite}
    .logo-core{transform-origin:22px 22px;animation:logoCorePulse 2s ease-in-out infinite alternate}
    .logo-ripple{transform-origin:22px 22px;animation:logoRipple 2.4s ease-out infinite}
    .logo-dot{animation:pulse 1.2s infinite}
    @keyframes logoRadarSpin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
    @keyframes logoSpinReverse{0%{transform:rotate(360deg)}100%{transform:rotate(0deg)}}
    @keyframes logoCorePulse{0%{transform:scale(.85);fill:#5eead4}50%{transform:scale(1.15);fill:#60a5fa}100%{transform:scale(.85);fill:#a78bfa}}
    @keyframes logoRipple{0%{r:6px;opacity:.8}70%{r:16px;opacity:.15}100%{r:18px;opacity:0}}

    .eyebrow{color:var(--cyan);font-size:10px;letter-spacing:.14em;text-transform:uppercase}h1{font-size:20px;margin:2px 0 0;font-weight:700}
    nav{display:flex;gap:5px;border-bottom:1px solid var(--line);margin-bottom:16px}.tab{border:0;background:transparent;color:var(--muted);padding:11px 16px;cursor:pointer;border-bottom:2px solid transparent;font:inherit;font-weight:500;transition:.15s}.tab:hover{color:var(--text)}.tab.active{color:var(--cyan);border-color:var(--cyan)}
    .view{display:none;animation:enter .3s ease}.view.active{display:block}
    
    /* TERM TOOLTIPS - CLEAN INLINE TEXT */
    .term-tip{display:inline;border-bottom:1px dashed rgba(94,234,212,.6);cursor:help;white-space:normal;transition:color .15s,border-color .15s}
    .term-tip:hover{color:var(--cyan);border-bottom-color:var(--cyan)}
    .term-tip i{font-style:normal;font-size:9px;background:#1e293b;color:var(--cyan);border-radius:3px;padding:1px 4px;margin-left:3px;vertical-align:1px;display:inline-block;line-height:1.2}

    /* COMPACT SLEEK TIMELINE STRIP */
    .timeline-strip-wrap{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:6px;padding:4px 2px 2px;border-top:1px solid rgba(255,255,255,.05)}
    .timeline-strip{display:flex;gap:4px;align-items:center}
    .day-cell{width:15px;height:16px;border-radius:3px;background:#182232;border:1px solid #27374e;cursor:pointer;position:relative;transition:all .15s ease}
    .day-cell:hover{transform:scale(1.25);border-color:var(--cyan);box-shadow:0 0 8px rgba(94,234,212,.5);z-index:10}
    .day-cell.active-day{border-color:#ffffff;box-shadow:0 0 10px var(--cyan);transform:scale(1.2);background:#22334a;z-index:9}
    .day-cell.critical{background:#fb7185;border-color:#fda4af}
    .day-cell.high{background:#f59e0b;border-color:#fbbf24}
    .day-cell.medium{background:#3b82f6;border-color:#60a5fa}
    .day-cell.low{background:#0f766e;border-color:#14b8a6}

    /* THRESHOLD CONTROL BAR */
    .threshold-bar{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
    .threshold-info{display:flex;align-items:center;gap:10px;font-size:12px}
    .threshold-info b{color:var(--text);font-size:13px}
    .threshold-val{color:var(--cyan);font-weight:700;font-size:13px;padding:2px 8px;border-radius:6px;background:#5eead412;border:1px solid #5eead433}
    .threshold-controls{display:flex;align-items:center;gap:12px}
    .threshold-controls input[type=range]{width:160px;accent-color:var(--cyan);cursor:pointer}
    .threshold-btn{padding:5px 10px;font-size:11px;background:#1b2636;color:var(--muted);border:1px solid #334158;border-radius:6px;cursor:pointer}
    .threshold-btn:hover{color:var(--text);border-color:var(--cyan)}

    .cards{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px}.card,.panel{background:linear-gradient(145deg,rgba(22,30,43,.94),rgba(13,18,27,.94));border:1px solid var(--line);border-radius:13px;box-shadow:0 16px 45px #0004}.card{padding:14px 16px;position:relative;overflow:hidden}.card:after{content:"";position:absolute;width:55px;height:2px;right:12px;top:13px;background:linear-gradient(90deg,transparent,var(--cyan));opacity:.6}.label{color:var(--muted);font-size:11px}.value{font-size:24px;font-weight:700;margin-top:4px;font-variant-numeric:tabular-nums}.delta{color:var(--green);font-size:11px}
    
    .grid{display:grid;grid-template-columns:minmax(560px,1.45fr) minmax(350px,.8fr);gap:12px;padding-bottom:30px;align-items:stretch}
    .grid-left{display:flex;flex-direction:column;gap:12px}
    
    .panel-title{padding:13px 17px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:10px;flex:0 0 auto}.panel-title h2{font-size:14px;margin:0;font-weight:600}.toolbar{display:flex;gap:7px;align-items:center}button,select,input{font:inherit}button{background:#1b2636;color:var(--text);border:1px solid #334158;border-radius:8px;padding:8px 12px;cursor:pointer;transition:.15s}button:hover{border-color:var(--cyan);transform:translateY(-1px)}button.primary{background:linear-gradient(100deg,#0f766e,#2563eb);border:0;font-weight:600;box-shadow:0 7px 25px #2563eb38}button:disabled{opacity:.55;cursor:wait}
    
    /* CHART STYLING - CONTAINED AND COMPACT */
    .chart{padding:12px 16px;position:relative;overflow:hidden}
    .chart svg{width:100%;height:190px;overflow:visible;display:block}
    .gridline{stroke:#273145;stroke-width:1}
    .risk-line{fill:none;stroke:var(--cyan);stroke-width:2;filter:drop-shadow(0 0 4px #5eead488)}
    .risk-line.reveal{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.05s ease forwards}
    .area{fill:url(#areaGradient);opacity:.28}
    .point{fill:var(--cyan);opacity:.65;transition:.18s;pointer-events:none}
    .point.active-point{fill:#ffffff;filter:drop-shadow(0 0 6px var(--cyan))}
    .hitpoint{fill:transparent;pointer-events:all;cursor:crosshair}
    .hitpoint:hover+.point{r:5;opacity:1;filter:drop-shadow(0 0 6px var(--cyan))}
    .anomaly{fill:var(--red);filter:drop-shadow(0 0 6px var(--red));animation:pulse 1.4s infinite;pointer-events:none}
    .cursor{stroke:#ffffff;stroke-width:1;stroke-dasharray:3 3;opacity:.7;pointer-events:none}
    .selected-ring{pointer-events:none;animation:ringPulse 1.8s infinite}
    @keyframes ringPulse{0%{r:5px;opacity:1}50%{r:9px;opacity:0.4}100%{r:5px;opacity:1}}
    .now{position:absolute;top:10px;right:16px;background:rgba(13,19,29,.9);border:1px solid var(--line);border-radius:7px;padding:3px 9px;font-size:11px;pointer-events:none;z-index:2;display:flex;align-items:center;gap:6px}
    .now b{font-size:14px;color:var(--cyan)}
    .now.alert{border-color:rgba(251,113,133,.4);background:rgba(251,113,133,.12)}
    .now.alert b{color:var(--red);text-shadow:0 0 10px #fb718577}
    
    /* USER LIST PANEL */
    .user-list-panel{display:flex;flex-direction:column;height:100%;min-height:760px;overflow:hidden}
    .user-scroll{flex:1 1 0;min-height:0;max-height:none;overflow-y:auto;overflow-x:hidden}
    .user-scroll::-webkit-scrollbar{width:6px}
    .user-scroll::-webkit-scrollbar-track{background:#0d131d;border-radius:4px}
    .user-scroll::-webkit-scrollbar-thumb{background:#25334a;border-radius:4px}
    .user-scroll::-webkit-scrollbar-thumb:hover{background:var(--cyan)}

    table{width:100%;border-collapse:collapse}th,td{padding:10px 13px;border-bottom:1px solid #202a3a;text-align:left}th{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);position:sticky;top:0;background:#111722;z-index:2}tbody tr{cursor:pointer;transition:.15s}tbody tr:hover,tbody tr.active{background:#1a2636}tbody tr.danger{box-shadow:inset 3px 0 var(--red)}.risk{font-weight:700}.critical{color:var(--red)}.high{color:var(--amber)}.medium{color:var(--blue)}.low{color:var(--cyan)}
    .profile-strip{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:0 16px 12px}.profile-strip .chip{border:1px solid var(--line);border-radius:99px;padding:3px 8px;color:var(--muted);font-size:11px}.profile-strip .chip b{color:var(--text)}.feed{height:185px;overflow-y:auto;padding:10px 15px}.event{display:grid;grid-template-columns:65px 1fr auto;gap:10px;padding:7px 0;border-bottom:1px solid #202a3a;animation:slide .3s ease;font-size:12px}.event.alert{color:#ffd7df}.badge{font-size:10px;font-weight:600;border:1px solid var(--line);border-radius:99px;padding:2px 8px;white-space:nowrap}.badge.red{border-color:#fb718566;color:var(--red);background:#fb718512}.badge.green{border-color:#34d39966;color:var(--green);background:#34d39912}.badge.blue{border-color:#60a5fa66;color:var(--blue);background:#60a5fa12}.badge.amber{border-color:#fbbf2466;color:var(--amber);background:#fbbf2412}
    .generator{display:grid;grid-template-columns:360px 1fr;gap:12px;padding-bottom:30px}.controls{padding:18px}.field{margin-bottom:16px}.field label{display:block;color:var(--muted);font-size:11px;margin-bottom:6px}.field select,.field input[type=number],.field input[type=text]{width:100%;background:#0d131d;border:1px solid var(--line);color:var(--text);padding:9px;border-radius:8px}.field input[type=range]{width:100%;accent-color:var(--cyan)}.hint{color:var(--muted);font-size:11px}.scenario-info{border-left:2px solid var(--cyan);padding-left:11px;margin:12px 0 18px}.scenario-info b{display:block;margin-bottom:3px;font-size:13px}.scenario-info span{color:var(--muted);font-size:12px}
    .generation-output{min-height:560px}.empty{height:480px;display:grid;place-items:center;text-align:center;color:var(--muted)}.radar{width:74px;height:74px;border:1px solid var(--cyan);border-radius:50%;position:relative;margin:auto auto 14px;opacity:.6}.radar:after{content:"";position:absolute;inset:8px;border-radius:50%;border:1px dashed var(--cyan);animation:spin 5s linear infinite}.radar:before{content:"";position:absolute;left:50%;top:50%;width:46%;height:1px;background:var(--cyan);transform-origin:left;animation:spin 2s linear infinite}
    
    .gen-result-wrap{display:grid;gap:12px;padding:16px}
    .gen-result-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;padding-bottom:12px;border-bottom:1px solid var(--line)}
    .gen-result-head h2{font-size:16px;margin:0 0 4px;font-weight:700}
    .gen-meta{font-size:12px;color:var(--muted)}
    .gen-meta b{color:var(--text)}
    .gen-summary-card{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
    .gen-stat{display:flex;flex-direction:column}
    .gen-stat .num{font-size:22px;font-weight:700;margin-top:3px}
    .gen-stat .desc{font-size:11px;color:var(--muted);margin-top:2px}
    
    .gen-charts-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
    .series-card{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:11px}
    .series-card h3{font-size:12px;margin:0 0 6px;display:flex;justify-content:space-between;align-items:center}
    .series-card svg{width:100%;height:105px}
    .normal-line{fill:none;stroke:var(--blue);stroke-width:1.8}
    .synthetic-line{fill:none;stroke:var(--red);stroke-width:2;filter:drop-shadow(0 0 3px #fb718577)}
    .impact-zone{fill:#fb718515}
    .gen-hit{fill:transparent;pointer-events:all;cursor:crosshair}
    .legend{display:flex;gap:12px;font-size:10px;color:var(--muted)}
    .legend i{display:inline-block;width:10px;height:2px;vertical-align:middle;margin-right:4px}
    
    .table-and-conclusion{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .diff-table-card{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:12px}
    .diff-table-card h3{font-size:12px;margin:0 0 8px;font-weight:600}
    .diff-table{width:100%;font-size:11px}
    .diff-table th,.diff-table td{padding:5px 6px;border-bottom:1px solid #1a2536}
    .diff-badge{padding:2px 5px;border-radius:4px;font-weight:600;font-size:10px;background:#fb718522;color:var(--red)}
    .conclusion-box{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:12px;display:flex;flex-direction:column;justify-content:center;font-size:12px;color:#cbd5e1;line-height:1.5}
    .conclusion-box b{color:var(--cyan);font-weight:600}

    .tooltip{position:fixed;z-index:1500;pointer-events:none;min-width:175px;max-width:320px;padding:8px 11px;border:1px solid #5eead466;border-radius:8px;background:#080d14fa;box-shadow:0 10px 35px #0009;color:var(--text);font-size:11px;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
    .tooltip.show{opacity:1;transform:none}
    .tooltip b{display:block;color:var(--cyan);font-size:12px;margin-bottom:2px}
    .augmentation-chart{height:220px;margin-top:12px}.augmentation-chart svg{width:100%;height:100%}.bar-base{fill:#334155}.bar-gan{fill:var(--cyan);filter:drop-shadow(0 0 5px #5eead455);cursor:pointer;transition:.2s}.bar-gan:hover{fill:#99f6e4}.metric-chip{display:inline-flex;gap:6px;align-items:center;border:1px solid var(--line);border-radius:99px;padding:4px 9px;margin:3px;color:var(--muted);font-size:11px}
    
    .method{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding-bottom:35px}
    .method .panel{padding:18px}
    .method h2{font-size:15px;margin-top:0;font-weight:600}
    .metric{font-size:30px;font-weight:700}
    .ok{color:var(--green)}
    
    .benchmark-table{width:100%;font-size:12px;margin-top:6px}
    .benchmark-table th,.benchmark-table td{padding:9px 12px;border-bottom:1px solid #202a3a}
    .benchmark-table tr:hover{background:#162232}
    .tag-role{display:inline-block;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600}
    .tag-main{background:#5eead415;color:var(--cyan);border:1px solid #5eead444}
    .tag-gen{background:#a78bfa15;color:#c4b5fd;border:1px solid #a78bfa44}
    .tag-base{background:#60a5fa15;color:var(--blue);border:1px solid #60a5fa44}

    .mitre-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}
    .mitre-card{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:6px}
    .mitre-card-head{display:flex;justify-content:space-between;align-items:flex-start}
    .mitre-code{color:var(--cyan);font-weight:700;font-size:12px}
    .mitre-name{font-weight:600;font-size:12px;margin-top:2px}
    .mitre-stat-row{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:4px}
    .mitre-stat-row b{color:var(--text)}
    .mitre-bar-track{height:6px;background:#202a3a;border-radius:99px;overflow:hidden;margin-top:4px}
    .mitre-bar-fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--cyan));border-radius:99px}
    .mitre-feature-note{font-size:10px;color:var(--muted);margin-top:4px}

    .feature-importance-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:10px}
    .feature-imp-item{background:#0d131d;border:1px solid var(--line);border-radius:8px;padding:9px 12px}
    .feature-imp-head{display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px}
    .feature-imp-head b{color:var(--text)}
    .feature-imp-head span{color:var(--cyan);font-weight:700}
    .feature-imp-bar{height:5px;background:#202a3a;border-radius:99px;overflow:hidden}
    .feature-imp-fill{height:100%;background:linear-gradient(90deg,var(--cyan),#60a5fa);border-radius:99px}

    .insights-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:10px}
    .insight-box{background:#0d131d;border:1px solid var(--line);border-radius:10px;padding:14px;font-size:12px;color:#cbd5e1;line-height:1.45}
    .insight-box b{color:var(--cyan);display:block;margin-bottom:4px;font-size:13px}

    .population{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:12px;margin-bottom:12px}.pop-card{padding:14px 16px}.donut-wrap{display:flex;align-items:center;gap:18px}.donut{width:136px;height:136px;position:relative;flex:none;filter:drop-shadow(0 0 14px #5eead422)}.donut svg{width:100%;height:100%;overflow:visible}.donut-track{fill:none;stroke:#202a3a;stroke-width:14}.donut-segment{fill:none;stroke-width:14;cursor:pointer;transition:stroke-width .18s,filter .18s;outline:none}.donut-segment:hover,.donut-segment.active{stroke-width:19;filter:drop-shadow(0 0 5px currentColor)}.donut-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;pointer-events:none;font-size:19px;font-weight:700;line-height:1.1}.donut-center small{display:block;max-width:70px;margin-top:3px;font-size:9px;line-height:1.2;color:var(--muted);font-weight:400}.pop-legend{display:grid;gap:4px;width:100%}.legend-row{display:flex;justify-content:space-between;gap:12px;font-size:11px;padding:4px 7px;border-radius:5px;cursor:pointer;border:1px solid transparent}.legend-row:hover,.legend-row.active{background:#ffffff08;border-color:var(--line)}.legend-row i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}.filter-note{font-size:10px;color:var(--cyan);margin-top:6px;min-height:14px}.mini-bars{height:120px;display:flex;align-items:end;gap:12px;padding-top:12px}.mini-col{flex:1;text-align:center;color:var(--muted);font-size:10px}.mini-bar{min-height:3px;border-radius:5px 5px 2px 2px;background:linear-gradient(var(--cyan),#2563eb);transition:.25s;cursor:pointer}.mini-bar:hover{filter:brightness(1.3);transform:scaleX(1.05)}.employee-name{font-size:12px;font-weight:600}.employee-id{font-size:10px;color:var(--muted);letter-spacing:.04em}
    .event-detail{margin-top:0;min-height:270px}.event-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.event-body{display:grid;grid-template-columns:230px 1fr;gap:12px;padding:14px}.event-summary{display:grid;gap:8px}.event-state{padding:11px;border-radius:10px;background:#0d131d;border:1px solid var(--line)}.event-state.alert{border-color:#fb718566;background:#fb71850b}.event-state b{font-size:24px;display:block}.feature-table{width:100%;font-size:11px}.feature-table th,.feature-table td{padding:6px 8px}.feature-table tr.hot{background:#fb71850a}.deviation{height:5px;background:#202a3a;border-radius:9px;overflow:hidden;min-width:65px}.deviation i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--red));border-radius:9px}.raw-note{padding:0 14px 12px;color:var(--muted);font-size:10px}.event-spark{width:100%;height:54px}.event-spark polyline{fill:none;stroke:var(--blue);stroke-width:2}.event-spark circle{fill:var(--cyan)}
    .step{position:relative;padding-left:36px;margin-bottom:18px}.step-no{position:absolute;left:0;top:0;width:24px;height:24px;border:1px solid #5eead466;border-radius:50%;display:grid;place-items:center;color:var(--cyan);font-size:11px;font-weight:700;box-shadow:0 0 12px #5eead422}.feature-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.feature-chips span{padding:3px 7px;border-radius:99px;background:#60a5fa12;border:1px solid #60a5fa33;color:#b9d9ff;font-size:10px}details{color:var(--muted);font-size:11px;margin:8px 0}details summary{cursor:pointer}.history{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}.history-item{font-size:11px;color:var(--muted);padding:6px 8px;border-radius:6px;cursor:pointer}.history-item:hover{background:#ffffff08;color:var(--text)}
    .mode-switch{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:10px 0 16px;padding:3px;background:#0b1018;border:1px solid var(--line);border-radius:10px}.mode-switch button{border:0;background:transparent;padding:6px;font-size:11px}.mode-switch button.active{background:#25334a;color:var(--cyan);box-shadow:inset 0 0 0 1px #5eead444}.custom-builder{display:none}.custom-builder.active{display:block;animation:enter .25s ease}.preset-builder.hidden{display:none}.channel-grid{display:grid;gap:5px;max-height:240px;overflow:auto;padding-right:4px}.channel-row{display:grid;grid-template-columns:20px 1fr 70px;gap:7px;align-items:center;padding:6px 8px;border:1px solid var(--line);border-radius:7px;background:#0d131d;font-size:11px}.channel-row:has(input:checked){border-color:#a78bfa77;background:#8b5cf60b}.channel-row input{accent-color:#a78bfa}.channel-row select{background:#111a28;color:var(--text);border:1px solid var(--line);border-radius:5px;padding:3px;font-size:10px}.builder-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.builder-preview{margin:9px 0;padding:9px;border:1px solid #a78bfa44;border-radius:8px;background:#8b5cf609;font-size:11px;color:#c4b5fd}.timeline-preview{display:grid;grid-template-columns:repeat(14,1fr);gap:2px;margin-top:6px}.timeline-preview i{height:16px;border-radius:3px;background:#202a3a}.timeline-preview i.on{background:#a78bfa;box-shadow:0 0 6px #a78bfa88}
    .case-panel{margin:0 14px 12px;padding:12px 14px;border:1px solid #334158;border-radius:10px;background:#0b111a}.case-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:8px}.case-status{font-size:10px;font-weight:600;padding:3px 8px;border-radius:99px;border:1px solid var(--line)}.case-status.confirmed{color:var(--red);border-color:#fb718566;background:#fb718512}.case-status.false-positive{color:var(--green);border-color:#34d39966;background:#34d39912}.case-status.investigating{color:var(--amber);border-color:#fbbf2466;background:#fbbf2412}.case-actions{display:flex;gap:6px;flex-wrap:wrap}.case-actions button.active{border-color:var(--cyan);background:#5eead412}.case-notes{width:100%;min-height:60px;margin:8px 0;background:#080d14;color:var(--text);border:1px solid var(--line);border-radius:7px;padding:8px;resize:vertical;font:11px/1.4 inherit}.case-meta{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;color:var(--muted);font-size:10px}
    .about-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:12px;padding-bottom:35px}.hero-about{padding:24px;grid-column:1/-1;position:relative;overflow:hidden;background:radial-gradient(circle at 80% 20%,#8b5cf62a,transparent 35%),linear-gradient(145deg,rgba(22,30,43,.94),rgba(13,18,27,.94))}.hero-about:after{content:"UEBA";position:absolute;right:30px;top:-20px;font-size:130px;font-weight:900;color:#a78bfa08;letter-spacing:-.06em;pointer-events:none}.hero-about h2{font-size:24px;max-width:780px;margin:6px 0 10px;font-weight:700}.hero-about p{max-width:820px;color:#c9d5e5;font-size:13px;margin:0}.architecture{padding:18px;grid-column:1/-1}
    
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
    
    .arch-icon{font-size:20px;display:block;margin-bottom:6px}.arch-detail{padding:16px;border-radius:11px;background:#080d14;border:1px solid #334158;min-height:300px}.arch-detail-head{display:flex;justify-content:space-between;gap:18px;margin-bottom:12px}.arch-detail-head h3{margin:0 0 2px;font-size:16px;font-weight:600}.arch-detail-grid{display:grid;grid-template-columns:.85fr 1.15fr;gap:14px}.diagram{min-height:205px;border:1px solid var(--line);border-radius:10px;background:radial-gradient(circle at 50% 50%,#2563eb10,transparent 60%),#0d131d;padding:10px;overflow:hidden}.diagram svg{width:100%;height:205px;display:block}.diagram text{fill:#edf3fb;font:11px "Segoe UI",Inter,sans-serif;dominant-baseline:central;text-anchor:middle}.diagram .box{fill:#111c2a;stroke:#4b6380;stroke-width:1}.diagram .ai-box{fill:#291e43;stroke:#a78bfa;stroke-width:1.2}.diagram .wire{fill:none;stroke:#5eead4;stroke-width:1.5;stroke-dasharray:5 4;animation:dashmove 2s linear infinite}.diagram .ai-wire{stroke:#a78bfa}.diagram .solid-wire{fill:none;stroke:#5eead4;stroke-width:1.5}.diagram .signal{fill:#5eead4;filter:drop-shadow(0 0 4px #5eead4)}.log-sample{width:100%;font-family:Consolas,monospace;font-size:11px;border-collapse:separate;border-spacing:0 4px}.log-sample td{padding:6px 8px;background:#111c2a;border:0}.log-sample td:first-child{color:var(--cyan);border-radius:5px 0 0 5px}.log-sample td:last-child{border-radius:0 5px 5px 0}.window-days{display:grid;grid-template-columns:repeat(14,1fr);gap:3px;margin:10px 0 12px}.window-day{height:50px;border:1px solid #334158;border-radius:4px;display:flex;align-items:end;justify-content:center;background:linear-gradient(to top,#2563eb88 var(--v),transparent var(--v));font-size:8px;padding-bottom:2px}.arch-facts{display:grid;gap:6px}.arch-fact{padding:8px 10px;border-left:2px solid var(--cyan);background:#5eead407;color:#aebbd0;font-size:11px}.arch-fact b{color:var(--text);display:block;margin-bottom:2px}.compare{padding:18px}.compare h2{margin-top:0;font-size:15px;font-weight:600}.compare-row{display:grid;grid-template-columns:24px 1fr;gap:10px;padding:9px 0;border-bottom:1px solid #202a3a}.compare-icon{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:#34d3991a;color:var(--green);font-size:12px;font-weight:700}.compare-icon.neutral{background:#60a5fa1a;color:var(--blue)}
    .loading{display:inline-flex;gap:5px;align-items:center}.loading i{width:5px;height:5px;background:white;border-radius:50%;animation:bounce 1s infinite}.loading i:nth-child(2){animation-delay:.15s}.loading i:nth-child(3){animation-delay:.3s}
    
    /* SOC SIMULATOR CARD */
    .soc-calc-card{background:linear-gradient(145deg,#0e1a2b,#09121d);border:1px solid #283d5a;border-radius:13px;padding:18px;margin-top:14px;box-shadow:0 16px 40px rgba(0,0,0,.45)}
    .soc-calc-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:20px;margin-top:14px;align-items:center}
    .soc-calc-controls{display:grid;gap:14px}
    .soc-calc-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
    .soc-stat-box{background:#0a111a;border:1px solid #203047;border-radius:9px;padding:10px 14px}
    .soc-stat-box .label{font-size:11px;color:var(--muted)}
    .soc-stat-box .val{font-size:22px;font-weight:800;margin-top:2px;font-variant-numeric:tabular-nums}
    .soc-stat-box .desc{font-size:10px;color:var(--muted);margin-top:2px}
    .soc-status-badge{padding:8px 12px;border-radius:8px;font-size:12px;font-weight:700;display:flex;align-items:center;gap:8px;grid-column:1/-1}
    .soc-status-badge.ok{background:rgba(34,197,94,.12);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
    .soc-status-badge.warn{background:rgba(251,191,36,.12);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
    .soc-status-badge.danger{background:rgba(251,113,133,.12);color:#fb7185;border:1px solid rgba(251,113,133,.3)}

    /* QUICK USER ACTION BUTTONS IN GENERATOR */
    .user-select-bar{display:flex;gap:6px;margin-bottom:6px}
    .user-select-btn{flex:1;padding:5px 8px;font-size:11px;background:#142233;border:1px solid #2a3c54;color:var(--muted);border-radius:6px;cursor:pointer;transition:.15s}
    .user-select-btn:hover{color:var(--cyan);border-color:var(--cyan)}
    
    /* INTERACTIVE MODAL OVERLAY */
    .modal-overlay{position:fixed;inset:0;background:rgba(4,7,14,0.78);backdrop-filter:blur(8px);z-index:1000;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .2s ease}
    .modal-overlay.open{opacity:1;pointer-events:all}
    .modal-container{background:linear-gradient(145deg,#121c2c,#0a111a);border:1px solid #2a3d58;border-radius:16px;width:min(940px,94vw);max-height:86vh;display:flex;flex-direction:column;box-shadow:0 25px 60px rgba(0,0,0,.75);overflow:hidden;animation:modalEnter .25s cubic-bezier(0.16,1,0.3,1)}
    @keyframes modalEnter{from{opacity:0;transform:scale(0.95) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
    .modal-head{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;background:#0d1522}
    .modal-head h2{margin:0;font-size:16px;font-weight:700;display:flex;align-items:center;gap:8px}
    .modal-close{width:32px;height:32px;border-radius:8px;border:1px solid #334158;background:#172234;color:var(--text);font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;transition:.15s}
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

    @keyframes pulse{50%{opacity:.3}}@keyframes enter{from{opacity:0;transform:translateY(6px)}}@keyframes draw{to{stroke-dashoffset:0}}@keyframes dashmove{to{stroke-dashoffset:-18}}@keyframes slide{from{opacity:0;transform:translateX(12px)}}@keyframes spin{to{transform:rotate(360deg)}}@keyframes bounce{50%{transform:translateY(-4px)}}
    @media(max-width:950px){.cards{grid-template-columns:repeat(2,1fr)}.grid,.generator,.population,.about-grid,.arch-detail-grid,.event-body,.table-and-conclusion,.gen-charts-grid,.mitre-grid,.feature-importance-grid,.insights-grid{grid-template-columns:1fr}.method{grid-template-columns:1fr}.arch-flow{grid-template-columns:1fr}.arch-node:not(:last-child):after{display:none}}@media(max-width:600px){header{align-items:flex-start;flex-direction:column}.cards{grid-template-columns:1fr}.toolbar{flex-wrap:wrap}.donut-wrap{align-items:flex-start}.window-days{grid-template-columns:repeat(7,1fr)}.gen-summary-card{grid-template-columns:1fr}}
  </style>"""

content = re.sub(r'<style>.*?</style>', clean_style, content, flags=re.DOTALL)

# 2. Update drawRisk to render the exact compact timeline strip without overflowing or covering anything!
clean_draw_risk_js = """    let activeDayIndex = null;

    function drawRisk(all, selectedIndex){
      let t = all;
      let w = 720, h = 190, p = 16;
      let pts = points(t, w, h, p);
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
        let isAl = (d.risk / 100) >= th;
        let rCls = riskClass(d.risk);
        let isSel = (i === activeIdx);
        return `<div class="day-cell ${rCls} ${isSel?'active-day':''}" data-day-i="${i}" tabindex="0" title="${d.day} · Риск ${d.risk}/100"></div>`;
      }).join('');
      
      $('#riskChart').innerHTML = `
        <svg viewBox="0 0 ${w} ${h}">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#5eead4" stop-opacity="0.32"/>
              <stop offset="100%" stop-color="#5eead4" stop-opacity="0.02"/>
            </linearGradient>
          </defs>
          ${grid}
          ${thLine}
          <polygon class="area" points="${p},${h-p} ${poly} ${pts[pts.length-1][0]},${h-p}"/>
          <polyline class="risk-line reveal" points="${poly}"/>
          ${dots}
          <line class="cursor" x1="${activePt[0]}" x2="${activePt[0]}" y1="${p}" y2="${h-p}"/>
          <circle class="selected-ring" cx="${activePt[0]}" cy="${activePt[1]}" r="8" fill="none" stroke="#5eead4" stroke-width="2"/>
          <circle cx="${activePt[0]}" cy="${activePt[1]}" r="4" fill="#ffffff"/>
        </svg>
        <div class="now ${isActiveAlert?'alert':''}">
          <span class="label">${activeDay.day}:</span>
          <b class="${riskClass(activeDay.risk)}">${activeDay.risk}</b>
          <span class="label">/ 100</span>
        </div>
        <div class="timeline-strip-wrap">
          <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)">
            <span class="term-tip" data-term="Окно активности">Лента 14 дней: <i>ℹ</i></span>
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
    }"""

content = re.sub(r'let activeDayIndex = null;.*?function attachDayInteraction\(el, i\)\{.*?\$\$\(\'#riskChart \.day-cell\'\)\.forEach\(dc => attachDayInteraction\(dc, \+dc\.dataset\.dayI\)\);\s*bindTermTooltips\(\);\s*\}', clean_draw_risk_js, content, flags=re.DOTALL)

html_path.write_text(content, encoding="utf-8")
print("Clean compact chart and timeline strip applied.")
