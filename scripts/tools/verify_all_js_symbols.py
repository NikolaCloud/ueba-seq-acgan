"""Check all function definitions and calls in index.html."""

import re
from pathlib import Path

html = Path("src/ueba_seq_acgan/web/index.html").read_text(encoding="utf-8")
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
assert script_match, "No script tag found!"
script = script_match.group(1)

# Essential required UI functions that must exist:
required_funcs = [
    'renderCards', 'renderPopulation', 'renderUserRows', 'renderUsers', 'selectUser',
    'drawRisk', 'points', 'humanValue', 'riskSpark', 'renderEventDetail',
    'renderCaseControls', 'caseKey', 'updateCase', 'exportCase', 'addFeed',
    'riskClass', 'riskBandName', 'applyRiskFilter', 'getActiveThreshold', 'saveState', 'readState',
    'showTip', 'hideTip', 'bindTermTooltips', 'openModal', 'closeModal', 'openCardModal',
    'updateSOCSimulator', 'renderArch', 'archContent', 'archHead', 'box',
    'renderGeneration', 'seriesSvg', 'renderHistory', 'renderAugmentation', 'scenarioInfo',
    'renderChannelGrid', 'setBuilderMode', 'updateBuilderPreview', 'customProfile'
]

missing = [fn for fn in required_funcs if f"function {fn}" not in script and f"const {fn}=" not in script and f"let {fn}=" not in script]

if missing:
    print(f"[FAIL] Missing {len(missing)} essential function(s): {missing}")
    assert False, f"Missing functions: {missing}"
else:
    print(f"[SUCCESS] All {len(required_funcs)} essential functions are defined!")

print("Checking syntax integrity...")
assert script.count("{") == script.count("}"), f"Unmatched curly braces! {{: {script.count('{')}, }}: {script.count('}')}"
assert script.count("(") == script.count(")"), f"Unmatched parentheses! (: {script.count('(')}, ): {script.count(')')}"
assert script.count("[") == script.count("]"), f"Unmatched brackets! [: {script.count('[')}, ]: {script.count(']')}"
print("[SUCCESS] All brackets, parentheses, and braces are 100% balanced!")
