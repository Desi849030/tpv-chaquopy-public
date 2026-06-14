# -*- coding: utf-8 -*-
"""modules/agent.py — Blueprint de agente IA (query + suggestions)
Decoradores unificados desde decorators.py (ya no redefine los propios)."""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from decorators import login_required, usuario_actual

try:
    from db_connection import agregar_log, obtener_conexion
    _HAS_DB = True
except Exception:
    _HAS_DB = False

agent_bp = Blueprint('agent', __name__, url_prefix='/api')


@agent_bp.route('/agent/query', methods=['POST'])
@login_required
def agent_query():
    datos = request.get_json(force=True, silent=True) or {}
    query = datos.get('query', '').lower().strip()
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    respuesta = "No entiendo tu pregunta. Prueba con: 'ventas', 'inventario', 'ayuda' o 'cerrar'."
    tipo = "text"
    data_extra = {}

    if not _HAS_DB:
        return jsonify({'ok': True, 'respuesta': respuesta, 'tipo': tipo, 'data': data_extra})

    try:
        if any(k in query for k in ['venta', 'dinero', 'caja']):
            conn = obtener_conexion()
            hoy = datetime.now().strftime('%Y-%m-%d')
            uid = u.get('usuario_id')
            if rol == 'vendedor' and uid:
                cursor = conn.execute(
                    "SELECT COUNT(*) as num, COALESCE(SUM(total),0) as total "
                    "FROM historial_ventas WHERE vendedor_id = ? AND fecha LIKE ?",
                    (uid, f"{hoy}%"))
            else:
                cursor = conn.execute(
                    "SELECT COUNT(*) as num, COALESCE(SUM(total),0) as total "
                    "FROM historial_ventas WHERE fecha LIKE ?",
                    (f"{hoy}%",))
            res = cursor.fetchone()
            conn.close()
            total = res['total'] if res else 0
            num = res['num'] if res else 0
            respuesta = f"📊 Ventas hoy: ${total:.2f} ({num} transacciones)"

        elif any(k in query for k in ['stock', 'inventario', 'producto']):
            conn = obtener_conexion()
            cursor = conn.execute("SELECT COUNT(*) as total FROM productos WHERE activo=1")
            res = cursor.fetchone()
            # Stock bajo
            cursor2 = conn.execute(
                "SELECT COUNT(*) as bajo FROM inventario_general WHERE stock_actual <= 5")
            bajo = cursor2.fetchone()
            conn.close()
            total = res['total'] if res else 0
            n_bajo = bajo['bajo'] if bajo else 0
            respuesta = f"📦 Inventario: {total} productos activos"
            if n_bajo > 0:
                respuesta += f" | ⚠️ {n_bajo} con stock bajo"

        elif 'qr' in query:
            respuesta = "🔲 Ve a Gestión → Etiquetas QR para generar códigos"
            tipo = "action"
            data_extra = {"target": "cliente-qr-tab"}

        elif 'exportar' in query or 'backup' in query:
            respuesta = "📤 Ve a Herramientas → Exportar para descargar datos"

        elif 'cerrar' in query or 'turno' in query:
            respuesta = "🔒 Ve a Inventario → Cerrar Día para registrar el cierre"

        elif 'ayuda' in query:
            respuesta = ("🤖 Puedo ayudarte con: ventas, inventario, QR, exportar, "
                         "cerrar día. ¿Qué necesitas?")

        try:
            agregar_log(f"IA: {u.get('username')} preguntó: {query[:50]}...", 'info')
        except Exception:  # noqa: broad-except - graceful degradation
            pass
        return jsonify({'ok': True, 'respuesta': respuesta, 'tipo': tipo, 'data': data_extra})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@agent_bp.route('/agent/suggestions', methods=['GET'])
@login_required
def agent_suggestions():
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    comunes = [
        "¿Cuánto vendí hoy?",
        "¿Qué productos tengo en stock bajo?",
        "¿Cómo genero QR?",
    ]
    por_rol = {
        'desarrollador': ["¿Cómo activo una licencia?", "¿Cómo sincronizo con Supabase?",
                          "Estado del sistema"],
        'administrador': ["¿Cómo creo un nuevo usuario?", "¿Cómo asigno inventario?",
                          "Reporte financiero"],
        'supervisor': ["Rendimiento de vendedores", "Dashboard de KPIs"],
        'vendedor': ["¿Cuánto me falta para cerrar?", "¿Cómo registro una venta?"],
        'cajero': ["¿Cómo cobro?", "Cierre de caja"],
    }
    return jsonify({'ok': True, 'sugerencias': comunes + por_rol.get(rol, [])})
