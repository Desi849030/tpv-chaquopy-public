from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from database import obtener_conexion, agregar_log

agent_bp = Blueprint('agent', __name__, url_prefix='/api')

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"): return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return wrapper

def usuario_actual(): return session.get("usuario", {})

@agent_bp.route('/agent/query', methods=['POST'])
@requiere_login
def agent_query():
    datos = request.get_json(force=True, silent=True) or {}
    query = datos.get('query', '').lower()
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    respuesta = "No entiendo tu pregunta. Prueba con: 'ventas', 'inventario', 'ayuda' o 'cerrar'."
    tipo = "text"
    data_extra = {}
    try:
        if any(k in query for k in ['venta', 'dinero', 'caja']):
            conn = obtener_conexion()
            hoy = datetime.now().strftime('%Y-%m-%d')
            vid = u['usuario_id'] if rol == 'vendedor' else None
            filtro = "WHERE vendedor_id = ?" if vid else ""
            params = (vid,) if vid else ()
            cursor = conn.execute(f"SELECT COUNT(*) as num, SUM(total) as total FROM historial_ventas {filtro} AND fecha LIKE ?", params + (f"{hoy}%",))
            res = cursor.fetchone()
            conn.close()
            respuesta = f"📊 Ventas hoy: ${res['total'] or 0:.2f} ({res['num'] or 0} transacciones)"
        elif any(k in query for k in ['stock', 'inventario', 'producto']):
            conn = obtener_conexion()
            cursor = conn.execute("SELECT COUNT(*) as total FROM productos WHERE activo=1")
            res = cursor.fetchone()
            conn.close()
            respuesta = f"📦 Inventario: {res['total'] or 0} productos activos"
        elif 'qr' in query:
            respuesta = "🔲 Ve a Gestión → Etiquetas QR para generar códigos"
            tipo = "action"; data_extra = {"target": "cliente-qr-tab"}
        elif 'exportar' in query or 'backup' in query:
            respuesta = "📤 Ve a Herramientas → Exportar para descargar datos"
        elif 'cerrar' in query or 'turno' in query:
            respuesta = "🔒 Ve a Inventario → Cerrar Día para registrar el cierre"
        elif 'ayuda' in query:
            respuesta = "🤖 Puedo ayudarte con: ventas, inventario, QR, exportar, cerrar día. ¿Qué necesitas?"
        agregar_log(f"IA: {u.get('username')} preguntó: {query[:50]}...", 'info')
        return jsonify({'ok': True, 'respuesta': respuesta, 'tipo': tipo, 'data': data_extra})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@agent_bp.route('/agent/suggestions', methods=['GET'])
@requiere_login
def agent_suggestions():
    u = usuario_actual()
    rol = u.get('rol', 'vendedor')
    comunes = ["¿Cuánto vendí hoy?", "¿Qué productos tengo en stock bajo?", "¿Cómo genero QR?"]
    por_rol = {
        'desarrollador': ["¿Cómo activo una licencia?", "¿Cómo sincronizo con Supabase?"],
        'administrador': ["¿Cómo creo un nuevo usuario?", "¿Cómo asigno inventario?"],
        'vendedor': ["¿Cuánto me falta para cerrar?", "¿Cómo registro una venta?"]
    }
    return jsonify({'ok': True, 'sugerencias': comunes + por_rol.get(rol, [])})
