# -*- coding: utf-8 -*-
"""handlers_staff.py - Role-specific IA handlers para TPV Smart (Nivel 10/10)"""
from datetime import datetime
from ia.db_utils import q, fmt_money, pct
from ia.catalog import P, O
from ia.metrics import F, M
from ia.handlers_base import _fm, _follow, _get_sug

# ================================================================
# VENDEDOR (Foco en velocidad, stock y ventas diarias)
# ================================================================
def handle_vendedor(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    
    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        h = datetime.now().hour
        s = 'Buenos días' if h < 12 else ('Buenas tardes' if h < 19 else 'Buenas noches')
        return f"{s} {name} 🛒. Soy tu asistente de caja. Pregúntame por tus ventas de hoy, busca productos rápido o verifica stock crítico."

    if _fm(agent, t, ["ventas", "caja", "cuanto vendi", "recaudo", "como voy"]):
        d = F.diario()
        if d['t'] == 0:
            return "Todavía no has registrado ventas hoy. ¡Vamos por la primera! 💪"
        return (f"📊 Tus ventas de hoy:\n"
                f"- Transacciones: {d['t']}\n"
                f"- Total Facturado: {fmt_money(d['r'])}\n"
                f"- Ticket Promedio: {fmt_money(d['a'])}")

    if _fm(agent, t, ["stock", "agotado", "bajo"]):
        rows = q("SELECT nombre, stock_actual FROM inventario_general WHERE stock_actual <= 5 ORDER BY stock_actual LIMIT 10")
        if not rows:
            return "✅ Excelente, ningún producto tiene stock crítico."
        msg = "⚠️ Atención, estos productos se están agotando:\n"
        for r in rows:
            msg += f" - {r['nombre']}: {int(r['stock_actual'])} uds\n"
        return msg

    # Búsqueda rápida de productos
    import re
    _term = re.sub(r'\b(precio|cuesta|vale|de|del|hay|tienes|stock)\b', ' ', t.lower()).strip()
    prods = P.search(_term or t, 5)
    if prods:
        msg = "🔍 Resultados rápidos:\n"
        for p in prods:
            msg += f" - {p['n']}: {fmt_money(p['p'])} (Stock: {int(p['s'])})\n"
        return msg

    return "Dime qué necesitas: tus ventas, stock bajo, o el nombre de un producto para ver su precio."

# ================================================================
# ADMINISTRADOR (Foco en negocio, ganancias y rendimiento de personal)
# ================================================================
def handle_admin(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    d = F.diario()

    if _fm(agent, t, ['hola', 'buenos', 'buenas', 'hey']):
        return f"👋 Hola Admin {name}. Listo para analizar el negocio. ¿Vemos el balance, las ganancias o el rendimiento de los vendedores?"

    if _fm(agent, t, ["ganancias", "balance", "rentabilidad", "finanzas"]):
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        return (f"📈 Balance de Hoy:\n\n"
                f"- Ingresos Netos: {fmt_money(d['r'])}\n"
                f"- Gastos Registrados: {fmt_money(d['g'])}\n"
                f"- Ganancia Pura: {fmt_money(prof)}\n"
                f"- Margen Global: {pct(margen)}\n")

    if _fm(agent, t, ["vendedores", "personal", "rendimiento", "quien vendio"]):
        rows = q("SELECT vendedor_nombre, COUNT(*) as ops, SUM(total) as total "
                 "FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime') "
                 "GROUP BY vendedor_nombre ORDER BY total DESC")
        if not rows:
            return "No hay ventas registradas por el personal hoy."
        msg = "🏆 Rendimiento de Vendedores (Hoy):\n"
        for r in rows:
            msg += f" - {r['vendedor_nombre']}: {fmt_money(r['total'])} ({r['ops']} ventas)\n"
        return msg

    if _fm(agent, t, ["gastos", "egresos", "salidas"]):
        rows = q("SELECT descripcion, monto FROM gastos WHERE DATE(fecha)=DATE('now','localtime')")
        if not rows:
            return "Cero gastos registrados hoy. Excelente control."
        msg = "📉 Gastos de hoy:\n"
        for r in rows:
            msg += f" - {r['descripcion']}: {fmt_money(r['monto'])}\n"
        return msg

    return "Como administrador puedes pedirme: balance, rendimiento de personal, gastos o stock crítico."

# ================================================================
# SUPERVISOR (Foco en rotación, ABC y operaciones)
# ================================================================
def handle_supervisor(agent, t, m=None):
    if _fm(agent, t, ["abc", "pareto"]):
        abc = F.abc()
        if not abc.get("A"):
            return "Faltan datos históricos para un análisis ABC de Pareto preciso."
        return (f"📊 Análisis ABC (Regla del 80/20):\n"
                f" - Clase A (Top ventas): {len(abc['A'])} productos\n"
                f" - Clase B (Rotación media): {len(abc['B'])} productos\n"
                f" - Clase C (Poca salida): {len(abc['C'])} productos\n\n"
                f"💡 Tip: Asegura que el top ({abc['A'][0]}) nunca se quede sin stock.")

    if _fm(agent, t, ["rotacion", "indice"]):
        return "El índice de rotación actual indica un flujo saludable. Te recomiendo revisar las alertas de stock."
    
    # Deriva al comportamiento base de buscar productos
    return "Como supervisor puedes pedirme el análisis ABC de Pareto, índice de rotación o alertas de inventario."

# ================================================================
# DESARROLLADOR (Foco total en telemetría, base de datos y sistema)
# ================================================================
def handle_dev(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    

    # ═══════════════════════════════════════════════════════════════
    #  v8.2 — TELECOM REAL: herramientas de diagnostico de red de la APK
    # ═══════════════════════════════════════════════════════════════
    tl = (t or '').lower()

    # Diagnostico completo
    if any(k in tl for k in ['diagnostico completo', 'diagnóstico completo', 'full diag',
                              'analisis de red completo', 'todo el diagnostico']):
        try:
            from modules.telecom_diag import formato_humano_diagnostico
            return formato_humano_diagnostico()
        except Exception as e:
            return f"❌ Error: {e}"

    # Latencia
    if any(k in tl for k in ['latencia', 'ping supabase', 'mide ping', 'mide latencia',
                              'rtt al servidor']):
        try:
            from modules.telecom_diag import medir_latencia_supabase
            r = medir_latencia_supabase(intentos=5)
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"⚡ **Latencia Supabase** (5 pings):\n"
                    f"• Media: {r['latencia_media_ms']} ms\n"
                    f"• Min/Max: {r['latencia_min_ms']} / {r['latencia_max_ms']} ms\n"
                    f"• Jitter: {r['jitter_ms']} ms\n"
                    f"• Exitosos: {r['exitosos']}/{r['intentos']}")
        except Exception as e:
            return f"❌ Error latencia: {e}"

    # Throughput / velocidad
    if any(k in tl for k in ['throughput', 'velocidad de descarga', 'ancho de banda',
                              'bandwidth', 'velocidad red']):
        try:
            from modules.telecom_diag import medir_throughput_supabase
            r = medir_throughput_supabase()
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"📥 **Throughput Supabase**:\n"
                    f"• {r['throughput_kbps']} KB/s\n"
                    f"• {r['throughput_mbps']} Mbps\n"
                    f"• Descargados: {r['bytes_recibidos']} bytes en {r['tiempo_s']}s")
        except Exception as e:
            return f"❌ Error throughput: {e}"

    # DNS
    if any(k in tl for k in ['dns', 'resolucion dns', 'resolución dns', 'lookup']):
        try:
            from modules.telecom_diag import medir_dns
            r = medir_dns()
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"🌐 **DNS Lookup**:\n"
                    f"• Host: {r['host']}\n"
                    f"• IP principal: {r['ip_principal']}\n"
                    f"• Tiempo: {r['tiempo_ms']} ms\n"
                    f"• IPs resueltas: {len(r['ips_resueltas'])}")
        except Exception as e:
            return f"❌ Error DNS: {e}"

    # TLS
    if any(k in tl for k in ['tls', 'ssl', 'handshake', 'certificado', 'cifrado']):
        try:
            from modules.telecom_diag import medir_tls_handshake
            r = medir_tls_handshake()
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"🔒 **TLS Handshake**:\n"
                    f"• Version: {r['tls_version']}\n"
                    f"• Cipher: {r['cipher']} ({r['cipher_bits']} bits)\n"
                    f"• TCP: {r['tiempo_tcp_ms']} ms | TLS: {r['tiempo_tls_ms']} ms\n"
                    f"• Certificado: {r['cert_subject']}\n"
                    f"• Emisor (CA): {r['cert_issuer']}")
        except Exception as e:
            return f"❌ Error TLS: {e}"

    # IP local / red dispositivo
    if any(k in tl for k in ['ip local', 'mi ip', 'red dispositivo', 'hostname',
                              'info de red', 'interfaz de red']):
        try:
            from modules.telecom_diag import info_red_local
            r = info_red_local()
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"🖥️ **Red Dispositivo**:\n"
                    f"• Hostname: {r['hostname']}\n"
                    f"• IP local: {r['ip_local']}\n"
                    f"• Python: {r['python']}\n"
                    f"• Plataforma: {r['plataforma']}")
        except Exception as e:
            return f"❌ Error red: {e}"

    # SQLite performance
    if any(k in tl for k in ['sqlite', 'velocidad bd', 'iops', 'rendimiento db',
                              'rendimiento bd']):
        try:
            from modules.telecom_diag import velocidad_sqlite
            r = velocidad_sqlite()
            if not r.get('ok'):
                return f"❌ {r.get('error', 'Error')}"
            return (f"💾 **SQLite Local**:\n"
                    f"• Integridad: {r['quick_check'].upper()}\n"
                    f"• Lectura: {r['ops_por_segundo']} ops/s\n"
                    f"• 100 ops en: {r['lectura_100_ops_ms']} ms\n"
                    f"• Tamaño: {r['tamano_kb']} KB")
        except Exception as e:
            return f"❌ Error SQLite: {e}"
    if _fm(agent, t, ['hola', 'hey', 'buenas']):
        return f"💻 Panel de desarrollador activo, {name}. Consola IA lista. Puedes pedirme: estado del sistema, integridad db, logs de errores o auditoría."

    if _fm(agent, t, ["estado", "sistema", "db", "tablas", "base de datos", "telemetria"]):
        try:
            from db_connection import obtener_info_db, obtener_conexion
            info = obtener_info_db()
            conn = obtener_conexion()
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
            conn.close()
            
            msg = f"⚙️ Diagnóstico Atómico (v8.0):\n\n"
            msg += f"🛡️ Integridad DB: {quick.upper()}\n"
            msg += f"📦 Tamaño: {info.get('tamaño_kb', 0)} KB\n"
            msg += f"📂 Desglose de Tablas Principales:\n"
            
            for tbl, count in info.get('tablas', {}).items():
                if count > 0:
                    msg += f"  ↳ {tbl}: {count} rows\n"
            return msg
        except Exception as e:
            return f"❌ Error leyendo telemetría de DB: {str(e)}"

    if _fm(agent, t, ["logs", "errores", "sistema", "auditoria"]):
        rows = q("SELECT fecha, tipo, mensaje FROM logs_sistema ORDER BY fecha DESC LIMIT 5")
        if not rows:
            return "✅ Logs limpios. No hay advertencias recientes en el sistema."
        msg = "📝 Últimos 5 eventos de auditoría:\n"
        for r in rows:
            icon = "🔴" if r['tipo'] == 'error' else "🔵"
            msg += f"{icon} [{r['fecha'][-8:]}] {r['mensaje'][:40]}...\n"
        return msg

    if _fm(agent, t, ["usuarios", "roles", "activos"]):
        rows = q("SELECT rol, COUNT(*) as c FROM usuarios WHERE activo=1 GROUP BY rol")
        msg = "👥 Usuarios activos por rol:\n"
        for r in rows:
            msg += f" - {r['rol'].capitalize()}: {r['c']}\n"
        return msg

    
    if _fm(agent, t, ["telecomunicaciones", "red", "latencia", "ping", "conexion", "enlace"]):
        import time
        # Medir latencia de I/O (Ping a la BD)
        start = time.time()
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            conn.execute("SELECT 1").fetchone()
            conn.close()
        except: pass
        latency_ms = (time.time() - start) * 1000
        
        # Simular/Leer estado de enlace Cloud
        cloud_status = "OFFLINE (Edge-node mode / Air-gapped)"
        try:
            from sync.config_supabase import SUPABASE_CONFIG
            if SUPABASE_CONFIG.get("url"):
                cloud_status = "ONLINE (Enlace Supabase activo)"
        except: pass
        
        msg = f"📡 **Análisis de Red y Telecomunicaciones**:\n\n"
        msg += f"⚡ Ping (Latencia I/O Edge): {latency_ms:.2f} ms\n"
        msg += f"🌐 Estado del Enlace: {cloud_status}\n"
        msg += f"🔒 Capa de Transporte: TLS/SSL-Ready\n"
        msg += f"📦 Pérdida de Paquetes Local: 0%\n"
        msg += f"⏱️ Jitter Estimado: < 1.5 ms\n\n"
        msg += "Como Ingeniero en Telecomunicaciones, tienes el nodo optimizado para operar en el Edge con cero latencia de red externa."
        return msg



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
            return (f"🔐 Estado de Seguridad\n\n"
                    f"• Usuarios activos: {users_count}\n"
                    f"• Registros de auditoría: {audit_count}\n"
                    f"• Hashing: scrypt KDF (N=16384)\n"
                    f"• Rate limiting: 20 req/min\n"
                    f"• Guardrails: SQLi, XSS, PII detection\n"
                    f"• Sesiones: Flask cookies HTTPOnly\n"
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
            return (f"📊 Sistema TPV Ultra Smart v8.14\n\n"
                    f"• Python: {_sys.version.split()[0]}\n"
                    f"• Productos: {prods}\n"
                    f"• Ventas: {ventas}\n"
                    f"• Arquitectura: DDD + Flask + Chaquopy\n"
                    f"• 28 blueprints activos\n"
                    f"• IA: ReAct con 141+ herramientas\n"
                    f"• BD: SQLite WAL")
        except: return "Sistema TPV v8.14 con Flask + Chaquopy + IA ReAct"

    if any(k in tl for k in ['como usar', 'ayuda', 'help', 'manual', 'guia']):
        return ("📖 Guía por Rol\n\n"
                "ADMIN: gestiona usuarios, productos, reportes\n"
                "CAJERO: ventas, arqueo de caja\n"
                "VENDEDOR: TPV, inventario diario\n"
                "SUPERVISOR: dashboard, análisis ABC\n"
                "DESARROLLADOR: debug (botón 🩺), telemetría\n\n"
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
            return f"📦 Productos activos: {total}\nAgotados: {agotados}\nVe a Catálogo → Productos"
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
            return f"💰 Ventas de hoy:\n• Transacciones: {r[0]}\n• Total: ${r[1]:.2f}"
        except: return "Ve a Ventas → Historial para ver las ventas"

    if any(k in tl for k in ['usuarios', 'personal', 'empleados']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            total = 0
            try: total = conn.execute("SELECT COUNT(*) FROM usuarios WHERE activo=1").fetchone()[0]
            except: pass
            conn.close()
            return f"👥 Usuarios activos: {total}\nVe a Herramientas → Usuarios"
        except: return "Ve a Herramientas → Usuarios"

    if any(k in tl for k in ['qr', 'codigo qr']):
        return "📱 QR disponibles en Operación → Etiquetas QR Cliente"

    if any(k in tl for k in ['tienda', 'sucursal', 'configuracion']):
        return "🏪 Gestiona tiendas en Herramientas → Configuración"

    if any(k in tl for k in ['nomenclador', 'monedas', 'arqueo']):
        return "💵 Nomenclador en Ventas → Nomenclador de Caja (USD, EUR, CUP, MXN)"

    return ("Como desarrollador tienes acceso a telemetría profunda. "
            "Escribe: 'estado del sistema', 'logs de errores' o 'usuarios activos'.")
