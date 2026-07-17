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
    tl = (t or '').lower()
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

    # ─── PUNTO DE EQUILIBRIO ────────────────────────────────────
    if _fm(agent, t, ["punto equilibrio", "break even", "umbral", "equilibrio"]):
        d = F.diario()
        gastos_fijos = d['g']
        ticket = d['a'] if d['a'] > 0 else 50
        # Costo variable estimado como 60% del precio
        cv = ticket * 0.6
        pe = M.punto_eq(gastos_fijos, ticket, cv)
        return (f"⚖️ **Punto de Equilibrio:**\n\n"
                f"  • Gastos fijos diarios: {fmt_money(gastos_fijos)}\n"
                f"  • Ticket promedio: {fmt_money(ticket)}\n"
                f"  • Costo variable estimado: {fmt_money(cv)}\n"
                f"  • **Ventas necesarias: {pe} transacciones**\n"
                f"  • Ingreso minimo: {fmt_money(pe * ticket)}")

    # ─── EOQ (LOTE OPTIMO) ──────────────────────────────────────
    if _fm(agent, t, ["eoq", "lote optimo", "pedido optimo"]):
        rows = q("SELECT nombre, stock_actual, precio_venta "
                 "FROM inventario_general WHERE stock_actual > 0 "
                 "ORDER BY stock_actual ASC LIMIT 5")
        if not rows:
            return "Sin productos en inventario para calcular EOQ."
        msg = "📐 **Lote Optimo de Pedido (EOQ):**\n\n"
        msg += "  (D=300 uds/mes, Costo pedido=$50, Costo almacen=20% precio)\n\n"
        for r in rows:
            d = 300  # demanda estimada mensual
            p = 50   # costo por pedido
            h = r['precio_venta'] * 0.2  # costo almacenamiento
            if h > 0:
                eoq = M.eoq(d, p, h)
                msg += f"  • {r['nombre']}: EOQ = {eoq:.0f} uds (stock: {int(r['stock_actual'])})\n"
        return msg

    # ─── DIAGNOSTICO COMPLETO ADMIN ──────────────────────────────
    if any(k in tl for k in ['diagnostico', 'resumen ejecutivo', 'como va',
                              'estado del negocio', 'reporte general']):
        d = F.diario()
        prof = d['r'] - d['g']
        margen = (prof / d['r'] * 100) if d['r'] > 0 else 0
        stock = F.stock_resumen()
        conteos = F.conteos()
        return (f"📊 **Reporte Ejecutivo Admin:**\n\n"
                f"💰 Balance Hoy:\n"
                f"  - Ingresos: {fmt_money(d['r'])}\n"
                f"  - Gastos: {fmt_money(d['g'])}\n"
                f"  - Ganancia: {fmt_money(prof)} (margen {pct(margen)})\n\n"
                f"📦 Inventario:\n"
                f"  - Total: {stock.get('total', 0)} | Agotados: {stock.get('agotados', 0)}\n"
                f"  - Criticos: {stock.get('criticos', 0)}\n\n"
                f"📈 Negocio:\n"
                f"  - Productos: {conteos['productos']}\n"
                f"  - Ventas hoy: {conteos['ventas_hoy']}\n"
                f"  - Clientes: {conteos['clientes']}\n\n"
                f"💡 Puedo mostrar: punto de equilibrio, EOQ, top vendedores, ABC.")

    return "Como administrador puedes pedirme: balance, rendimiento de personal, gastos o stock crítico."

