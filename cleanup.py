import os, re

BASE = os.path.join(os.path.expanduser("~"), "tpv-chaquopy")
INDEX = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")

with open(INDEX, "r", encoding="utf-8") as f:
    html = f.read()

changed = 0

# ── 1. Eliminar burbuja de modo oscuro ──
if "dark-mode-bubble" in html:
    html = re.sub(
        r'\s*<!-- ═══ Dark Mode Draggable Bubble ═══ -->.*?<!-- ═══ End Dark Mode Bubble ═══ -->\s*',
        '\n', html, flags=re.DOTALL)
    changed += 1
    print("✓ Burbuja de modo oscuro eliminada")
else:
    print("- Burbuja de modo oscuro no encontrada")

# ── 2. Eliminar indicador offline ──
if 'id="offline-indicator"' in html:
    html = re.sub(
        r'\s*<!-- Indicador de estado offline -->\s*<div id="offline-indicator"[^>]*>.*?</div>\s*',
        '\n', html, flags=re.DOTALL)
    changed += 1
    print("✓ Indicador offline eliminado del HTML")
else:
    print("- Indicador offline no encontrado en HTML")

with open(INDEX, "w", encoding="utf-8") as f:
    f.write(html)

# ── 3. Ocultar offline-indicator en CSS ──
CSS_FILE = os.path.join(BASE, "app/src/main/assets/frontend/static/css/style_5.css")
with open(CSS_FILE, "r", encoding="utf-8") as f:
    css = f.read()

if ".offline-indicator" in css:
    css = re.sub(
        r'(\.offline-indicator\s*\{[^}]*\})',
        r'\1\n        .offline-indicator { display: none !important; }',
        css, flags=re.DOTALL)
    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(css)
    changed += 1
    print("✓ Offline indicator ocultado en CSS")
else:
    print("- No se encontró .offline-indicator en CSS")

print(f"\n{changed} cambios aplicados")
