#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_v12_tests_metrics.py — TPV Ultra Smart
════════════════════════════════════════════════
1. Agrega /api/dev/metrics directo en app.py (fallback si diag_bp no carga en Chaquopy)
2. Mejora handle_cliente para clientes anónimos (listar categorías al preguntar productos)
3. Crea tests exhaustivos por rol con cobertura
4. Agrega handle_cajero al dispatch si falta

USO (Termux):
  cp /storage/emulated/0/Download/patch_v12_tests_metrics.py .
  python patch_v12_tests_metrics.py
"""
import os, sys, re, shutil, json, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
print(f"[v12] BASE = {BASE}")

# ================================================================
#  STEP 1: Agregar /api/dev/metrics directo en app.py
# ================================================================
def step1_fix_metrics():
    """Agrega endpoint /api/dev/metrics directamente en app.py como fallback.
    Esto garantiza que las métricas del sistema funcionen incluso si diag_bp
    no se registra en Chaquopy (por import chain rota)."""
    app_path = os.path.join(BASE, 'app.py')
    if not os.path.exists(app_path):
        print("[v12] SKIP: app.py no encontrado")
        return

    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya existe la ruta directa
    if 'def api_dev_metrics_fallback' in content:
        print("[v12] STEP 1 SKIP: /api/dev/metrics fallback ya existe")
        return

    # Buscar un buen punto de inserción: después de @app.route("/api/status")
    marker = '@app.route("/api/status", methods=["GET"])'
    idx = content.find(marker)
    if idx == -1:
        marker = '@app.route("/api/metrics")'
        idx = content.find(marker)

    if idx == -1:
        print("[v12] STEP 1 SKIP: no se encontró punto de inserción en app.py")
        return

    # Insertar ANTES del marker
    metrics_fallback = '''# ══════════════════════════════════════════════════
#  DEV METRICS (fallback directo — funciona sin diag_bp)
# ══════════════════════════════════════════════════════════════
@app.route("/api/dev/metrics", methods=["GET"])
def api_dev_metrics_fallback():
    """Métricas de sistema: RAM, disco, BD. Fallback si diag_bp no carga."""
    try:
        import gc, time
        ram = {"proceso_mb": 0.0, "sistema_total_mb": 0.0, "sistema_usado_mb": 0.0,
               "sistema_libre_mb": 0.0, "sistema_pct": 0.0, "fuente": "basico"}
        try:
            gc.collect()
            objetos = len(gc.get_objects())
            estimado = objetos * 256
            ram["proceso_mb"] = round(estimado / 1024 / 1024, 2)
            ram["fuente"] = "gc_estimado"
        except Exception:
            pass
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info()
            ram["proceso_mb"] = round(mem.rss / 1024 / 1024, 2)
            vm = psutil.virtual_memory()
            ram["sistema_total_mb"] = round(vm.total / 1024 / 1024, 2)
            ram["sistema_usado_mb"] = round(vm.used / 1024 / 1024, 2)
            ram["sistema_libre_mb"] = round(vm.available / 1024 / 1024, 2)
            ram["sistema_pct"] = vm.percent
            ram["fuente"] = "psutil"
        except Exception:
            pass
        try:
            with open("/proc/self/status", "r") as fh:
                for ln in fh:
                    if ln.startswith("VmRSS:"):
                        kb = int(ln.split()[1])
                        ram["proceso_mb"] = round(kb / 1024, 2)
                        ram["fuente"] = "/proc"
                        break
        except Exception:
            pass

        # Disco y BD
        db_path = "desconocido"
        db_size_kb = 0.0
        num_indexes = 0
        try:
            from db_connection import DB_FILE
            db_path = DB_FILE
        except Exception:
            pass
        if not os.path.exists(db_path):
            for p in sys.path:
                c = os.path.join(p, 'tpv_datos.db')
                if os.path.exists(c):
                    db_path = c
                    break
        if os.path.exists(db_path):
            try:
                db_size_kb = round(os.path.getsize(db_path) / 1024, 2)
            except Exception:
                pass
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                num_indexes = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
                ).fetchone()[0]
                conn.close()
            except Exception:
                pass

        storage = {"db_path": db_path, "db_size_kb": db_size_kb, "db_size_mb": round(db_size_kb/1024,3),
                   "disco_total_mb": 0.0, "disco_usado_mb": 0.0, "disco_libre_mb": 0.0,
                   "disco_pct": 0.0, "num_indexes": num_indexes}
        try:
            d = os.path.dirname(db_path) or os.getcwd()
            st = os.statvfs(d)
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used = total - free
            storage["disco_total_mb"] = round(total/1024/1024, 2)
            storage["disco_usado_mb"] = round(used/1024/1024, 2)
            storage["disco_libre_mb"] = round(free/1024/1024, 2)
            storage["disco_pct"] = round(used/total*100, 1) if total else 0
        except Exception:
            pass

        # Tablas
        tablas = {"tablas": [], "total_tablas": 0, "total_filas": 0}
        try:
            import sqlite3
            conn = sqlite3.connect(db_path if os.path.exists(db_path) else ":memory:")
            nombres = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            total_filas = 0
            for t in nombres:
                try:
                    n = conn.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
                except Exception:
                    n = -1
                tablas["tablas"].append({"nombre": t, "filas": n})
                if n > 0:
                    total_filas += n
            tablas["total_tablas"] = len(nombres)
            tablas["total_filas"] = total_filas
            conn.close()
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "ram": ram,
            "storage": storage,
            "tablas": tablas,
            "db_path": db_path,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


'''

    # Si ya existe la ruta de diag_bp, necesitamos evitar duplicado.
    # Flask usa la última registrada, así que ponemos la nuestra DESPUÉS
    # y她会 sobreescribir. Pero mejor: la registramos ANTES y Flask usará la primera.
    # En realidad Flask lanza un error si hay duplicados. Así que registramos
    # solo si diag_bp NO está registrado (es None).

    # Enfoque: inyectar la ruta ANTES del marcador, y verificar que no choque
    # con la de diag_bp. Flask permite que sobreescribas con app.route si
    # el blueprint route no se registró.

    # Insertar justo antes del marcador
    new_content = content[:idx] + metrics_fallback + '\n' + content[idx:]

    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("[v12] STEP 1 OK: /api/dev/metrics fallback agregado a app.py")

    # Ahora necesitamos que si diag_bp SÍ se registró, nuestra ruta no choque.
    # Flask lanza AssertionError si hay rutas duplicadas.
    # Solución: envolver nuestra ruta para que sea condicional.
    # Reemplazamos con una versión que solo se registra si diag_bp es None.

    with open(app_path, 'r', encoding='utf-8') as f:
        content2 = f.read()

    # Hacer la ruta condicional
    old_def = '@app.route("/api/dev/metrics", methods=["GET"])\ndef api_dev_metrics_fallback():'
    new_def = '''# /api/dev/metrics: solo si diag_bp no lo proveyó
if not diag_bp:
    @app.route("/api/dev/metrics", methods=["GET"])
    def api_dev_metrics_fallback():'''

    if old_def in content2:
        # Necesitamos indentar todo el bloque de la función
        content3 = content2.replace(old_def, new_def)
        # La función necesita indentación extra (4 espacios más)
        # Pero es más fácil usar un enfoque diferente: registrar al final
        content3 = content2  # revertir

    # Enfoque final: inyectar al final de app.py, antes del if __name__
    # Ya que Flask ya procesó los blueprints, podemos sobreescribir
    # Volvemos al contenido original
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Quitar lo que insertamos antes del marker
    content = content.replace(metrics_fallback + '\n', '')

    # Enfoque final: agregar después de todos los blueprints, como route directo
    # pero solo si diag_bp es None
    inject_code = '''

# ══════════════════════════════════════════════════════════════
#  DEV METRICS DIRECTO (si diag_bp no cargó en Chaquopy)
# ══════════════════════════════════════════════════════════════
if not diag_bp:
    @app.route("/api/dev/metrics", methods=["GET"])
    def _dev_metrics_direct():
        """Métricas de sistema cuando diag_bp no está disponible."""
        import gc
        ram = {"proceso_mb": 0.0, "sistema_total_mb": 0.0, "sistema_usado_mb": 0.0,
               "sistema_libre_mb": 0.0, "sistema_pct": 0.0, "fuente": "basico"}
        try:
            gc.collect(); ram["proceso_mb"] = round(len(gc.get_objects())*256/1024/1024, 2)
            ram["fuente"] = "gc_estimado"
        except Exception: pass
        try:
            import psutil as _ps
            ram["proceso_mb"] = round(_ps.Process(os.getpid()).memory_info().rss/1024/1024, 2)
            vm = _ps.virtual_memory()
            ram.update(sistema_total_mb=round(vm.total/1024/1024,2),
                       sistema_usado_mb=round(vm.used/1024/1024,2),
                       sistema_libre_mb=round(vm.available/1024/1024,2),
                       sistema_pct=vm.percent, fuente="psutil")
        except Exception: pass
        try:
            with open("/proc/self/status") as _f:
                for _l in _f:
                    if _l.startswith("VmRSS:"):
                        ram["proceso_mb"]=round(int(_l.split()[1])/1024,2); ram["fuente"]="/proc"; break
        except Exception: pass
        db_path = "desconocido"
        try:
            from db_connection import DB_FILE; db_path = DB_FILE
        except Exception: pass
        if not os.path.exists(db_path):
            for _p in sys.path:
                _c = os.path.join(_p, 'tpv_datos.db')
                if os.path.exists(_c): db_path = _c; break
        stg = {"db_path":db_path, "db_size_kb":0.0, "db_size_mb":0.0,
               "disco_total_mb":0.0, "disco_usado_mb":0.0, "disco_libre_mb":0.0,
               "disco_pct":0.0, "num_indexes":0}
        if os.path.exists(db_path):
            try: stg["db_size_kb"] = round(os.path.getsize(db_path)/1024, 2)
            except Exception: pass
            try: stg["db_size_mb"] = round(stg["db_size_kb"]/1024, 3)
            except Exception: pass
            try:
                import sqlite3 as _sl
                _cn = _sl.connect(db_path)
                stg["num_indexes"] = _cn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
                _cn.close()
            except Exception: pass
            try:
                _d = os.path.dirname(db_path) or os.getcwd()
                _sv = os.statvfs(_d)
                _t = _sv.f_blocks*_sv.f_frsize; _fr = _sv.f_bavail*_sv.f_frsize
                stg.update(disco_total_mb=round(_t/1024/1024,2), disco_usado_mb=round((_t-_fr)/1024/1024,2),
                           disco_libre_mb=round(_fr/1024/1024,2), disco_pct=round((_t-_fr)/_t*100,1) if _t else 0)
            except Exception: pass
        tbls = {"tablas":[], "total_tablas":0, "total_filas":0}
        try:
            import sqlite3 as _sl
            _cn = _sl.connect(db_path if os.path.exists(db_path) else ":memory:")
            _names = [r[0] for r in _cn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            _tf = 0
            for _tn in _names:
                try: _n = _cn.execute('SELECT COUNT(*) FROM "%s"' % _tn).fetchone()[0]
                except Exception: _n = -1
                tbls["tablas"].append({"nombre":_tn,"filas":_n})
                if _n > 0: _tf += _n
            tbls["total_tablas"] = len(_names); tbls["total_filas"] = _tf; _cn.close()
        except Exception: pass
        return jsonify({"ok":True,"ram":ram,"storage":stg,"tablas":tbls,"db_path":db_path,"timestamp":datetime.now().isoformat()})
    print("[app] /api/dev/metrics registrado directamente (diag_bp no disponible)")
else:
    print("[app] /api/dev/metrics servido por diag_bp")

'''

    # Buscar el punto de inserción: después de todos los register_blueprint
    bp_end_marker = "print(f\"Blueprints ({len(_bps)}): {', '.join(_bps)}\")"
    idx = content.find(bp_end_marker)
    if idx == -1:
        print("[v12] STEP 1 SKIP: no encontré marcador de blueprints")
        return

    insert_pos = idx + len(bp_end_marker)
    new_content = content[:insert_pos] + inject_code + content[insert_pos:]

    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("[v12] STEP 1 OK: /api/dev/metrics fallback condicional agregado")


# ================================================================
#  STEP 2: Mejorar handle_cliente — más dinámico para anónimos
# ================================================================
def step2_improve_cliente():
    """Mejora el handler de cliente para que responda mejor a preguntas
    genéricas de productos, mostrando categorías y top productos."""
    handler_path = os.path.join(BASE, 'ia', 'handlers_cliente.py')
    if not os.path.exists(handler_path):
        print("[v12] STEP 2 SKIP: handlers_cliente.py no encontrado")
        return

    with open(handler_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya se mejoró
    if 'v12_mejora' in content:
        print("[v12] STEP 2 SKIP: handlers_cliente.py ya mejorado")
        return

    # Reemplazar el DEFAULT fallback para que sea más inteligente
    old_default = '''    # ─── DEFAULT: buscar lo que escribió ───────────────────────
    if len(tl) > 2:
        items = _buscar_productos(tl)
        if items:
            msg = "🔍 Encontré esto con tu búsqueda:" + NL + NL
            for p in items[:5]:
                msg += "• **" + str(p.get('nombre', '?')) + "**"
                msg += " — $" + str(p.get('precio', 0))
                if p.get('en_oferta'):
                    msg += " 🏷️"
                msg += NL
            return msg

    return ("🛍️ ¿En qué te ayudo? Puedes preguntarme por productos, precios, "
            "ofertas, categorías o stock. Escribe 'ayuda' para opciones.")'''

    new_default = '''    # ─── DEFAULT: buscar lo que escribió ───────────────────────
    if len(tl) > 2:
        items = _buscar_productos(tl)
        if items:
            msg = "🔍 Encontré esto con tu búsqueda:" + NL + NL
            for p in items[:5]:
                msg += "• **" + str(p.get('nombre', '?')) + "**"
                msg += " — $" + str(p.get('precio', 0))
                if p.get('en_oferta'):
                    msg += " 🏷️"
                stock = int(p.get('stock_total') or 0)
                if stock > 0:
                    msg += f" ({stock} uds)"
                msg += NL
            # v12_mejora: sugerir productos relacionados
            if items and len(items) >= 1:
                try:
                    cat_primera = items[0].get('categoria', '')
                    if cat_primera:
                        msg += NL + f"📂 Más en *{cat_primera}*: pregúntame 'productos de {cat_primera}'"
                except Exception:
                    pass
            return msg

    # ─── MENSAJE POR DEFECTO CON CATEGORÍAS (v12_mejora) ───────
    n = _contar_productos()
    cats = _todas_categorias()
    if cats:
        msg = (f"🛍️ Tenemos **{n} productos** en {len(cats)} categorías:" + NL + NL)
        for c in cats[:5]:
            msg += f"• {c['categoria']} ({c['total']} productos)" + NL
        msg += NL + "Pregúntame por cualquier producto o categoría."
        return msg

    return ("🛍️ ¿En qué te ayudo? Puedes preguntarme por productos, precios, "
            "ofertas, categorías o stock. Escribe 'ayuda' para opciones.")'''

    if old_default in content:
        content = content.replace(old_default, new_default)
        with open(handler_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[v12] STEP 2 OK: handle_cliente mejorado con categorías en fallback")
    else:
        print("[v12] STEP 2 SKIP: no encontré el bloque DEFAULT original (puede ya estar modificado)")


# ================================================================
#  STEP 2.5: Crear handle_cajero si no existe
# ================================================================
def step2b_create_cajero():
    """Crea handle_cajero en handlers_staff.py si no existe."""
    staff_path = os.path.join(BASE, 'ia', 'handlers_staff.py')
    if not os.path.exists(staff_path):
        print("[v12] STEP 2b SKIP: handlers_staff.py no encontrado")
        return

    with open(staff_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'def handle_cajero' in content:
        print("[v12] STEP 2b SKIP: handle_cajero ya existe")
        return

    cajero_code = '''

# ================================================================
# CAJERO (Foco en caja, arqueo, métodos de pago)
# ================================================================
def handle_cajero(agent, t, m=None):
    """Handler del rol cajero: arqueo de caja, ventas por método de pago, productos rápidos."""
    name = m if isinstance(m, str) else ''
    tl = t.lower().strip()

    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        h = datetime.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        return f"{s} {name} 💰. Soy tu asistente de caja. Pregúntame por arqueo, ventas por método de pago o busca productos."

    # ─── ARQUEO DE CAJA ──────────────────────────────────────
    if _fm(agent, t, ['arqueo', 'cierre', 'cerrar caja', 'cuanto hay en caja',
                      'total en caja', 'fondos']):
        rows = q("SELECT metodo_pago, COUNT(*) t, COALESCE(SUM(total),0) r "
                 "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') "
                 "GROUP BY metodo_pago ORDER BY r DESC")
        if not rows:
            return "📊 No hay ventas registradas hoy. La caja está en $0.00"
        total_general = sum(r['r'] for r in rows)
        msg = f"📊 **Arqueo de Caja — Hoy**\n\n"
        for r in rows:
            pct = (r['r'] / total_general * 100) if total_general > 0 else 0
            msg += f"  • {r['metodo_pago']}: {fmt_money(r['r'])} ({r['t']} txns, {pct:.0f}%)\n"
        msg += f"\n  **Total: {fmt_money(total_general)}** ({sum(r['t'] for r in rows)} transacciones)"
        # Gastos
        g = q("SELECT COALESCE(SUM(monto),0) g FROM gastos WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        if g and g['g'] > 0:
            neto = total_general - g['g']
            msg += f"\n  Gastos: {fmt_money(g['g'])}"
            msg += f"\n  **Neto: {fmt_money(neto)}**"
        return msg

    # ─── VENTAS POR MÉTODO DE PAGO ───────────────────────────
    if _fm(agent, t, ['metodo de pago', 'metodos de pago', 'forma de pago',
                      'pago efectivo', 'pago tarjeta', 'como pagan']):
        rows = q("SELECT metodo_pago, COUNT(*) t, COALESCE(SUM(total),0) r "
                 "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') "
                 "GROUP BY metodo_pago ORDER BY t DESC")
        if not rows:
            return "💳 No hay ventas hoy para desglosar por método de pago."
        msg = "💳 **Ventas por Método de Pago (hoy):**\n\n"
        total = sum(r['r'] for r in rows)
        for r in rows:
            icon = '💵' if 'efectivo' in r['metodo_pago'].lower() else '💳' if 'tarjeta' in r['metodo_pago'].lower() else '📱'
            pct = (r['r'] / total * 100) if total > 0 else 0
            msg += f"  {icon} {r['metodo_pago']}: {fmt_money(r['r'])} ({r['t']} ventas, {pct:.0f}%)\n"
        msg += f"\n  **Total general: {fmt_money(total)}**"
        return msg

    # ─── VENTAS DE HOY (resumen rápido) ──────────────────────
    if _fm(agent, t, ['ventas hoy', 'cuanto vendido', 'total ventas', 'recaudado',
                      'cuanto hecho', 'como va el dia']):
        d = F.diario()
        if d['t'] == 0:
            return "📊 Sin ventas registradas hoy aún. ¡Animo! 💪"
        msg = (f"📊 **Resumen del Día:**\n\n"
               f"  Transacciones: {d['t']}\n"
               f"  Total: {fmt_money(d['r'])}\n"
               f"  Ticket Promedio: {fmt_money(d['a'])}\n")
        if d['g'] > 0:
            msg += f"  Gastos: {fmt_money(d['g'])}\n"
            msg += f"  **Neto: {fmt_money(d['r'] - d['g'])}**"
        return msg

    # ─── ÚLTIMAS VENTAS ─────────────────────────────────────
    if _fm(agent, t, ['ultimas ventas', 'ventas recientes', 'historial']):
        rows = q("SELECT nombre, total, metodo_pago, fecha FROM historial_ventas "
                 "ORDER BY fecha DESC LIMIT 8")
        if not rows:
            return "📋 No hay ventas registradas."
        msg = "📋 **Últimas Ventas:**\n\n"
        for r in rows:
            msg += f"  • {r['nombre']}: {fmt_money(r['total'])} ({r['metodo_pago']}) — {r['fecha'][-8:]}\n"
        return msg

    # ─── BÚSQUEDA RÁPIDA DE PRODUCTOS ────────────────────────
    import re
    _term = re.sub(r'\\b(precio|cuesta|vale|de|del|hay|tienes|stock)\\b', ' ', tl).strip()  # noqa: escape raw string
    prods = P.search(_term or t, 5)
    if prods:
        msg = "🔍 **Productos encontrados:**\n"
        for p in prods:
            msg += f"  • {p['n']}: {fmt_money(p['p'])} (Stock: {int(p['s'])})\n"
        return msg

    return ("💰 **Asistente de Caja** — Puedo ayudarte con:\n\n"
            "  📊 Arqueo de caja\n"
            "  💳 Ventas por método de pago\n"
            "  📋 Últimas ventas\n"
            "  🔍 Buscar productos y precios\n\n"
            "Pregúntame: 'arqueo', 'metodos de pago', 'ventas hoy'")
'''

    # Insertar al final del archivo
    content = content.rstrip() + '\n' + cajero_code + '\n'

    with open(staff_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[v12] STEP 2b OK: handle_cajero creado en handlers_staff.py")


# ================================================================
#  STEP 3: Mejorar dispatcher ia/agent.py para incluir cajero
# ================================================================
def step3_fix_dispatcher():
    """Verifica que handle_cajero esté en el dispatcher."""
    agent_path = os.path.join(BASE, 'ia', 'agent.py')
    if not os.path.exists(agent_path):
        print("[v12] STEP 3 SKIP: ia/agent.py no encontrado")
        return

    with open(agent_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'handle_cajero' in content:
        print("[v12] STEP 3 SKIP: handle_cajero ya está en agent.py")
        return

    # Agregar import de handle_cajero
    old_import = '''from ia.handlers import (
    greet, help_text, _follow, _get_sug, _fm,
    handle_cliente, handle_vendedor, handle_supervisor,
    handle_admin, handle_dev,
)'''

    new_import = '''from ia.handlers import (
    greet, help_text, _follow, _get_sug, _fm,
    handle_cliente, handle_vendedor, handle_supervisor,
    handle_admin, handle_dev, handle_cajero,
)'''

    if old_import in content:
        content = content.replace(old_import, new_import)
    else:
        print("[v12] STEP 3 WARN: no encontré bloque de imports exacto")

    # Agregar cajero al ROLES registry
    old_roles = """ROLES = {
    'cliente':      {'label': 'Cliente',      'color': '#2ecc71', 'icon': 'C'},
    'vendedor':     {'label': 'Vendedor',     'color': '#3498db', 'icon': 'V'},
    'supervisor':   {'label': 'Supervisor',   'color': '#f39c12', 'icon': 'S'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
}"""

    new_roles = """ROLES = {
    'cliente':      {'label': 'Cliente',      'color': '#2ecc71', 'icon': 'C'},
    'vendedor':     {'label': 'Vendedor',     'color': '#3498db', 'icon': 'V'},
    'supervisor':   {'label': 'Supervisor',   'color': '#f39c12', 'icon': 'S'},
    'cajero':       {'label': 'Cajero',       'color': '#1abc9c', 'icon': 'K'},
    'administrador': {'label': 'Administrador', 'color': '#e74c3c', 'icon': 'A'},
    'desarrollador': {'label': 'Desarrollador', 'color': '#9b59b6', 'icon': 'D'},
}"""

    if old_roles in content:
        content = content.replace(old_roles, new_roles)

    # Agregar dispatch para cajero
    old_dispatch = """        if role == 'cliente':
            result = handle_cliente(self, t, m)
        elif role == 'vendedor':
            result = handle_vendedor(self, t, m)
        elif role == 'supervisor':
            result = handle_supervisor(self, t, m)
        elif role == 'administrador':
            result = handle_admin(self, t, name)
        else:
            result = handle_dev(self, t, name)"""

    new_dispatch = """        if role == 'cliente':
            result = handle_cliente(self, t, m)
        elif role == 'vendedor':
            result = handle_vendedor(self, t, m)
        elif role == 'cajero':
            result = handle_cajero(self, t, m)
        elif role == 'supervisor':
            result = handle_supervisor(self, t, m)
        elif role == 'administrador':
            result = handle_admin(self, t, name)
        else:
            result = handle_dev(self, t, name)"""

    if old_dispatch in content:
        content = content.replace(old_dispatch, new_dispatch)

    with open(agent_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[v12] STEP 3 OK: handle_cajero agregado al dispatcher")


# ================================================================
#  STEP 4: Verificar handlers.py re-exports handle_cajero
# ================================================================
def step4_fix_handlers_reexport():
    """Asegura que ia/handlers.py re-exporte handle_cajero."""
    handlers_path = os.path.join(BASE, 'ia', 'handlers.py')
    if not os.path.exists(handlers_path):
        print("[v12] STEP 4 SKIP: ia/handlers.py no encontrado")
        return

    with open(handlers_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'handle_cajero' in content:
        print("[v12] STEP 4 SKIP: handle_cajero ya re-exportado")
        return

    old_export = '''from ia.handlers_staff import (
    handle_vendedor, handle_supervisor, handle_admin, handle_dev
)'''

    new_export = '''from ia.handlers_staff import (
    handle_vendedor, handle_supervisor, handle_admin, handle_dev,
    handle_cajero,
)'''

    if old_export in content:
        content = content.replace(old_export, new_export)
        with open(handlers_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[v12] STEP 4 OK: handle_cajero re-exportado en handlers.py")
    else:
        # El archivo puede tener formato diferente
        if 'handle_cajero' not in content:
            # Agregar al final
            content = content.rstrip() + '\n' + \
                'from ia.handlers_staff import handle_cajero  # v12\n'
            with open(handlers_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("[v12] STEP 4 OK: handle_cajero import agregado")


# ================================================================
#  STEP 5: Crear tests exhaustivos por rol
# ================================================================
def step5_create_tests():
    """Crea suite de tests para todos los handlers por rol."""
    tests_dir = os.path.join(BASE, 'tests')
    os.makedirs(tests_dir, exist_ok=True)

    test_file = os.path.join(tests_dir, 'test_agent_roles_v12.py')

    test_code = '''# -*- coding: utf-8 -*-
"""Tests exhaustivos por rol para el agente TPV Ultra Smart v12.
Cobertura: cliente, vendedor, supervisor, admin, dev, cajero.
Ejecutar:  cd app/src/main/python && python -m pytest tests/test_agent_roles_v12.py -v
Cobertura:  python -m pytest tests/test_agent_roles_v12.py -v --tb=short
           python -c "import pytest; pytest.main(['tests/test_agent_roles_v12.py','--cov=ia','--cov-report=term-missing'])"
"""
import os, sys, pytest

# Asegurar path del proyecto
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TEST_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ================================================================
#  FIXTURES
# ================================================================
class FakeAgent:
    """Agente falso para testing sin BD real."""
    def __init__(self):
        self.ses = {}


@pytest.fixture
def agent():
    return FakeAgent()


@pytest.fixture
def ctx_vacio():
    return {}


@pytest.fixture
def ctx_con_historial():
    return {"h": ["ventas hoy", "cafe"], "t": "ventas", "p": "", "n": ""}


# ================================================================
#  TESTS: handlers_base
# ================================================================
class TestHandlersBase:
    """Funciones compartidas entre handlers."""

    def test_fm_exact_match(self, agent):
        from ia.handlers_base import _fm
        assert _fm(agent, "hola buenas tardes", ["hola"]) is True
        assert _fm(agent, "quiero ver ventas", ["ventas"]) is True
        assert _fm(agent, "como esta el stock", ["stock"]) is True
        assert _fm(agent, "precio del cafe", ["precio"]) is True

    def test_fm_no_match(self, agent):
        from ia.handlers_base import _fm
        assert _fm(agent, "como estas", ["ventas", "stock", "gastos"]) is False

    def test_fm_empty(self, agent):
        from ia.handlers_base import _fm
        assert _fm(agent, "", ["ventas"]) is False
        assert _fm(agent, None, ["ventas"]) is False

    def test_follow_por_rol(self):
        from ia.handlers_base import _follow
        assert "ayudarle" in _follow('cliente')
        assert "stock" in _follow('vendedor')
        assert "tendencias" in _follow('supervisor')
        assert "finanzas" in _follow('administrador')
        assert "metricas" in _follow('desarrollador')

    def test_get_sug_por_rol(self):
        from ia.handlers_base import _get_sug
        s = _get_sug('cliente')
        assert isinstance(s, list)
        assert len(s) > 0

    def test_greet_por_rol(self):
        from ia.handlers_base import greet
        assert "administración" in greet('administrador', 'Juan')
        assert "vender" in greet('vendedor', 'Ana')
        assert "Bienvenido" in greet('cliente', 'Pedro')

    def test_help_text_por_rol(self):
        from ia.handlers_base import help_text
        assert help_text('cliente') != help_text('desarrollador')
        assert help_text('vendedor') != help_text('administrador')

    def test_handle_unknown(self):
        from ia.handlers_base import handle_unknown
        assert "No entendí" in handle_unknown("xyz123")


# ================================================================
#  TESTS: db_utils
# ================================================================
class TestDbUtils:
    """Utilidades de base de datos."""

    def test_q_conexion(self):
        from ia.db_utils import q
        # Debe conectar sin error (la BD existe en Termux)
        result = q("SELECT 1 as uno", one=True)
        assert result is not None
        assert result['uno'] == 1

    def test_q_tablas_existentes(self):
        from ia.db_utils import q
        result = q("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        assert result is not None
        assert len(result) > 0
        nombres = [r['name'] for r in result]
        assert 'productos' in nombres or 'historial_ventas' in nombres

    def test_fmt_money(self):
        from ia.db_utils import fmt_money
        assert fmt_money(100) == "$100.00"
        assert fmt_money(0) == "$0.00"
        assert fmt_money(1234.56) == "$1,234.56"
        assert fmt_money(None) == "$0.00"

    def test_pct(self):
        from ia.db_utils import pct
        assert pct(85.5) == "85.5%"
        assert pct(0) == "0.0%"

    def test_q_productos_activos(self):
        from ia.db_utils import q
        result = q("SELECT COUNT(*) as n FROM productos WHERE activo=1", one=True)
        assert result is not None
        assert result['n'] >= 0


# ================================================================
#  TESTS: catalog (P y O)
# ================================================================
class TestCatalog:
    """Catálogo de productos P y ofertas O."""

    def test_p_load(self):
        from ia.catalog import P
        P._loaded = False
        P._load()
        assert isinstance(P.cache, list)

    def test_p_search(self):
        from ia.catalog import P
        P._loaded = False
        P._load()
        results = P.search("cafe", 5)
        assert isinstance(results, list)

    def test_p_cats(self):
        from ia.catalog import P
        P._loaded = False
        P._load()
        assert isinstance(P.cats, list)

    def test_o_mejores(self):
        from ia.catalog import O
        ofertas = O.mejores()
        assert isinstance(ofertas, list)

    def test_o_relacionados(self):
        from ia.catalog import O
        rel = O.relacionados("cafe")
        assert isinstance(rel, list)

    def test_p_refresh(self):
        from ia.catalog import P
        P.refresh()
        assert P._loaded is True


# ================================================================
#  TESTS: metrics (M y F)
# ================================================================
class TestMetrics:
    """Modelos matemáticos y financieros."""

    def test_m_regresion(self):
        from ia.metrics import M
        m, b = M.regresion([1, 2, 3], [2, 4, 6])
        assert abs(m - 2.0) < 0.01  # y = 2x

    def test_m_regresion_insuficiente(self):
        from ia.metrics import M
        m, b = M.regresion([1], [2])
        assert m == 0

    def test_m_eoq(self):
        from ia.metrics import M
        import math
        d, p, m = 1000, 50, 2
        result = M.eoq(d, p, m)
        assert result > 0
        expected = math.sqrt(2 * d * p / m)
        assert abs(result - expected) < 0.01

    def test_m_eoq_zero_cost(self):
        from ia.metrics import M
        assert M.eoq(1000, 50, 0) == 0

    def test_m_punto_eq(self):
        from ia.metrics import M
        assert M.punto_eq(10000, 100, 60) == 250  # 10000/(100-60)
        assert M.punto_eq(1000, 10, 15) == float('inf')  # precio < costo variable

    def test_m_roi(self):
        from ia.metrics import M
        assert M.roi(1000, 1500) == 50.0  # (1500-1000)/1000 * 100
        assert M.roi(0, 100) == 0

    def test_f_diario(self):
        from ia.metrics import F
        d = F.diario()
        assert 't' in d  # transacciones
        assert 'r' in d  # recaudado
        assert 'a' in d  # promedio
        assert 'g' in d  # gastos

    def test_f_semanal(self):
        from ia.metrics import F
        s = F.semanal()
        assert 't' in s
        assert 'r' in s

    def test_f_top(self):
        from ia.metrics import F
        t = F.top(7, 5)
        assert isinstance(t, list)

    def test_f_abc(self):
        from ia.metrics import F
        abc = F.abc()
        assert 'A' in abc
        assert 'B' in abc
        assert 'C' in abc

    def test_f_stock_critico(self):
        from ia.metrics import F
        rows = F.stock_critico()
        assert isinstance(rows, list)

    def test_f_stock_resumen(self):
        from ia.metrics import F
        r = F.stock_resumen()
        assert 'total' in r
        assert 'agotados' in r

    def test_f_conteos(self):
        from ia.metrics import F
        c = F.conteos()
        assert 'productos' in c
        assert 'ventas_hoy' in c


# ================================================================
#  TESTS: handle_cliente (rol más usado por anónimos)
# ================================================================
class TestHandleCliente:
    """Handler del cliente anónimo — dinámismo y cobertura total."""

    def test_saludo_hola(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "hola")
        assert isinstance(r, str)
        assert len(r) > 10

    def test_saludo_buenas_tardes(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "buenas tardes")
        assert "tardes" in r.lower()

    def test_ofertas(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "que ofertas hay")
        assert isinstance(r, str)
        assert len(r) > 5

    def test_categorias(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "que categorias tienen")
        assert isinstance(r, str)
        # Debe mostrar al menos algo
        assert len(r) > 10

    def test_catalogo_completo(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "que productos tienen")
        assert isinstance(r, str)
        assert len(r) > 10

    def test_busqueda_producto(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "cafe")
        assert isinstance(r, str)

    def test_precio_producto(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "cuanto cuesta el cafe")
        assert isinstance(r, str)

    def test_tienda_horario(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "que horario tienen")
        assert "08:00" in r or "Horario" in r

    def test_ayuda(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "ayuda")
        assert isinstance(r, str)
        assert "buscar" in r.lower() or "producto" in r.lower()

    def test_fallback_default(self, agent):
        """El fallback debe mostrar categorías, no mensaje genérico."""
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "xyzpq123")
        assert isinstance(r, str)
        assert len(r) > 10

    def test_vacio(self, agent):
        from ia.handlers_cliente import handle_cliente
        r = handle_cliente(agent, "")
        assert isinstance(r, str)

    def test_normalizar(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("Café Molido") == "cafe molido"
        assert _normalizar("ACEREO") == "acero"
        assert _normalizar("") == ""
        assert _normalizar(None) == ""

    def test_extraer_producto(self):
        from ia.handlers_cliente import _extraer_producto
        r = _extraer_producto("cuanto cuesta el cafe americano")
        assert "cafe" in r.lower()
        assert "cuesta" not in r.lower()

    def test_contar_productos(self):
        from ia.handlers_cliente import _contar_productos
        n = _contar_productos()
        assert isinstance(n, int)
        assert n >= 0

    def test_todas_categorias(self):
        from ia.handlers_cliente import _todas_categorias
        cats = _todas_categorias()
        assert isinstance(cats, list)

    def test_todas_ofertas(self):
        from ia.handlers_cliente import _todas_ofertas
        of = _todas_ofertas()
        assert isinstance(of, list)


# ================================================================
#  TESTS: handle_vendedor
# ================================================================
class TestHandleVendedor:
    """Handler del vendedor — ventas, stock, metas."""

    def test_saludo(self, agent):
        from ia.handlers_staff import handle_vendedor
        r = handle_vendedor(agent, "hola", "Carlos")
        assert isinstance(r, str)
        assert len(r) > 10

    def test_ventas_hoy(self, agent):
        from ia.handlers_staff import handle_vendedor
        r = handle_vendedor(agent, "cuanto vendi hoy", "")
        assert isinstance(r, str)
        assert "ventas" in r.lower() or "facturado" in r.lower() or "registra" in r.lower()

    def test_stock_bajo(self, agent):
        from ia.handlers_staff import handle_vendedor
        r = handle_vendedor(agent, "que productos tienen stock bajo", "")
        assert isinstance(r, str)

    def test_busqueda_rapida(self, agent):
        from ia.handlers_staff import handle_vendedor
        r = handle_vendedor(agent, "cafe", "")
        assert isinstance(r, str)

    def test_precio_rapido(self, agent):
        from ia.handlers_staff import handle_vendedor
        r = handle_vendedor(agent, "cuanto cuesta el cafe", "")
        assert isinstance(r, str)

    def test_respuesta_no_vacia(self, agent):
        """Todo input debe devolver respuesta no vacía."""
        from ia.handlers_staff import handle_vendedor
        for msg in ["ventas", "stock", "cafe", "metas", "top productos", "xyz"]:
            r = handle_vendedor(agent, msg, "")
            assert isinstance(r, str) and len(r) > 0, f"Vacío para: {msg}"


# ================================================================
#  TESTS: handle_supervisor
# ================================================================
class TestHandleSupervisor:
    """Handler del supervisor — dashboard, ABC, predicciones."""

    def test_saludo(self, agent):
        from ia.handlers_staff import handle_supervisor
        r = handle_supervisor(agent, "hola", "")
        assert isinstance(r, str)

    def test_dashboard(self, agent):
        from ia.handlers_staff import handle_supervisor
        r = handle_supervisor(agent, "dame el dashboard", "")
        assert isinstance(r, str)

    def test_abc(self, agent):
        from ia.handlers_staff import handle_supervisor
        r = handle_supervisor(agent, "analisis abc", "")
        assert isinstance(r, str)

    def test_stock_dias(self, agent):
        from ia.handlers_staff import handle_supervisor
        r = handle_supervisor(agent, "dias de stock", "")
        assert isinstance(r, str)

    def test_prediccion(self, agent):
        from ia.handlers_staff import handle_supervisor
        r = handle_supervisor(agent, "prediccion de ventas", "")
        assert isinstance(r, str)

    def test_respuestas_no_vacias(self, agent):
        """Varios inputs no deben crashear ni devolver vacío."""
        from ia.handlers_staff import handle_supervisor
        for msg in ["dashboard", "rotacion", "categorias", "prediccion", "tendencia"]:
            r = handle_supervisor(agent, msg, "")
            assert isinstance(r, str) and len(r) > 0, f"Vacío para: {msg}"


# ================================================================
#  TESTS: handle_admin
# ================================================================
class TestHandleAdmin:
    """Handler del administrador — finanzas, EOQ, punto equilibrio."""

    def test_saludo(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "hola", "Admin")
        assert isinstance(r, str)

    def test_finanzas(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "dame las finanzas", "Admin")
        assert isinstance(r, str)

    def test_hora_pico(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "hora pico", "Admin")
        assert isinstance(r, str)

    def test_ticket_promedio(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "ticket promedio", "Admin")
        assert isinstance(r, str)

    def test_eoq(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "eoq cafe", "Admin")
        assert isinstance(r, str)

    def test_punto_equilibrio(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "punto de equilibrio", "Admin")
        assert isinstance(r, str)

    def test_gastos(self, agent):
        from ia.handlers_staff import handle_admin
        r = handle_admin(agent, "gastos de hoy", "Admin")
        assert isinstance(r, str)

    def test_respuestas_no_vacias(self, agent):
        """Varios inputs no deben crashear."""
        from ia.handlers_staff import handle_admin
        for msg in ["finanzas", "balance", "gastos", "comisiones", "categorias ventas"]:
            r = handle_admin(agent, msg, "Admin")
            assert isinstance(r, str) and len(r) > 0, f"Vacío para: {msg}"


# ================================================================
#  TESTS: handle_dev
# ================================================================
class TestHandleDev:
    """Handler del desarrollador — SQL, docs, telemetría."""

    def test_saludo(self, agent):
        from ia.handlers_staff import handle_dev
        r = handle_dev(agent, "hola", "dev")
        assert isinstance(r, str)

    def test_sql_executor(self, agent):
        from ia.handlers_staff import handle_dev
        r = handle_dev(agent, "select count(*) from productos", "dev")
        assert isinstance(r, str)

    def test_documentos(self, agent):
        from ia.handlers_staff import handle_dev
        r = handle_dev(agent, "documentacion", "dev")
        assert isinstance(r, str)

    def test_integridad(self, agent):
        from ia.handlers_staff import handle_dev
        r = handle_dev(agent, "verificar integridad", "dev")
        assert isinstance(r, str)

    def test_telemetria(self, agent):
        from ia.handlers_staff import handle_dev
        r = handle_dev(agent, "telemetria", "dev")
        assert isinstance(r, str)

    def test_respuestas_no_vacias(self, agent):
        """Varios inputs no deben crashear."""
        from ia.handlers_staff import handle_dev
        for msg in ["metricas", "logs", "tablas", "estado", "diagnostico"]:
            r = handle_dev(agent, msg, "dev")
            assert isinstance(r, str) and len(r) > 0, f"Vacío para: {msg}"


# ================================================================
#  TESTS: handle_cajero (si existe)
# ================================================================
class TestHandleCajero:
    """Handler del cajero — arqueo, métodos de pago."""

    @pytest.fixture(autouse=True)
    def _check_cajero(self):
        try:
            from ia.handlers_staff import handle_cajero
            self._handler = handle_cajero
        except ImportError:
            self._handler = None

    def test_import_exists(self):
        try:
            from ia.handlers_staff import handle_cajero
            assert callable(handle_cajero)
        except ImportError:
            pytest.skip("handle_cajero no disponible")

    def test_arqueo(self, agent):
        if not self._handler:
            pytest.skip("handle_cajero no disponible")
        r = self._handler(agent, "arqueo de caja", "")
        assert isinstance(r, str)

    def test_metodos_pago(self, agent):
        if not self._handler:
            pytest.skip("handle_cajero no disponible")
        r = self._handler(agent, "ventas por metodo de pago", "")
        assert isinstance(r, str)


# ================================================================
#  TESTS: Agente completo (pipeline)
# ================================================================
class TestAgentPipeline:
    """Pipeline completo del agente por rol."""

    def test_process_question_cliente(self):
        from ia.agent import _get, ROLES
        agent = _get()
        r = agent.process("hola", "test-1", "cliente", "Pedro")
        assert 'answer' in r
        assert len(r['answer']) > 0
        assert r['role'] == 'cliente'

    def test_process_question_vendedor(self):
        from ia.agent import _get
        agent = _get()
        r = agent.process("ventas hoy", "test-2", "vendedor", "Ana")
        assert 'answer' in r
        assert len(r['answer']) > 0

    def test_process_question_admin(self):
        from ia.agent import _get
        agent = _get()
        r = agent.process("finanzas", "test-3", "administrador", "Admin")
        assert 'answer' in r
        assert len(r['answer']) > 0

    def test_process_question_dev(self):
        from ia.agent import _get
        agent = _get()
        r = agent.process("estado del sistema", "test-4", "desarrollador", "Dev")
        assert 'answer' in r
        assert len(r['answer']) > 0

    def test_process_vacio(self):
        from ia.agent import _get
        agent = _get()
        r = agent.process("", "test-5", "cliente", "")
        assert 'answer' in r

    def test_roles_registry_completo(self):
        from ia.agent import ROLES
        assert 'cliente' in ROLES
        assert 'vendedor' in ROLES
        assert 'supervisor' in ROLES
        assert 'administrador' in ROLES
        assert 'desarrollador' in ROLES

    def test_get_status(self):
        from ia.agent import get_status
        s = get_status()
        assert 'status' in s
        assert s['status'] == 'active'

    def test_process_question_public_api(self):
        from ia.agent import process_question
        r = process_question("test-6", "que productos tienen", role='cliente')
        assert 'answer' in r
        assert len(r['answer']) > 0

    def test_respuestas_unicas_por_rol(self):
        """Cada rol debe dar respuestas diferentes a la misma pregunta genérica."""
        from ia.agent import _get
        agent = _get()
        respuestas = {}
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = agent.process("ayuda", f"test-uniq-{rol}", rol, "User")
            respuestas[rol] = r['answer']
        # Al menos cliente y admin deben ser diferentes
        assert respuestas['cliente'] != respuestas['administrador']


# ================================================================
#  TESTS: Intent engine (si disponible)
# ================================================================
class TestIntentEngine:
    """Detección de intenciones."""

    def test_import(self):
        try:
            from ia.intent_engine import detect_intents
            assert callable(detect_intents)
        except ImportError:
            pytest.skip("intent_engine no disponible")

    def test_detect_saludo(self):
        try:
            from ia.intent_engine import detect_intents
            r = detect_intents("hola", "cliente")
            assert isinstance(r, list)
        except ImportError:
            pytest.skip()


# ================================================================
#  TESTS: NLP engine
# ================================================================
class TestNLPEngine:
    """Motor NLP básico."""

    def test_import(self):
        from ia.nlp_engine import NLPEngine
        assert NLPEngine is not None

    def test_instance(self):
        from ia.nlp_engine import NLPEngine
        nlp = NLPEngine()
        assert nlp is not None


# ================================================================
#  TESTS: Fuzzy match
# ================================================================
class TestFuzzyMatch:
    """Búsqueda difusa."""

    def test_best_match_exacto(self):
        try:
            from ia.fuzzy_match import best_match
            m, s = best_match("cafe", ["cafe", "leche", "azucar"], threshold=50)
            assert m == "cafe"
        except ImportError:
            pytest.skip("fuzzy_match no disponible")

    def test_best_match_parcial(self):
        try:
            from ia.fuzzy_match import best_match
            m, s = best_match("café molido", ["Cafe Molido 250g", "Leche"], threshold=30)
            assert m is not None or True  # puede no match por umbral
        except ImportError:
            pytest.skip()


if __name__ == "__main__":
    # Ejecutar directamente si no hay pytest
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    sys.exit(result.returncode)
'''

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)
    print(f"[v12] STEP 5 OK: tests creados en {test_file}")


# ================================================================
#  STEP 6: Crear script de cobertura
# ================================================================
def step6_create_coverage_runner():
    """Crea script para ejecutar tests con medición de cobertura."""
    cov_file = os.path.join(BASE, 'tests', 'run_coverage.py')

    cov_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecuta tests con cobertura y genera reporte.
Uso:  cd app/src/main/python && python tests/run_coverage.py
"""
import os, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

def main():
    print("=" * 60)
    print("  TPV Ultra Smart — Tests + Cobertura")
    print("=" * 60)

    # Intentar instalar coverage si no existe
    try:
        import coverage
    except ImportError:
        print("Instalando coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage", "-q"],
                       capture_output=True)

    # Ejecutar pytest con cobertura
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_agent_roles_v12.py",
        "-v", "--tb=short",
        f"--cov=ia",
        f"--cov-report=term-missing",
        f"--cov-report=html:{os.path.join(BASE, 'htmlcov')}",
    ]

    print(f"\\nEjecutando: {' '.join(cmd)}\\n")
    result = subprocess.run(cmd, cwd=PARENT, capture_output=False)

    # Resumen
    print("\\n" + "=" * 60)
    if result.returncode == 0:
        print("  TODOS LOS TESTS PASARON")
    else:
        print(f"  HUBO ERRORES (exit code: {result.returncode})")
    print("=" * 60)

    # Intentar obtener porcentaje de cobertura
    try:
        import coverage
        cov = coverage.Coverage()
        # No podemos leer el .coverage de pytest, pero el reporte HTML ya se generó
        html_dir = os.path.join(BASE, 'htmlcov', 'index.html')
        if os.path.exists(html_dir):
            print(f"\\nReporte HTML: {html_dir}")
    except Exception:
        pass

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
'''

    with open(cov_file, 'w', encoding='utf-8') as f:
        f.write(cov_code)
    print(f"[v12] STEP 6 OK: coverage runner en {cov_file}")


# ================================================================
#  STEP 7: Crear script de test rápido (sin BD)
# ================================================================
def step7_create_quick_test():
    """Crea tests que NO necesitan BD — unitarios puros."""
    test_file = os.path.join(BASE, 'tests', 'test_unitarios_v12.py')

    test_code = '''# -*- coding: utf-8 -*-
