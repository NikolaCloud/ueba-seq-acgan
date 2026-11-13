"""Check all function calls against definitions in index.html script."""

import re
from pathlib import Path

html = Path("src/ueba_seq_acgan/web/index.html").read_text(encoding="utf-8")
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
assert script_match, "No script tag found!"
script = script_match.group(1)

# Find all function definitions
func_defs = set(re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', script))
# Also arrow functions: const foo = (...) =>
arrow_defs = set(re.findall(r'(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>', script))
all_defs = func_defs.union(arrow_defs)

# Builtin standard JS functions/methods to ignore
builtins = {
    'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURIComponent', 'decodeURIComponent',
    'fetch', 'alert', 'confirm', 'prompt', 'setInterval', 'clearInterval', 'setTimeout', 'clearTimeout',
    'requestAnimationFrame', 'cancelAnimationFrame', 'Number', 'String', 'Boolean', 'Array', 'Object',
    'Date', 'RegExp', 'Math', 'JSON', 'Promise', 'Error', 'URL', 'Blob'
}

# Find all function calls: name(...)
func_calls = set(re.findall(r'\b([a-zA-Z0-9_]+)\s*\(', script))
# Filter out control keywords
keywords = {'if', 'for', 'while', 'switch', 'catch', 'function', 'return', 'typeof', 'delete', 'import', 'export'}
called_user_funcs = func_calls - keywords - builtins

print(f"Total defined functions in script: {len(all_defs)}")
print(sorted(all_defs))

print(f"\nTotal called functions: {len(called_user_funcs)}")
print(sorted(called_user_funcs))

undefined = called_user_funcs - all_defs
print(f"\nUndefined functions: {undefined}")
assert len(undefined) == 0, f"Found undefined functions: {undefined}"
print("\n[OK] 100% of all called functions are properly defined!")