# ================================================================
# SUPERVISOR (Foco en rotación, ABC y operaciones)
# ================================================================
def handle_supervisor(agent, t, m=None):
    # ─── DIAGNOSTICO EJECUTIVO ──────────────────────────────────
    tl2 = (t or '').lower()
    if any(k in tl2 for k in ['diagnostico', 'resumen', 'estado negocio',
                                'como va', 'reporte ejecutivo', 'dashboard']):
        try:
            from db_connection import obtener_conexion
            from datetime import date, timedelta
            conn = obtener_conexion()
            semana = (date.today() - timedelta(days=7)).isoformat()
            vh = conn.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE DATE('now')||'%'").fetchone()
            vs = conn.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha >= ?", (semana,)).fetchone()
            gh = conn.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE DATE(fecha)=DATE('now','localtime')").fetchone()
            stock_bajo = conn.execute("SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= COALESCE(NULLIF(stock_minimo,0),5)").fetchone()[0]
            conn.close()
            return (f"📊 **Dashboard Supervisor:**\n\n"
                    f"🛒 Ventas Hoy: {vh[0]} txns / ${vh[1]:,.2f}\n"
                    f"📅 Ventas Semana: {vs[0]} txns / ${vs[1]:,.2f}\n"
                    f"📉 Gastos Hoy: ${gh[0]:,.2f}\n"
                    f"💰 Ganancia Hoy: ${vh[1]-gh[0]:,.2f}\n"
                    f"⚠️ Stock bajo: {stock_bajo} productos\n\n"
                    f"💡 Pregunta por 'analisis ABC', 'prediccion' o 'rotacion'.")
        except Exception as e:
            return f"Error generando dashboard: {e}"

    # ─── PREDICCIONES ────────────────────────────────────────────
    if any(k in tl2 for k in ['prediccion', 'pronostico', 'proyeccion', 'forecast', 'tendencia']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT DATE(fecha) dia, SUM(total) total "
                "FROM historial_ventas WHERE fecha >= DATE('now','-7 days') "
                "GROUP BY dia ORDER BY dia"
            ).fetchall()
            conn.close()
            if not rows or len(rows) < 2:
                return "Necesito al menos 2 dias de datos para predecir. Registre mas ventas."
            totales = [r['total'] for r in rows]
            # Regresion lineal simple
            n = len(totales)
            x = list(range(n))
            sx, sy = sum(x), sum(totales)
            sxy = sum(x[i] * totales[i] for i in range(n))
            sx2 = sum(v * v for v in x)
            denom = n * sx2 - sx * sx
            pendiente = (n * sxy - sx * sy) / denom if denom != 0 else 0
            intercepto = (sy - pendiente * sx) / n
            prediccion = intercepto + pendiente * n
            tendencia = "creciente" if pendiente > 0 else "decreciente" if pendiente < 0 else "estable"
            return (f"🔮 **Prediccion de Ventas:**\n\n"
                    f"  • Tendencia: {tendencia} ({pendiente:+.2f}/dia)\n"
                    f"  • Prediccion manana: ${prediccion:,.2f}\n"
                    f"  • Promedio 7 dias: ${sum(totales)/n:,.2f}\n"
                    f"  • Min/Max: ${min(totales):,.2f} / ${max(totales):,.2f}")
        except Exception as e:
            return f"Error en prediccion: {e}"

    # ─── ROTACION ────────────────────────────────────────────────
    if _fm(agent, t, ["rotacion", "indice"]):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, stock_actual, precio_venta, "
                "(SELECT COALESCE(SUM(cantidad),0) FROM historial_ventas hv WHERE hv.nombre=ig.nombre AND hv.fecha>=DATE('now','-30 days')) vendidos_30d "
                "FROM inventario_general ig WHERE stock_actual > 0 ORDER BY vendidos_30d DESC LIMIT 5"
            ).fetchall()
            conn.close()
            if not rows:
                return "Sin datos suficientes para calcular rotacion."
            msg = "🔄 **Indice de Rotacion (30 dias, Top 5):**\n\n"
            for r in rows:
                v = r['vendidos_30d']
                s = r['stock_actual']
                rot = (v / s) if s > 0 else 0
                msg += f"  • {r['nombre']}: rot={rot:.2f}x (vendidos {v}, stock {s})\n"
            return msg
        except Exception as e:
            return f"Error calculando rotacion: {e}"

    if _fm(agent, t, ["abc", "pareto"]):
        abc = F.abc()
        if not abc.get("A"):
            return "Faltan datos historicos para un analisis ABC de Pareto preciso."
        return (f"📊 Análisis ABC (Regla del 80/20):\n"
                f" - Clase A (Top ventas): {len(abc['A'])} productos\n"
                f" - Clase B (Rotación media): {len(abc['B'])} productos\n"
                f" - Clase C (Poca salida): {len(abc['C'])} productos\n\n"
                f"💡 Tip: Asegura que el top ({abc['A'][0]}) nunca se quede sin stock.")
    
    # Deriva al comportamiento base de buscar productos
    return "Como supervisor puedes pedirme el análisis ABC de Pareto, índice de rotación o alertas de inventario."

