from auth_decorator import login_required
from routes.loyalty_bp import loyalty_bp
from routes.loyalty_helpers import *

@login_required
@loyalty_bp.route('/headless/order', methods=['POST'])
def headless_order():
    _ensure_loyalty_table()
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    items = data.get('items', [])
    channel = data.get('channel', 'online')
    if not items:
        return jsonify({"error": "Items requeridos"}), 400
    c = _db()
    if not c:
        return jsonify({"error": "DB no disponible"}), 500
    try:
        # Calcular total y descontar inventario
        total = 0
        items_json = []
        for item in items:
            nombre = item.get('nombre', '')
            qty = item.get('cantidad', 1)
            precio = item.get('precio', 0)
            subtotal = qty * precio
            total += subtotal
            items_json.append({"nombre": nombre, "cantidad": qty, "precio": precio, "subtotal": subtotal})
            # Descontar inventario
            c.execute("UPDATE productos SET stock_actual = stock_actual - ? WHERE LOWER(nombre) = LOWER(?) AND stock_actual >= ?", (qty, nombre, qty))
        # Crear orden
        cid = None
        if phone:
            cid_row = c.execute("SELECT id FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
            if cid_row:
                cid = cid_row[0]
        cur = c.execute("INSERT INTO headless_orders (client_id, channel, items, total, status) VALUES (?,?,?,?,?)",
            (cid, channel, json.dumps(items_json, ensure_ascii=False), total, 'pending'))
        order_id = cur.lastrowid
        c.commit()
        # Acumular puntos si hay cliente
        if cid and total > 0:
            pts = int(total) + 10
            c.execute("UPDATE loyalty_clients SET points=points+?, total_spent=total_spent+?, visits=visits+1, updated_at=datetime('now','localtime') WHERE id=?", (pts, total, cid))
            c.execute("INSERT INTO loyalty_transactions (client_id, type, points, amount, description) VALUES (?, 'earn', ?, ?, ?)", (cid, pts, total, 'Orden omnicanal #%d' % order_id))
            c.commit()
        return jsonify({"ok": True, "order_id": order_id, "total": total, "status": "pending", "channel": channel})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        c.close()

@login_required
@loyalty_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    _ensure_loyalty_table()
    c = _db()
    if not c:
        return jsonify({"leaders": []})
    try:
        rows = c.execute("SELECT name, points, tier, visits, total_spent FROM loyalty_clients ORDER BY points DESC LIMIT 10").fetchall()
        return jsonify({"leaders": [{"name": r[0], "points": r[1], "tier": r[2], "visits": r[3], "spent": r[4]} for r in rows]})
    finally:
        c.close()
