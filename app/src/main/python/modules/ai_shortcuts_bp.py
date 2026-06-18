# -*- coding: utf-8 -*-
"""Atajos IA: respuestas instantaneas con datos reales de la BD."""
from flask import Blueprint, jsonify, request
from decorators import login_required, requiere_rol
from db_connection import obtener_conexion

ai_shortcuts_bp = Blueprint('ai_shortcuts_bp', __name__)


def _q(sql, params=()):
    """Ejecuta query y cierra conexion."""
    conn = obtener_conexion()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@ai_shortcuts_bp.route('/api/ai/shortcut/top-ventas-hoy', methods=['GET'])
@login_required
@requiere_rol(['vendedor', 'cajero', 'supervisor', 'administrador', 'desarrollador'])
def top_ventas_hoy():
    rows = _q("SELECT nombre, SUM(cantidad) AS unidades, SUM(total) AS ingresos FROM historial_ventas WHERE date(fecha) = date('now', 'localtime') GROUP BY nombre ORDER BY unidades DESC LIMIT 5")
    if not rows:
        return jsonify(shortcut='top-ventas-hoy', title='Top ventas', text='Aun no hay ventas hoy.', items=[])
    txt = 'Top ventas de hoy:\n'
    for i, r in enumerate(rows, 1):
        txt += f"{i}. {r['nombre']} - {int(r['unidades'])} und - ${float(r['ingresos']):.2f}\n"
    return jsonify(shortcut='top-ventas-hoy', title='Top ventas hoy', text=txt.strip(), items=rows)


@ai_shortcuts_bp.route('/api/ai/shortcut/alerta-stock', methods=['GET'])
@login_required
@requiere_rol(['supervisor', 'administrador', 'desarrollador'])
def alerta_stock():
    rows = _q("SELECT p.nombre, p.producto_id, COALESCE(i.stock_actual, 0) AS stock, COALESCE(p.stock_minimo, 5) AS minimo FROM productos p LEFT JOIN inventario_general i ON i.producto_id = p.producto_id WHERE COALESCE(i.stock_actual, 0) <= COALESCE(p.stock_minimo, 5) AND p.activo = 1 ORDER BY stock ASC LIMIT 20")
    if not rows:
        return jsonify(shortcut='alerta-stock', title='Stock', text='Stock saludable.', items=[])
    crit = sum(1 for x in rows if x['stock'] <= x['minimo'] / 2)
    txt = f"{len(rows)} productos con stock bajo ({crit} criticos):\n"
    for it in rows[:10]:
        e = 'CRIT' if it['stock'] <= it['minimo'] / 2 else 'BAJO'
        txt += f"[{e}] {it['nombre']} - {it['stock']} und\n"
    return jsonify(shortcut='alerta-stock', title='Alerta stock', text=txt.strip(), items=rows, criticos_count=crit)


@ai_shortcuts_bp.route('/api/ai/shortcut/resumen-dia', methods=['GET'])
@login_required
def resumen_dia():
    s_rows = _q("SELECT COUNT(*) AS n, COALESCE(SUM(total), 0) AS ing, COALESCE(AVG(total), 0) AS ticket FROM historial_ventas WHERE date(fecha) = date('now', 'localtime')")
    m_rows = _q("SELECT metodo_pago, COUNT(*) AS n FROM historial_ventas WHERE date(fecha) = date('now', 'localtime') AND metodo_pago IS NOT NULL GROUP BY metodo_pago ORDER BY n DESC LIMIT 1")
    s = s_rows[0] if s_rows else {'n': 0, 'ing': 0, 'ticket': 0}
    metodo = m_rows[0]['metodo_pago'] if m_rows else None
    txt = (f"Resumen de hoy:\n- Ventas: {s['n']}\n- Ingresos: ${float(s['ing']):.2f}\n- Ticket prom: ${float(s['ticket']):.2f}\n")
    if metodo:
        txt += f"- Metodo top: {metodo}"
    return jsonify(shortcut='resumen-dia', title='Resumen del dia', text=txt.strip(), num_ventas=s['n'], ingresos=round(float(s['ing']), 2), ticket_promedio=round(float(s['ticket']), 2), metodo_top=metodo)


_RULES = [
    (['top ventas hoy', 'mas vendido hoy', 'que vendi hoy', 'ranking hoy', 'productos mas vendidos'], 'top'),
    (['stock bajo', 'stock critico', 'alerta de stock', 'inventario bajo', 'por agotarse'], 'stock'),
    (['resumen del dia', 'resumen de hoy', 'como voy hoy', 'estadisticas hoy', 'cuanto llevo hoy'], 'resumen'),
]

@ai_shortcuts_bp.route('/api/ai/shortcut/detect', methods=['POST'])
@login_required
def detect():
    q = (request.json or {}).get('query', '').lower().strip()
    fns = {'top': top_ventas_hoy, 'stock': alerta_stock, 'resumen': resumen_dia}
    for kws, key in _RULES:
        if any(k in q for k in kws):
            r = fns[key]()
            d = r.get_json()
            d['matched'] = True
            d['kw'] = next(k for k in kws if k in q)
            return jsonify(d)
    return jsonify(matched=False, msg='No es atajo')