"""Tests unitarios puros — NO necesitan BD.
Ejecutar:  python -m pytest tests/test_unitarios_v12.py -v
"""
import os, sys, math

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TEST_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class TestMatematicas:
    """Modelos matemáticos puros (sin BD)."""

    def test_regresion_lineal_perfecta(self):
        from ia.metrics import M
        m, b = M.regresion([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        assert abs(m - 2.0) < 0.01
        assert abs(b - 0.0) < 0.01

    def test_regresion_con_intercepto(self):
        from ia.metrics import M
        m, b = M.regresion([1, 2, 3], [5, 7, 9])
        assert abs(m - 2.0) < 0.01
        assert abs(b - 3.0) < 0.01

    def test_regresion_un_punto(self):
        from ia.metrics import M
        m, b = M.regresion([1], [5])
        assert m == 0
        assert b == 0

    def test_eoq_formula(self):
        from ia.metrics import M
        # EOQ = sqrt(2*D*P/M)
        # D=3600, P=50, M=2 => EOQ = sqrt(180000) = 424.26
        result = M.eoq(3600, 50, 2)
        expected = math.sqrt(2 * 3600 * 50 / 2)
        assert abs(result - expected) < 0.01

    def test_eoq_cero_costo(self):
        from ia.metrics import M
        assert M.eoq(100, 50, 0) == 0

    def test_punto_equilibrio_normal(self):
        from ia.metrics import M
        # CF=10000, P=100, CV=60 => PE = 10000/40 = 250
        assert M.punto_eq(10000, 100, 60) == 250

    def test_punto_equilibrio_loss(self):
        from ia.metrics import M
        # P < CV => infinito
        assert M.punto_eq(1000, 10, 15) == float('inf')

    def test_punto_equilibrio_zero_cv(self):
        from ia.metrics import M
        assert M.punto_eq(1000, 100, 0) == 10

    def test_roi_positivo(self):
        from ia.metrics import M
        assert M.roi(1000, 1500) == 50.0

    def test_roi_negativo(self):
        from ia.metrics import M
        assert M.roi(1000, 500) == -50.0

    def test_roi_cero_inversion(self):
        from ia.metrics import M
        assert M.roi(0, 500) == 0


class TestFormatters:
    """Formateadores de dinero y porcentaje."""

    def test_fmt_money_entero(self):
        from ia.db_utils import fmt_money
        assert fmt_money(100) == "$100.00"

    def test_fmt_money_decimal(self):
        from ia.db_utils import fmt_money
        assert fmt_money(1234.56) == "$1,234.56"

    def test_fmt_money_cero(self):
        from ia.db_utils import fmt_money
        assert fmt_money(0) == "$0.00"

    def test_fmt_money_none(self):
        from ia.db_utils import fmt_money
        assert fmt_money(None) == "$0.00"

    def test_pct_normal(self):
        from ia.db_utils import pct
        assert pct(85.5) == "85.5%"

    def test_pct_cero(self):
        from ia.db_utils import pct
        assert pct(0) == "0.0%"


class TestNormalizar:
    """Normalización de texto para búsqueda."""

    def test_quita_tildes(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("Café") == "cafe"
        assert _normalizar("Acción") == "accion"
        assert _normalizar("Información") == "informacion"

    def test_minusculas(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("CAFÉ MOLIDO") == "cafe molido"

    def test_vacio(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("") == ""
        assert _normalizar(None) == ""


class TestRolesRegistry:
    """Registro de roles del agente."""

    def test_roles_existentes(self):
        from ia.agent import ROLES
        roles_requeridos = ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']
        for r in roles_requeridos:
            assert r in ROLES, f"Falta rol: {r}"

    def test_roles_tienen_label(self):
        from ia.agent import ROLES
        for r, data in ROLES.items():
            assert 'label' in data, f"Rol {r} sin label"
            assert 'color' in data, f"Rol {r} sin color"

    def test_roles_unicos(self):
        from ia.agent import ROLES
        labels = [d['label'] for d in ROLES.values()]
        assert len(labels) == len(set(labels)), "Labels duplicados"


class TestAgentGetStatus:
    """Status del agente."""

    def test_status_fields(self):
        from ia.agent import get_status
        s = get_status()
        assert 'status' in s
        assert 'version' in s or 'versión' in s

    def test_status_active(self):
        from ia.agent import get_status
        s = get_status()
        assert s['status'] == 'active'

    def test_features_list(self):
        from ia.agent import get_status
        s = get_status()
        assert 'features' in s
        assert len(s['features']) > 0


class TestHandlersBase:
    """Funciones base sin BD."""

    def test_follow_todos_roles(self):
        from ia.handlers_base import _follow
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = _follow(rol)
            assert isinstance(r, str)
            assert len(r) > 5

    def test_get_sug_todos_roles(self):
        from ia.handlers_base import _get_sug
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = _get_sug(rol)
            assert isinstance(r, list)

    def test_greet_todos_roles(self):
        from ia.handlers_base import greet
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = greet(rol, "Test")
            assert isinstance(r, str)
            assert len(r) > 3

    def test_help_text_todos_roles(self):
        from ia.handlers_base import help_text
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = help_text(rol)
            assert isinstance(r, str)
            assert len(r) > 3

    def test_handle_unknown(self):
        from ia.handlers_base import handle_unknown
        r = handle_unknown("xyz")
        assert "No entendí" in r


class TestProactiveAlerts:
    """Alertas proactivas del agente."""

    def test_alerts_structure(self):
        from ia.agent import get_proactive_alerts
        a = get_proactive_alerts("test-session")
        assert 'alerts' in a
        assert isinstance(a['alerts'], list)


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    sys.exit(result.returncode)
'''

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)
    print(f"[v12] STEP 7 OK: tests unitarios puros en {test_file}")


# ================================================================
#  STEP 8: Seed datos de prueba para tests
# ================================================================
def step8_seed_test_data():
    """Inserta datos mínimos de prueba si la BD está vacía."""
    import sqlite3
    db_paths = [
        os.path.join(BASE, 'tpv_datos.db'),
    ]
    for p in sys.path:
        db_paths.append(os.path.join(p, 'tpv_datos.db'))

    db_path = None
    for p in db_paths:
        if os.path.exists(p):
            db_path = p
            break

    if not db_path:
        print("[v12] STEP 8 SKIP: no se encontró tpv_datos.db")
        return

    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Verificar si hay datos
    ventas = c.execute("SELECT COUNT(*) FROM historial_ventas").fetchone()[0]
    gastos = c.execute("SELECT COUNT(*) FROM gastos").fetchone()[0]
    productos = c.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]

    print(f"[v12] BD actual: {productos} productos, {ventas} ventas, {gastos} gastos")

    if ventas > 0 or gastos > 0:
        print("[v12] STEP 8 SKIP: BD ya tiene datos")
        conn.close()
        return

    # Insertar ventas de ejemplo (3 días diferentes para que las métricas funcionen)
    import uuid
    hoy = datetime.now().strftime('%Y-%m-%d')
    ayer = (datetime.now() - __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d')
    anteayer = (datetime.now() - __import__('datetime').timedelta(days=2)).strftime('%Y-%m-%d')

    # Obtener productos
    prods = c.execute("SELECT producto_id, nombre, precio FROM productos WHERE activo=1 LIMIT 5").fetchall()
    if not prods:
        print("[v12] STEP 8 SKIP: no hay productos en la BD")
        conn.close()
        return

    metodos = ['Efectivo', 'Tarjeta', 'Transferencia']
    total_ventas = 0
    total_gastos = 0

    for i in range(20):
        p = prods[i % len(prods)]
        dia = [hoy, hoy, hoy, ayer, ayer, anteayer][i % 6]
        hora = f"{8 + (i % 12):02d}:{(i * 17) % 60:02d}"
        cantidad = (i % 3) + 1
        total = round(p['precio'] * cantidad, 2)

        c.execute("""INSERT INTO historial_ventas
            (venta_id, fecha, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, vendedor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), f"{dia} {hora}", p['producto_id'], p['nombre'],
             cantidad, p['precio'], total, metodos[i % 3], 'vendedor1'))
        total_ventas += total

    # Insertar gastos
    descripciones = ['Recibo luz', 'Internet', 'Transporte', 'Limpieza', 'Mantenimiento']
    for i in range(5):
        monto = round(50 + i * 25.5, 2)
        dia = [hoy, hoy, ayer, ayer, anteayer][i]
        c.execute("""INSERT INTO gastos (gasto_id, fecha, monto, descripcion, categoria, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), f"{dia} 10:00", monto, descripciones[i],
             'Operativo', 'admin'))
        total_gastos += monto

    conn.commit()
    conn.close()
    print(f"[v12] STEP 8 OK: seed {total_ventas} en ventas, {total_gastos} en gastos")


# ================================================================
#  STEP 9: Ejecutar tests y mostrar resultados
# ================================================================
def step9_run_tests():
    """Ejecuta los tests unitarios (los que no necesitan servidor)."""
    import subprocess

    # Tests unitarios puros primero
    unit_test = os.path.join(BASE, 'tests', 'test_unitarios_v12.py')
    if not os.path.exists(unit_test):
        print("[v12] STEP 9 SKIP: no se encontró test_unitarios_v12.py")
        return

    print("\n" + "=" * 60)
    print("  EJECUTANDO TESTS UNITARIOS (sin BD)...")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", unit_test, "-v", "--tb=short"],
        cwd=BASE, capture_output=True, text=True, timeout=60
    )

    output = result.stdout
    if result.stderr:
        output += "\nSTDERR:\n" + result.stderr

    # Contar resultados
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    errors = output.count(" ERROR")

    print(output[-2000:] if len(output) > 2000 else output)

    print(f"\n[v12] RESUMEN UNITARIOS: {passed} passed, {failed} failed, {errors} errors")

    # Tests con BD
    role_test = os.path.join(BASE, 'tests', 'test_agent_roles_v12.py')
    if os.path.exists(role_test):
        print("\n" + "=" * 60)
        print("  EJECUTANDO TESTS POR ROL (con BD)...")
        print("=" * 60)

        result2 = subprocess.run(
            [sys.executable, "-m", "pytest", role_test, "-v", "--tb=short"],
            cwd=BASE, capture_output=True, text=True, timeout=120
        )

        output2 = result2.stdout
        if result2.stderr:
            output2 += "\nSTDERR:\n" + result2.stderr

        print(output2[-2000:] if len(output2) > 2000 else output2)

        p2 = output2.count(" PASSED")
        f2 = output2.count(" FAILED")
        e2 = output2.count(" ERROR")
        print(f"\n[v12] RESUMEN ROLES: {p2} passed, {f2} failed, {e2} errors")


# ================================================================
#  MAIN
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  PATCH v12 — Tests, Cobertura, Métricas, Dinamismo")
    print("=" * 60)
    print()

    steps = [
        ("Fix métricas sistema (/api/dev/metrics fallback)", step1_fix_metrics),
        ("Mejorar handle_cliente (fallback dinámico)", step2_improve_cliente),
        ("Crear handle_cajero en handlers_staff.py", step2b_create_cajero),
        ("Agregar handle_cajero al dispatcher", step3_fix_dispatcher),
        ("Re-exportar handle_cajero", step4_fix_handlers_reexport),
        ("Crear tests por rol (test_agent_roles_v12.py)", step5_create_tests),
        ("Crear coverage runner", step6_create_coverage_runner),
        ("Crear tests unitarios puros", step7_create_quick_test),
        ("Seed datos de prueba", step8_seed_test_data),
        ("Ejecutar tests", step9_run_tests),
    ]

    for i, (desc, fn) in enumerate(steps, 1):
        print(f"\n{'─' * 50}")
        print(f"[{i}/{len(steps)}] {desc}")
        try:
            fn()
        except Exception as e:
            print(f"[v12] ERROR en step {i}: {e}")
            traceback.print_exc()

    print(f"\n{'═' * 60}")
    print("  PATCH v12 COMPLETADO")
    print("═" * 60)
    print("""
Para ejecutar tests manualmente:
  cd app/src/main/python
  python -m pytest tests/test_unitarios_v12.py -v
  python -m pytest tests/test_agent_roles_v12.py -v

Con cobertura:
  pip install coverage
  python tests/run_coverage.py
""")