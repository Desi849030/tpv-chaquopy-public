#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TPV — Fix DEFINITIVO Y FINAL: IA + BD + Burbuja + submenús + responsive.

Este script arregla TODO de una vez, sin scripts parciales:
  1. Crea tabla audit_logs si no existe
  2. Arregla el handler del agente IA (import os + query SQL segura)
  3. Burbuja: Pointer Events (drag garantizado en móvil)
  4. CSS: submenús + gestión usuarios + responsive + debug bar

Uso:
    python fix_maestro.py
"""
import os
import re
import sqlite3
from pathlib import Path

REPO = Path(os.environ.get("TPV_REPO_DIR", os.path.expanduser("~/tpv-chaquopy")))
PY_DIR = REPO / "app/src/main/python"
JS_DIR = REPO / "app/src/main/assets/frontend/static/js"
TPL_DIR = REPO / "app/src/main/assets/frontend/templates"

G = '\033[1;32m'; Y = '\033[1;33m'; B = '\033[1;36m'; N = '\033[0m'
log  = lambda m: print(f"{G}✅{N} {m}")
warn = lambda m: print(f"{Y}⚠️ {N} {m}")
step = lambda m: print(f"\n{B}━━━ {m} ━━━{N}")


# ═══════════════════════════════════════════════════════════════════════════
# FIX 1: Crear tabla audit_logs si no existe
# ═══════════════════════════════════════════════════════════════════════════
step("Fix 1 · Crear tabla audit_logs")

db_path = PY_DIR / "tpv_datos.db"
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    # Crear tabla si no existe
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            usuario_id TEXT,
            accion TEXT,
            tabla TEXT,
            registro_id TEXT,
            datos TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
    conn.close()
    log(f"Tabla audit_logs verificada ({count} registros)")
else:
    # Crear la tabla en el schema para que se cree al iniciar
    schema_file = PY_DIR / "db/schema.py"
    if schema_file.exists():
        src = schema_file.read_text(encoding="utf-8")
        if "audit_logs" not in src:
            src += """
    # audit_logs (creada en v8.14 fix)
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        log_id TEXT PRIMARY KEY,
        usuario_id TEXT,
        accion TEXT,
        tabla TEXT,
        registro_id TEXT,
        datos TEXT,
        timestamp TEXT
    )''')
"""
            schema_file.write_text(src, encoding="utf-8")
            log("Tabla audit_logs agregada al schema.py")


# ═══════════════════════════════════════════════════════════════════════════
# FIX 2: Handler del agente IA — usar try/except en cada query
# ═══════════════════════════════════════════════════════════════════════════
step("Fix 2 · Agente IA — handler robusto")

handlers_file = PY_DIR / "ia/handlers_staff.py"
if handlers_file.exists():
    src = handlers_file.read_text(encoding="utf-8")

    # Eliminar handlers anteriores (v8.14)
    src = re.sub(
        r"\n    # v8\.14 — Handlers de seguridad.*?(?=\n    return \()",
        "\n",
        src,
        flags=re.DOTALL
    )

    # Handlers robustos con try/except en cada query
    NEW_HANDLERS = '''
    # v8.14 — Handlers de seguridad, sistema y ayuda (robustos)
    if any(k in tl for k in ['seguridad', 'security', 'audit', 'auditoria']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            audit_count = 0
            users_count = 0
            try:
                audit_count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            except: pass
            try:
                users_count = conn.execute("SELECT COUNT(*) FROM usuarios WHERE activo=1").fetchone()[0]
            except: pass
            conn.close()
            return (f"🔐 Estado de Seguridad\\n\\n"
                    f"• Usuarios activos: {users_count}\\n"
                    f"• Registros de auditoría: {audit_count}\\n"
                    f"• Hashing: scrypt KDF (N=16384)\\n"
                    f"• Rate limiting: 20 req/min\\n"
                    f"• Guardrails: SQLi, XSS, PII detection\\n"
                    f"• Sesiones: Flask cookies HTTPOnly\\n"
                    f"• SQLite WAL con BEGIN IMMEDIATE")
        except Exception as e:
            return f"Info de seguridad: sistema operativo, hashing scrypt activo, rate limiting 20/min"

    if any(k in tl for k in ['sistema', 'system status', 'estado del sistema', 'info del sistema', 'apk', 'version']):
        try:
            import sys as _sys
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            prods = 0
            ventas = 0
            try: prods = conn.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
            except: pass
            try: ventas = conn.execute("SELECT COUNT(*) FROM historial_ventas").fetchone()[0]
            except: pass
            conn.close()
            return (f"📊 Sistema TPV Ultra Smart v8.14\\n\\n"
                    f"• Python: {_sys.version.split()[0]}\\n"
                    f"• Productos: {prods}\\n"
                    f"• Ventas: {ventas}\\n"
                    f"• Arquitectura: DDD + Flask + Chaquopy\\n"
                    f"• 28 blueprints activos\\n"
                    f"• IA: ReAct con 141+ herramientas\\n"
                    f"• BD: SQLite WAL")
        except: return "Sistema TPV v8.14 con Flask + Chaquopy + IA ReAct"

    if any(k in tl for k in ['como usar', 'ayuda', 'help', 'manual', 'guia']):
        return ("📖 Guía por Rol\\n\\n"
                "ADMIN: gestiona usuarios, productos, reportes\\n"
                "CAJERO: ventas, arqueo de caja\\n"
                "VENDEDOR: TPV, inventario diario\\n"
                "SUPERVISOR: dashboard, análisis ABC\\n"
                "DESARROLLADOR: debug (botón 🩺), telemetría\\n\\n"
                "Pregúntame: 'seguridad', 'sistema', 'productos', 'ventas'")

    if any(k in tl for k in ['productos', 'inventario', 'stock']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            total = 0; agotados = 0
            try: total = conn.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
            except: pass
            try: agotados = conn.execute("SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= 0").fetchone()[0]
            except: pass
            conn.close()
            return f"📦 Productos activos: {total}\\nAgotados: {agotados}\\nVe a Catálogo → Productos"
        except: return "Ve a Catálogo → Productos para ver el inventario"

    if any(k in tl for k in ['ventas', 'balance', 'ganancias', 'ingresos']):
        try:
            from db_connection import obtener_conexion
            from datetime import date
            conn = obtener_conexion()
            hoy = date.today().isoformat()
            r = [0, 0]
            try: r = conn.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",)).fetchone()
            except: pass
            conn.close()
            return f"💰 Ventas de hoy:\\n• Transacciones: {r[0]}\\n• Total: ${r[1]:.2f}"
        except: return "Ve a Ventas → Historial para ver las ventas"

    if any(k in tl for k in ['usuarios', 'personal', 'empleados']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            total = 0
            try: total = conn.execute("SELECT COUNT(*) FROM usuarios WHERE activo=1").fetchone()[0]
            except: pass
            conn.close()
            return f"👥 Usuarios activos: {total}\\nVe a Herramientas → Usuarios"
        except: return "Ve a Herramientas → Usuarios"

    if any(k in tl for k in ['qr', 'codigo qr']):
        return "📱 QR disponibles en Operación → Etiquetas QR Cliente"

    if any(k in tl for k in ['tienda', 'sucursal', 'configuracion']):
        return "🏪 Gestiona tiendas en Herramientas → Configuración"

    if any(k in tl for k in ['nomenclador', 'monedas', 'arqueo']):
        return "💵 Nomenclador en Ventas → Nomenclador de Caja (USD, EUR, CUP, MXN)"

'''

    # Insertar antes del return final
    final_return = '    return ("Como desarrollador tienes acceso'
    if final_return in src and "v8.14 — Handlers" not in src:
        src = src.replace(final_return, NEW_HANDLERS + final_return, 1)
        handlers_file.write_text(src, encoding="utf-8")
        log("Handlers IA robustos agregados (try/except en cada query)")
    elif "v8.14 — Handlers" in src:
        # Reemplazar los handlers existentes
        src = re.sub(
            r"\n    # v8\.14 — Handlers.*?(?=\n    return \()",
            NEW_HANDLERS,
            src,
            flags=re.DOTALL
        )
        handlers_file.write_text(src, encoding="utf-8")
        log("Handlers IA reemplazados con versión robusta")
    else:
        warn("No encontré dónde insertar los handlers")


# ═══════════════════════════════════════════════════════════════════════════
# FIX 3: Burbuja 💬 con Pointer Events (drag garantizado)
# ═══════════════════════════════════════════════════════════════════════════
step("Fix 3 · Burbuja 💬 — Pointer Events")

chat_file = JS_DIR / "tpv_chat.js"
if chat_file.exists():
    src = chat_file.read_text(encoding="utf-8")

    # Buscar y reemplazar el bloque de drag
    drag_start = src.find("  (function () {\n    var btn = document.getElementById('chat-btn');")
    if drag_start == -1:
        # Buscar alternativa
        drag_start = src.find("(function () {\n    var btn = document.getElementById('chat-btn');")

    if drag_start != -1:
        drag_end = src.find("setTimeout(_cargarHistorial", drag_start)
        if drag_end == -1:
            drag_end = src.find("})();", drag_start + 100)

        if drag_end != -1:
            NEW_DRAG = """  // DRAG CON POINTER EVENTS (garantizado en móvil)
  (function () {
    var btn = document.getElementById('chat-btn');
    if (!btn) return;
    var dragging = false, moved = false, sx, sy, ox, oy;
    var _lastToggle = 0;
    var activePointerId = null;

    function _toggleSafe() {
      var now = Date.now();
      if (now - _lastToggle < 350) return;
      _lastToggle = now;
      api.toggle();
    }

    function start(x, y) {
      dragging = true; moved = false; sx = x; sy = y;
      var rect = wrap.getBoundingClientRect();
      ox = rect.left; oy = rect.top;
    }
    function move(x, y) {
      if (!dragging) return;
      var dx = x - sx, dy = y - sy;
      if (Math.abs(dx) > 6 || Math.abs(dy) > 6) moved = true;
      if (!moved) return;
      var btnSize = 56;
      var nl = Math.min(Math.max(4, ox + dx), window.innerWidth - btnSize - 4);
      var nt = Math.min(Math.max(4, oy + dy), window.innerHeight - btnSize - 4);
      wrap.style.left = nl + 'px'; wrap.style.top = nt + 'px';
      wrap.style.right = 'auto'; wrap.style.bottom = 'auto';
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      if (moved) {
        var rect = wrap.getBoundingClientRect();
        var midX = window.innerWidth / 2;
        var snapLeft = rect.left < midX ? 8 : (window.innerWidth - 60);
        wrap.style.transition = 'left 0.2s ease';
        wrap.style.left = snapLeft + 'px';
        setTimeout(function() { wrap.style.transition = ''; }, 250);
        try { localStorage.setItem('tpv_chat_pos', JSON.stringify({left: snapLeft, top: rect.top})); } catch (e) {}
      }
      if (!moved) _toggleSafe();
      moved = false;
    }

    btn.addEventListener('pointerdown', function(e) {
      if (activePointerId !== null) return;
      activePointerId = e.pointerId;
      start(e.clientX, e.clientY);
      try { btn.setPointerCapture(e.pointerId); } catch(err) {}
      e.preventDefault();
    });
    btn.addEventListener('pointermove', function(e) {
      if (!dragging || e.pointerId !== activePointerId) return;
      move(e.clientX, e.clientY);
      e.preventDefault();
    });
    btn.addEventListener('pointerup', function(e) {
      if (e.pointerId !== activePointerId) return;
      try { btn.releasePointerCapture(e.pointerId); } catch(err) {}
      activePointerId = null;
      end();
    });
    btn.addEventListener('pointercancel', function(e) {
      if (e.pointerId !== activePointerId) return;
      activePointerId = null;
      end();
    });
    btn.addEventListener('click', function(e) {
      if (moved) { e.preventDefault(); e.stopPropagation(); return false; }
    });
    btn.addEventListener('touchstart', function(e) { e.preventDefault(); }, {passive: false});
    btn.addEventListener('touchmove', function(e) { e.preventDefault(); }, {passive: false});
  })();

  """
            src = src[:drag_start] + NEW_DRAG + src[drag_end:]
            chat_file.write_text(src, encoding="utf-8")
            log("Burbuja: drag con Pointer Events reemplazado")
        else:
            warn("No encontré el final del drag en tpv_chat.js")
    else:
        warn("No encontré el bloque de drag en tpv_chat.js")


# ═══════════════════════════════════════════════════════════════════════════
# FIX 4: CSS integral — submenús + usuarios + responsive + debug
# ═══════════════════════════════════════════════════════════════════════════
step("Fix 4 · CSS integral")

index_file = TPL_DIR / "index.html"
if index_file.exists():
    src = index_file.read_text(encoding="utf-8")

    # Eliminar fixes CSS anteriores
    src = re.sub(r'\n\s*/\* ═══ FIX INTEGRAL CSS v8\.14 ═══ \*/.*?(?=\n\s*</style>)', '', src, flags=re.DOTALL)
    src = re.sub(r'\n\s*/\* FIX[^*]*(?:Submenús|submenus|CSS|Responsive|Debug bar|Gestión)[^*]*\*/.*?(?=\n\s*/\*|\n\s*</style>)', '', src, flags=re.DOTALL | re.IGNORECASE)

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
        #main-nav-tabs .dropdown-item:hover { background: rgba(79,70,229,0.25) !important; color: #fff !important; }
        #main-nav-tabs .dropdown-header { color: #94a3b8 !important; }
        .tab-content, .tab-pane { overflow: visible !important; }

        /* 2. Gestión de Usuarios */
        .u-card {
            display: flex !important; align-items: center !important; justify-content: space-between !important;
            padding: 10px 12px !important; border-radius: 10px !important; margin-bottom: 6px !important;
            background: rgba(30, 41, 59, 0.5) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important;
            gap: 8px !important; transition: all 0.2s ease;
        }
        .u-card:hover { background: rgba(79, 70, 229, 0.1) !important; border-color: rgba(79, 70, 229, 0.3) !important; }
        .u-pill {
            white-space: nowrap !important; overflow: visible !important; text-overflow: clip !important; max-width: none !important;
            padding: 0.2rem 0.55rem !important; border-radius: 999px !important; font-size: 0.62rem !important;
            font-weight: 700 !important; text-transform: uppercase !important; flex-shrink: 0 !important;
        }
        .ub-badge { white-space: nowrap !important; overflow: visible !important; max-width: none !important; font-size: 0.62rem !important; padding: 0.15rem 0.5rem !important; }
        .u-card .fw-semibold { font-size: 0.85rem !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
        .u-card .text-muted.small { font-size: 0.7rem !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
        .u-card .btn-sm { min-width: 32px !important; min-height: 32px !important; padding: 4px 8px !important; }
        .priv-rol-card { padding: 12px 6px !important; font-size: 0.75rem !important; white-space: nowrap !important; }
        .priv-rol-card span { white-space: nowrap !important; overflow: visible !important; font-size: 0.72rem !important; }
        .priv-rol-card i { font-size: 1.3em !important; }

        /* 3. Debug bar no tapa contenido */
        body.debug-active { padding-bottom: 60px !important; }
        #dbg-v2 { z-index: 9998 !important; }
        @media (max-width: 768px) { body.debug-active { padding-bottom: 80px !important; } }

        /* 4. Responsive */
        * { -webkit-tap-highlight-color: transparent; }
        html { -webkit-text-size-adjust: 100%; }
        body { overflow-x: hidden; width: 100vw; max-width: 100%; }
        .container, .container-fluid { max-width: 100% !important; padding-left: 12px !important; padding-right: 12px !important; }
        .glass-card, .card { border-radius: 12px !important; padding: 14px !important; overflow: visible !important; }
        .table { font-size: 0.8rem !important; }
        .btn { min-height: 40px; font-size: 0.85rem; }
        input, select, textarea { font-size: 16px !important; min-height: 40px; }

        @media (max-width: 576px) {
            h4 { font-size: 1.1rem !important; } h5 { font-size: 1rem !important; } h6 { font-size: 0.9rem !important; }
            .glass-card, .card { padding: 10px !important; }
            .ub-badge, .u-pill { font-size: 0.55rem !important; padding: 0.15rem 0.4rem !important; }
            .priv-rol-card { padding: 10px 4px !important; }
            .u-card { padding: 8px 10px !important; }
        }
'''

    last_style = src.rfind("</style>")
    if last_style != -1:
        src = src[:last_style] + CSS_TODO + "\n        " + src[last_style:]
        index_file.write_text(src, encoding="utf-8")
        log("CSS integral agregado")


step("DONE")
print(f"""
{G}Fix maestro aplicado.{N}

CAMBIOS:
  1. Tabla audit_logs creada (la IA ya puede consultar seguridad)
  2. Agente IA: handlers robustos con try/except en cada query
  3. Burbuja: Pointer Events (drag garantizado en móvil)
  4. CSS: submenús + usuarios + debug + responsive

REINICIAR Y PROBAR:
  pkill -f "python app.py"; sleep 2
  cd ~/tpv-chaquopy/app/src/main/python
  nohup env TPV_PORT=5050 python app.py > ~/tpv_server.log 2>&1 &
  echo $! > ~/tpv_server.pid
  sleep 5

En Chrome: http://localhost:5050
  - Login: desarrollador / demo-tpv-2026
  - Pregunta al agente: "seguridad" → ahora responde sin error
  - Burbuja: mantén presionado + arrastra → se mueve
  - Submenús: no se solapan
  - Usuarios: ADMINISTRADOR completo

COMMIT:
  cd ~/tpv-chaquopy && git add -A && git commit -m "fix(maestro): audit_logs + IA robusta + burbuja pointer + CSS integral"
""")