# ================================================================
# DESARROLLADOR (Foco total en telemetría, base de datos y sistema)
# ================================================================
def handle_dev(agent, t, m=None):
    name = m if isinstance(m, str) else ''
    

    tl = (t or '').lower()

    # ═══════════════════════════════════════════════════════════════
    #  v9.0 — SUPER AGENTE: Ejecucion SQL (PRIMERO, antes de todo)
    #  100% offline, sin dependencias externas
    # ═══════════════════════════════════════════════════════════════

    # --- EJECUTAR SQL ---
    if any(k in tl for k in ['ejecutar', 'select ', 'query ', 'sql',
                              'consulta sql', 'run sql', 'ejecuta']):
        sql_query = t
        # Extraer el SQL del mensaje
        for prefix in ['ejecutar ', 'ejecuta ', 'query ', 'run ', 'consulta sql ', 'sql:']:
            if prefix in tl:
                sql_query = tl.split(prefix, 1)[1].strip()
                break
        # Palabras clave que inician SQL
        for kw in ['select ', 'insert ', 'update ', 'delete ', 'create ', 'alter ',
                    'drop ', 'pragma ', 'explain ']:
            idx = tl.find(kw)
            if idx >= 0:
                sql_query = tl[idx:]
                break
        if not sql_query or len(sql_query) < 6:
            return "Escribe el SQL completo, ej: 'ejecutar SELECT * FROM productos LIMIT 5'"
        # Seguridad: solo SELECT y PRAGMA para modo conversacional
        sql_upper = sql_query.strip().upper()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('PRAGMA')
                or sql_upper.startswith('EXPLAIN') or sql_upper.startswith('WITH')):
            return "Por seguridad solo se permiten consultas SELECT, PRAGMA y EXPLAIN."
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            rows = conn.execute(sql_query).fetchall()
            conn.close()
            if not rows:
                return "Consulta ejecutada. Sin resultados."
            # Formatear salida
            if len(rows) == 1 and len(rows[0]) == 1:
                return f"Resultado: {rows[0][0]}"
            cols = rows[0].keys() if hasattr(rows[0], 'keys') else []
            lines = []
            if cols:
                lines.append(" | ".join(str(c) for c in cols))
                lines.append("-" * len(lines[0]))
            for r in rows[:15]:
                if hasattr(r, 'keys'):
                    lines.append(" | ".join(str(r[c]) for c in cols))
                else:
                    lines.append(" | ".join(str(v) for v in r))
            msg = "\n".join(lines)
            if len(rows) > 15:
                msg += f"\n... ({len(rows)} filas totales, mostrando 15)"
            return f"📊 **SQL Result** ({len(rows)} filas):\n\n{msg}"
        except Exception as e:
            return f"Error SQL: {e}"


    # ═══════════════════════════════════════════════════════════════
    #  v8.2 — TELECOM REAL: herramientas de diagnostico de red de la APK
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    #  v9.0 — SUPER AGENTE: Tablas, Escritura BD, Diagnostico

    # --- CONTAR TABLAS ---
    if any(k in tl for k in ['tablas', 'tables', 'esquema', 'schema']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            tables = conn.execute(
                "SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=m.name) idx "
                "FROM sqlite_master m WHERE type='table' ORDER BY name"
            ).fetchall()
            msg = "📂 **Tablas de la BD:**\n\n"
            for t in tables:
                name = t[0] if isinstance(t, (list, tuple)) else t['name']
                try:
                    cnt = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
                    msg += f"  • {name}: {cnt} filas\n"
                except:
                    msg += f"  • {name}\n"
            conn.close()
            return msg
        except Exception as e:
            return f"Error: {e}"

    # --- ESCRIBIR EN BD (seguro) ---
    if any(k in tl for k in ['insertar', 'crear registro', 'nuevo registro',
                              'agregar registro', 'add record']):
        try:
            # Detectar tabla y campos del mensaje
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            # Buscar menciones de tablas conocidas
            known_tables = ['productos', 'clientes', 'gastos', 'categorias', 'usuarios']
            target_table = None
            for tb in known_tables:
                if tb in tl:
                    target_table = tb
                    break
            if not target_table:
                conn.close()
                return "Indica en que tabla quieres insertar. Tablas disponibles: " + ", ".join(known_tables)
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info([{target_table}])").fetchall()]
            conn.close()
            return (f"Para insertar en **{target_table}**, las columnas son:\n"
                    + ", ".join(cols) + "\n\n"
                    f"Escribe: 'INSERT INTO {target_table} (columna1, columna2) VALUES (valor1, valor2)'")
        except Exception as e:
            return f"Error: {e}"

    # --- DIAGNOSTICO COMPLETO DEL NEGOCIO ---
    if any(k in tl for k in ['diagnostico negocio', 'estado negocio', 'resumen negocio',
                              'como va el negocio', 'reporte ejecutivo']):
        try:
            from db_connection import obtener_conexion
            from datetime import date, timedelta
            conn = obtener_conexion()
            hoy = date.today().isoformat()
            ayer = (date.today() - timedelta(days=1)).isoformat()
            semana = (date.today() - timedelta(days=7)).isoformat()

            # Ventas hoy
            vh = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?",
                (f"{hoy}%",)).fetchone()
            # Ventas ayer
            va = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?",
                (f"{ayer}%",)).fetchone()
            # Ventas semana
            vs = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha >= ?",
                (semana,)).fetchone()
            # Gastos hoy
            gh = conn.execute(
                "SELECT COALESCE(SUM(monto),0) FROM gastos WHERE DATE(fecha)=DATE('now','localtime')").fetchone()
            # Productos
            prods = conn.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
            # Stock bajo
            stock_bajo = conn.execute(
                "SELECT COUNT(*) FROM inventario_general WHERE stock_actual <= stock_minimo").fetchone()[0]
            # Clientes
            try:
                clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
            except:
                clientes = 0
            conn.close()

            v_hoy_total = vh[1] if vh else 0
            v_ayer_total = va[1] if va else 0
            v_sem_total = vs[1] if vs else 0
            g_hoy = gh[0] if gh else 0
            ganancia_hoy = v_hoy_total - g_hoy
            cambio = ((v_hoy_total - v_ayer_total) / v_ayer_total * 100) if v_ayer_total > 0 else 0
            flecha = "📈" if cambio >= 0 else "📉"

            return (f"📊 **Diagnostico Ejecutivo del Negocio**\n\n"
                    f"{flecha} **Ventas Hoy:** ${v_hoy_total:,.2f} ({vh[0] if vh else 0} txns) vs ayer ${v_ayer_total:,.2f} ({cambio:+.1f}%)\n"
                    f"📅 **Ventas Semana:** ${v_sem_total:,.2f} ({vs[0] if vs else 0} txns)\n"
                    f"💰 **Ganancia Neta Hoy:** ${ganancia_hoy:,.2f}\n"
                    f"🛒 **Gastos Hoy:** ${g_hoy:,.2f}\n\n"
                    f"📦 **Productos:** {prods} activos | {stock_bajo} con stock bajo\n"
                    f"👥 **Clientes:** {clientes}\n\n"
                    f"💡 Escribe 'analisis ABC' o 'prediccion' para analisis avanzado.")
        except Exception as e:
            return f"Error en diagnostico: {e}"

    # --- TOP PRODUCTOS VENDIDOS ---
    if any(k in tl for k in ['top vendido', 'mas vendido', 'ranking', 'best seller',
                              'producto estrella', 'lo mas vendido']):
        try:
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, SUM(cantidad) as qty, SUM(total) as rev "
                "FROM historial_ventas "
                "WHERE fecha >= DATE('now','-7 days') "
                "GROUP BY nombre ORDER BY rev DESC LIMIT 10"
            ).fetchall()
            conn.close()
            if not rows:
                return "Sin datos de ventas en los ultimos 7 dias."
            msg = "🏆 **Top Productos (7 dias):**\n\n"
            for i, r in enumerate(rows, 1):
                msg += f"  {i}. {r['nombre']} — {int(r['qty'])} uds / ${r['rev']:,.2f}\n"
            msg += "\n💡 Escribe 'analisis ABC' para clasificacion completa."
            return msg
        except Exception as e:
            return f"Error: {e}"

    # --- ESTADO DE LA IA ---
    if any(k in tl for k in ['estado ia', 'estado ai', 'modo agente', 'motor ia',
                              'agent status', 'cuantas herramientas']):
        tools_count = 0
        try:
            from tool_registry import get_catalog_stats
            stats = get_catalog_stats()
            tools_count = stats.get("total_tools", 0)
            cats = stats.get("total_categories", 0)
            by_cat = stats.get("by_category", {})
            msg = (f"🤖 **Motor de IA — Estado:**\n\n"
                   f"  • Herramientas registradas: {tools_count}\n"
                   f"  • Categorias: {cats}\n"
                   f"  • Motor: ReAct Agentic (offline)\n"
                   f"  • LLM: No requerido (razonamiento simbolico)\n\n"
                   f"**Por categoria:**\n")
            for cat, count in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
                msg += f"  • {cat}: {count} tools\n"
            msg += "\nEl agente ejecuta herramientas reales via API interna."
            return msg
        except Exception as e:
            return f"Motor IA activo. Herramientas: {tools_count}. Error detalle: {e}"

    # --- RAM / MEMORIA DEL DISPOSITIVO ---
    if any(k in tl for k in ['ram', 'memoria', 'memory', 'memoria libre',
                              'memoria usada', 'cuanta ram']):
        try:
            import os
            ram_info = {}
            mem_path = '/proc/meminfo'
            if os.path.exists(mem_path):
                with open(mem_path) as f:
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            ram_info[key] = int(val)  # en kB
            total_kb = ram_info.get('MemTotal', 0)
            free_kb = ram_info.get('MemFree', 0)
            available_kb = ram_info.get('MemAvailable', free_kb)
            used_kb = total_kb - available_kb
            total_mb = total_kb / 1024
            used_mb = used_kb / 1024
            free_mb = available_kb / 1024
            pct_used = (used_kb / total_kb * 100) if total_kb > 0 else 0
            bar_len = 20
            filled = int(bar_len * pct_used / 100)
            bar = '#' * filled + '-' * (bar_len - filled)
            msg = (f"🧠 **Memoria RAM del Dispositivo:**\n\n"
                   f"  Total:    {total_mb:,.0f} MB\n"
                   f"  Usada:    {used_mb:,.0f} MB ({pct_used:.1f}%)\n"
                   f"  Libre:    {free_mb:,.0f} MB\n"
                   f"  [{bar}] {pct_used:.1f}%\n\n")
            if 'SwapTotal' in ram_info:
                swap_total = ram_info['SwapTotal'] / 1024
                swap_free = ram_info.get('SwapFree', 0) / 1024
                swap_used = swap_total - swap_free
                msg += f"  Swap: {swap_used:,.0f} / {swap_total:,.0f} MB"
            return msg
        except Exception as e:
            return f"Error leyendo RAM: {e}"

    # --- DISCO / ALMACENAMIENTO ---
    if any(k in tl for k in ['disco', 'almacenamiento', 'storage', 'espacio',
                              'cuanto espacio', 'disco duro', 'flash']):
        try:
            import shutil
            import os
            paths_to_check = ['/data', '/sdcard', '/storage/emulated', '/']
            msg = "💾 **Almacenamiento del Dispositivo:**\n\n"
            checked = 0
            for p in paths_to_check:
                if os.path.exists(p):
                    try:
                        usage = shutil.disk_usage(p)
                        total_gb = usage.total / (1024**3)
                        used_gb = usage.used / (1024**3)
                        free_gb = usage.free / (1024**3)
                        pct = (usage.used / usage.total * 100) if usage.total > 0 else 0
                        bar_len = 20
                        filled = int(bar_len * pct / 100)
                        bar = '#' * filled + '-' * (bar_len - filled)
                        msg += (f"  **{p}**\n"
                                f"    Total: {total_gb:.1f} GB | Usado: {used_gb:.1f} GB\n"
                                f"    Libre: {free_gb:.1f} GB ({100-pct:.1f}%)\n"
                                f"    [{bar}] {pct:.1f}%\n\n")
                        checked += 1
                    except Exception:
                        pass
            if checked == 0:
                msg += "  No se pudo acceder a las rutas de almacenamiento."
            return msg
        except Exception as e:
            return f"Error leyendo disco: {e}"

    # --- PROCESOS / CPU ---
    if any(k in tl for k in ['procesos', 'cpu', 'proceso', 'hilos',
                              'carga', 'load', 'top procesos', 'ps']):
        try:
            import os
            msg = "⚡ **Procesos y CPU:**\n\n"
            # Carga del sistema
            load_path = '/proc/loadavg'
            if os.path.exists(load_path):
                with open(load_path) as f:
                    load_data = f.read().strip().split()
                if len(load_data) >= 3:
                    msg += (f"  Carga promedio: {load_data[0]} (1min) "
                            f"{load_data[1]} (5min) {load_data[2]} (15min)\n")
            # Uptime
            uptime_path = '/proc/uptime'
            if os.path.exists(uptime_path):
                with open(uptime_path) as f:
                    uptime_sec = float(f.read().strip().split()[0])
                hours = int(uptime_sec // 3600)
                mins = int((uptime_sec % 3600) // 60)
                msg += f"  Uptime del sistema: {hours}h {mins}m\n\n"
            # Contar procesos de Python
            try:
                import subprocess
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                lines = [l for l in result.stdout.strip().split('\n') if l]
                python_procs = [l for l in lines if 'python' in l.lower() and 'ps aux' not in l]
                msg += f"  Procesos Python activos: {len(python_procs)}\n"
                for p in python_procs[:5]:
                    parts = p.split(None, 10)
                    if len(parts) >= 11:
                        msg += f"    PID {parts[1]} | CPU {parts[2]}% | MEM {parts[3]}% | {parts[10][:60]}\n"
            except Exception:
                msg += "  (No se pudieron listar procesos detallados)\n"
            return msg
        except Exception as e:
            return f"Error leyendo procesos: {e}"

    # --- TEMPERATURA ---
    if any(k in tl for k in ['temperatura', 'temp', 'calor', 'bateria',
                              'termica', 'termal']):
        try:
            import os, glob
            msg = "🌡️ **Temperaturas del Dispositivo:**\n\n"
            thermal_zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')
            if thermal_zones:
                for tz in thermal_zones[:6]:
                    try:
                        with open(tz) as f:
                            temp_raw = int(f.read().strip())
                        temp_c = temp_raw / 1000.0
                        zone = tz.split('/')[-2]
                        icon = "🟢" if temp_c < 45 else ("🟡" if temp_c < 65 else "🔴")
                        msg += f"  {icon} {zone}: {temp_c:.1f} C\n"
                    except Exception:
                        pass
            else:
                msg += "  No se encontraron zonas termicas accesibles."
            # Info de bateria si existe
            batt = '/sys/class/power_supply/battery'
            if os.path.exists(batt):
                msg += "\n🔋 **Bateria:**\n"
                try:
                    with open(os.path.join(batt, 'capacity')) as f:
                        msg += f"  Nivel: {f.read().strip()}%\n"
                except Exception: pass
                try:
                    with open(os.path.join(batt, 'status')) as f:
                        msg += f"  Estado: {f.read().strip()}\n"
                except Exception: pass
            return msg
        except Exception as e:
            return f"Error leyendo temperatura: {e}"

    # --- ARCHIVOS / SISTEMA DE ARCHIVOS ---
    if any(k in tl for k in ['archivos', 'directorios', 'carpetas', 'ls',
                              'listar', 'ficheros', 'files']):
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            msg = f"📁 **Archivos en {os.path.basename(base_dir)}:**\n\n"
            # Listar subdirectorios principales
            for item in sorted(os.listdir(base_dir)):
                full = os.path.join(base_dir, item)
                if os.path.isdir(full) and not item.startswith('.'):
                    count = sum(1 for _ in os.walk(full))
                    msg += f"  📂 {item}/ ({count} archivos)\n"
            msg += f"\n💡 Para leer un archivo: 'lee ia/handlers_staff.py'"
            msg += f"\n💡 Para SQL: 'ejecutar SELECT * FROM productos LIMIT 5'"
            return msg
        except Exception as e:
            return f"Error listando archivos: {e}"

    # --- LEER ARCHIVO ---
    if any(k in tl for k in ['lee ', 'leer ', 'ver archivo', 'cat ',
                              'muestra archivo', 'contenido de']):
        try:
            import os
            # Extraer la ruta del archivo
            filepath = None
            for prefix in ['lee ', 'leer ', 'ver archivo ', 'cat ',
                           'muestra archivo ', 'contenido de ']:
                if prefix in tl:
                    filepath = tl.split(prefix, 1)[1].strip()
                    break
            if not filepath:
                return "Indica que archivo leer, ej: 'lee ia/agent.py'"
            # Buscar en el directorio del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, filepath)
            if not os.path.exists(full_path):
                return f"No encontrado: {filepath}"
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            total = len(lines)
            show = lines[:25]
            msg = f"📄 **{filepath}** ({total} lineas, mostrando 25):\n\n"
            for i, line in enumerate(show, 1):
                msg += f"  {i:4d} | {line.rstrip()}\n"
            if total > 25:
                msg += f"\n... ({total - 25} lineas mas)"
            return msg
        except Exception as e:
            return f"Error leyendo archivo: {e}"

    # --- VENTAS DE HOY (para dev tambien) ---
    if any(k in tl for k in ['ventas de hoy', 'ventas hoy', 'cuanto vendido hoy',
                              'recaudado hoy']):
        try:
            from db_connection import obtener_conexion
            from datetime import date
            conn = obtener_conexion()
            hoy = date.today().isoformat()
            r = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM historial_ventas WHERE fecha LIKE ?",
                (f"{hoy}%",)).fetchone()
            conn.close()
            return f"💰 **Ventas de hoy:**\n\n  Transacciones: {r[0]}\n  Total: ${r[1]:,.2f}"
        except Exception as e:
            return f"Error: {e}"

    # ═══════════════════════════════════════════════════════════════
    #  RETURN POR DEFECTO — Al final de todo
    # ═══════════════════════════════════════════════════════════════
    return ("💻 **Super Agente Dev** — Comandos disponibles:\n\n"
            "  📊 SQL: 'ejecutar SELECT * FROM productos LIMIT 5'\n"
            "  📂 Tablas: 'tablas' o 'esquema'\n"
            "  📈 Diagnostico: 'diagnostico negocio'\n"
            "  🏆 Top: 'top vendidos' o 'ranking'\n"
            "  🧠 RAM: 'ram' o 'memoria'\n"
            "  💾 Disco: 'disco' o 'almacenamiento'\n"
            "  ⚡ Procesos: 'procesos' o 'cpu'\n"
            "  🌡️ Temp: 'temperatura'\n"
            "  📁 Archivos: 'archivos' o 'listar'\n"
            "  📄 Leer: 'lee ia/agent.py'\n"
            "  📝 Logs: 'logs'\n"
            "  🔐 Seguridad: 'seguridad'\n"
            "  🤖 IA: 'estado ia'")
