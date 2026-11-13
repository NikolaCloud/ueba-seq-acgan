"""Fix modal placement and safe event listeners in index.html."""

import re
from pathlib import Path

html_path = Path("src/ueba_seq_acgan/web/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Remove modal from after </script>
modal_regex = r'\s*<!-- INTERACTIVE DETAIL MODAL -->\s*<div class="modal-overlay" id="detailModal">.*?</div>\s*</div>'
content = re.sub(modal_regex, '', content, flags=re.DOTALL)

# 2. Place modal inside <main> before </main>
modal_html = """
    <!-- INTERACTIVE DETAIL MODAL -->
    <div class="modal-overlay" id="detailModal">
      <div class="modal-container">
        <div class="modal-head">
          <h2 id="modalTitle">Детальные показатели</h2>
          <button class="modal-close" id="modalClose" title="Закрыть (Esc)">✕</button>
        </div>
        <div class="modal-body" id="modalContent"></div>
      </div>
    </div>
  </main>"""

content = content.replace('</main>', modal_html)

# 3. Make modal close handlers null-safe
modal_js_old = """    $('#modalClose').onclick = closeModal;
    $('#detailModal').onclick = e => { if(e.target === $('#detailModal')) closeModal(); };"""

modal_js_safe = """    document.getElementById('modalClose')?.addEventListener('click', closeModal);
    document.getElementById('detailModal')?.addEventListener('click', e => { if(e.target === document.getElementById('detailModal')) closeModal(); });"""

content = content.replace(modal_js_old, modal_js_safe)

html_path.write_text(content, encoding="utf-8")
print("Modal moved inside <main> and event listeners made 100% safe.")
