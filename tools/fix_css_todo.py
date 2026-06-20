#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TPV — Reaplicar TODOS los fixes de CSS/UI que se perdieron.

NO toca archivos Python (ya están arreglados).
SOLO agrega CSS al index.html para arreglar:
  1. Submenús solapados
  2. Gestión de usuarios (u-card, u-pill)
  3. Debug bar no tapa contenido
  4. Responsive móvil
  5. Nav tabs scroll horizontal

Uso:
    python fix_css_todo.py
"""
import os
from pathlib import Path

REPO = Path(os.environ.get("TPV_REPO_DIR", os.path.expanduser("~/tpv-chaquopy")))
INDEX = REPO / "app/src/main/assets/frontend/templates/index.html"

G = '\033[1;32m'; B = '\033[1;36m'; N = '\033[0m'
log  = lambda m: print(f"{G}✅{N} {m}")
step = lambda m: print(f"\n{B}━━━ {m} ━━━{N}")

step("Reaplicar TODOS los fixes de CSS/UI")

if not INDEX.exists():
    print(f"❌ No encuentro {INDEX}")
    exit(1)

src = INDEX.read_text(encoding="utf-8")

# Eliminar fixes anteriores si existen
import re
src = re.sub(r'\n\s*/\* FIX[^*]*(?:Submenús|submenus|CSS|Responsive|Debug bar|Gestión)[^*]*\*/.*?(?=\n\s*/\*|\n\s*</style>)', '', src, flags=re.DOTALL | re.IGNORECASE)

# CSS COMPLETO con todos los fixes
CSS_TODO = '''
        /* ═══ FIX INTEGRAL CSS v8.14 ═══ */

        /* 1. Submenús siempre encima + scroll horizontal */
        #main-nav-tabs {
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            overflow-y: visible !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            padding-bottom: 4px;
        }
        #main-nav-tabs::-webkit-scrollbar { display: none; }
        #main-nav-tabs .nav-item { flex-shrink: 0; }
        #main-nav-tabs .dropdown-menu {
            z-index: 99999 !important;
            position: fixed !important;
            box-shadow: 0 12px 40px rgba(0,0,0,.4) !important;
            border: 1px solid rgba(255,255,255,.1) !important;
            background: #1e293b !important;
        }
        #main-nav-tabs .dropdown-item { color: #e2e8f0 !important; }
        #main-nav-tabs .dropdown-item:hover {
            background: rgba(79,70,229,0.25) !important;
            color: #fff !important;
        }
        #main-nav-tabs .dropdown-header { color: #94a3b8 !important; }
        .tab-content, .tab-pane { overflow: visible !important; }

        /* 2. Gestión de Usuarios — u-card + u-pill profesionales */
        .u-card {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding: 10px 12px !important;
            border-radius: 10px !important;
            margin-bottom: 6px !important;
            background: rgba(30, 41, 59, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            gap: 8px !important;
            transition: all 0.2s ease;
        }
        .u-card:hover {
            background: rgba(79, 70, 229, 0.1) !important;
            border-color: rgba(79, 70, 229, 0.3) !important;
        }
        .u-pill {
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
            max-width: none !important;
            padding: 0.2rem 0.55rem !important;
            border-radius: 999px !important;
            font-size: 0.62rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.02em !important;
            flex-shrink: 0 !important;
        }
        .ub-badge {
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
            max-width: none !important;
            font-size: 0.62rem !important;
            padding: 0.15rem 0.5rem !important;
        }
        .u-card .fw-semibold {
            font-size: 0.85rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .u-card .text-muted.small {
            font-size: 0.7rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .u-card .btn-sm {
            min-width: 32px !important;
            min-height: 32px !important;
            padding: 4px 8px !important;
        }
        .priv-rol-card {
            padding: 12px 6px !important;
            font-size: 0.75rem !important;
            white-space: nowrap !important;
        }
        .priv-rol-card span {
            white-space: nowrap !important;
            overflow: visible !important;
            font-size: 0.72rem !important;
        }
        .priv-rol-card i { font-size: 1.3em !important; }

        /* 3. Debug bar no se superpone con contenido */
        body.debug-active { padding-bottom: 60px !important; }
        #dbg-v2 { z-index: 9998 !important; }
        @media (max-width: 768px) {
            body.debug-active { padding-bottom: 80px !important; }
            #dbg-v2 { font-size: 10px !important; }
        }

        /* 4. Responsive APK */
        * { -webkit-tap-highlight-color: transparent; }
        html { -webkit-text-size-adjust: 100%; }
        body { overflow-x: hidden; width: 100vw; max-width: 100%; }
        .container, .container-fluid { max-width: 100% !important; padding-left: 12px !important; padding-right: 12px !important; }
        .glass-card, .card { border-radius: 12px !important; padding: 14px !important; overflow: visible !important; }
        .table-responsive { -webkit-overflow-scrolling: touch; }
        .table { font-size: 0.8rem !important; }
        .modal-dialog { margin: 8px !important; }
        .btn { min-height: 40px; font-size: 0.85rem; }
        .btn-sm { min-height: 34px; }
        input, select, textarea { font-size: 16px !important; min-height: 40px; }

        /* 5. Responsive móvil pequeño */
        @media (max-width: 576px) {
            .row > [class*="col-"] { padding-left: 6px !important; padding-right: 6px !important; }
            h4 { font-size: 1.1rem !important; }
            h5 { font-size: 1rem !important; }
            h6 { font-size: 0.9rem !important; }
            .glass-card, .card { padding: 10px !important; }
            .table { font-size: 0.75rem !important; }
            .ub-badge { font-size: 0.55rem !important; padding: 0.15rem 0.4rem !important; }
            .u-pill { font-size: 0.55rem !important; padding: 0.15rem 0.4rem !important; }
            .priv-rol-card { padding: 10px 4px !important; }
            .u-card { padding: 8px 10px !important; }
        }

        /* 6. Canvas solo en dashboard */
        canvas { max-width: 100%; }
'''

# Insertar antes del último </style>
last_style = src.rfind("</style>")
if last_style != -1:
    src = src[:last_style] + CSS_TODO + "\n        " + src[last_style:]
    INDEX.write_text(src, encoding="utf-8")
    log(f"CSS integral agregado al index.html ({len(src)} bytes)")

# Verificar que se aplicó
content = INDEX.read_text(encoding="utf-8")
checks = [
    ("Submenús z-index", "z-index: 99999" in content),
    ("Submenús position:fixed", "position: fixed" in content),
    ("Nav scroll horizontal", "overflow-x: auto" in content),
    ("u-card con nowrap", ".u-card" in content and "nowrap" in content),
    ("u-pill con nowrap", ".u-pill" in content and "nowrap" in content),
    ("Debug bar padding", "body.debug-active" in content),
    ("Responsive móvil", "@media (max-width: 576px)" in content),
    ("Inputs 16px", "font-size: 16px" in content),
]

print("\nVerificación:")
for name, ok in checks:
    print(f"  {'✅' if ok else '❌'} {name}")

step("DONE")
print(f"""
{G}Todos los fixes de CSS reaplicados.{N}

Reinicia el servidor:
  pkill -f "python app.py"; sleep 2
  cd ~/tpv-chaquopy/app/src/main/python
  nohup env TPV_PORT=5050 python app.py > ~/tpv_server.log 2>&1 &
  echo $! > ~/tpv_server.pid
  sleep 5

Abre Chrome: http://localhost:5050
  - Submenús no se solapan
  - Gestión de Usuarios: ADMINISTRADOR completo
  - Debug bar no tapa tarjetas
  - Responsive en móvil

Commit:
  cd ~/tpv-chaquopy && git add -A && git commit -m "fix(css): reaplicar todos los fixes UI — submenus + usuarios + debug + responsive"
""")
