from auth_decorator import login_required
from routes.loyalty_bp import loyalty_bp
from routes.loyalty_helpers import *

@login_required
@loyalty_bp.route('/status', methods=['GET'])
def status():
    _ensure_loyalty_table()
    c = _db()
    if not c:
        return jsonify({"active": False, "clients": 0, "tiers": {}})
    try:
        total = c.execute("SELECT COUNT(*) FROM loyalty_clients").fetchone()[0]
        tier_counts = {}
        for tier in TIERS:
            cnt = c.execute("SELECT COUNT(*) FROM loyalty_clients WHERE tier=?", (tier,)).fetchone()[0]
            tier_counts[tier] = cnt
        pending = c.execute("SELECT COUNT(*) FROM headless_orders WHERE status='pending'").fetchone()[0]
        return jsonify({
            "active": True,
            "clients": total,
            "tier_distribution": tier_counts,
            "pending_orders": pending,
            "tiers": {k: {"label": v["label"], "discount": v["discount"], "min": v["min"]} for k, v in TIERS.items()}
        })
    finally:
        c.close()

@login_required
@loyalty_bp.route('/enroll', methods=['POST'])
def enroll():
    _ensure_loyalty_table()
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    if not phone or not name:
        return jsonify({"error": "Telefono y nombre son requeridos"}), 400
    c = _db()
    if not c:
        return jsonify({"error": "Base de datos no disponible"}), 500
    try:
        existing = c.execute("SELECT id, points, tier FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
        if existing:
            return jsonify({"ok": True, "client_id": existing[0], "points": existing[1], "tier": existing[2], "message": "Cliente ya inscrito"})
        cur = c.execute("INSERT INTO loyalty_clients (phone, name, email) VALUES (?,?,?)", (phone, name, email or ""))
        cid = cur.lastrowid
        c.commit()
        # Bonificacion de bienvenida
        c.execute("INSERT INTO loyalty_transactions (client_id, type, points, description) VALUES (?, 'bonus', 50, 'Bienvenida al programa')", (cid,))
        c.execute("UPDATE loyalty_clients SET points=50, updated_at=datetime('now','localtime') WHERE id=?", (cid,))
        c.commit()
        return jsonify({"ok": True, "client_id": cid, "points": 50, "tier": "bronze", "message": "Inscrito! 50 puntos de bienvenida"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        c.close()

@login_required
@loyalty_bp.route('/points', methods=['GET'])
def get_points():
    _ensure_loyalty_table()
    phone = request.args.get('phone', '').strip()
    client_id = request.args.get('client_id')
    if not phone and not client_id:
        return jsonify({"error": "Especifica phone o client_id"}), 400
    c = _db()
    if not c:
        return jsonify({"error": "DB no disponible"}), 500
    try:
        if phone:
            row = c.execute("SELECT id, name, points, tier, total_spent, visits FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
        else:
            row = c.execute("SELECT id, name, points, tier, total_spent, visits FROM loyalty_clients WHERE id=?", (client_id,)).fetchone()
        if not row:
            return jsonify({"error": "Cliente no encontrado"}), 404
        tier_info = TIERS.get(row[3], TIERS["bronze"])
        next_tier = None
        for name, t in sorted(TIERS.items(), key=lambda x: x[1]["min"]):
            if t["min"] > row[2]:
                next_tier = {"name": name, "label": t["label"], "min": t["min"], "needed": t["min"] - row[2]}
                break
        return jsonify({
            "client_id": row[0], "name": row[1], "points": row[2],
            "tier": row[3], "tier_label": tier_info["label"], "tier_discount": tier_info["discount"],
            "total_spent": row[4], "visits": row[5], "next_tier": next_tier
        })
    finally:
        c.close()

@login_required
@loyalty_bp.route('/points/add', methods=['POST'])
def add_points():
    _ensure_loyalty_table()
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    amount = data.get('amount', 0)
    if not phone or amount <= 0:
        return jsonify({"error": "Telefono y monto requeridos"}), 400
    c = _db()
    if not c:
        return jsonify({"error": "DB no disponible"}), 500
    try:
        row = c.execute("SELECT id, points FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
        if not row:
            return jsonify({"error": "Cliente no encontrado"}), 404
        # 1 punto por cada $1 + 10 puntos bono por venta
        pts = int(amount) + 10
        new_pts = row[1] + pts
        new_tier = _get_tier(new_pts)
        c.execute("UPDATE loyalty_clients SET points=?, tier=?, total_spent=total_spent+?, visits=visits+1, updated_at=datetime('now','localtime') WHERE id=?", (new_pts, new_tier, amount, row[0]))
        c.execute("INSERT INTO loyalty_transactions (client_id, type, points, amount, description) VALUES (?, 'earn', ?, ?, 'Puntos por compra')", (row[0], pts, amount))
        c.commit()
        return jsonify({"ok": True, "points_added": pts, "total_points": new_pts, "new_tier": new_tier})
    finally:
        c.close()

@login_required
@loyalty_bp.route('/points/redeem', methods=['POST'])
def redeem():
    _ensure_loyalty_table()
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    points = data.get('points', 0)
    if not phone or points <= 0:
        return jsonify({"error": "Telefono y puntos requeridos"}), 400
    if points < 500:
        return jsonify({"error": "Minimo 500 puntos para canjear"}), 400
    c = _db()
    if not c:
        return jsonify({"error": "DB no disponible"}), 500
    try:
        row = c.execute("SELECT id, name, points, tier FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
        if not row:
            return jsonify({"error": "Cliente no encontrado"}), 404
        if row[2] < points:
            return jsonify({"error": "Puntos insuficientes (tienes %d)" % row[2]}), 400
        # Valor de canje: $1 por cada 100 puntos
        value = points / 100.0
        new_pts = row[2] - points
        new_tier = _get_tier(new_pts)
        c.execute("UPDATE loyalty_clients SET points=?, tier=?, updated_at=datetime('now','localtime') WHERE id=?", (new_pts, new_tier, row[0]))
        c.execute("INSERT INTO loyalty_transactions (client_id, type, points, amount, description) VALUES (?, 'redeem', ?, ?, 'Canje de puntos')", (row[0], -points, value))
        c.commit()
        return jsonify({"ok": True, "points_redeemed": points, "remaining_points": new_pts, "value": value, "new_tier": new_tier})
    finally:
        c.close()

@login_required
@loyalty_bp.route('/history', methods=['GET'])
def get_history():
    _ensure_loyalty_table()
    phone = request.args.get('phone', '').strip()
    client_id = request.args.get('client_id')
    limit = request.args.get('limit', 20)
    if not phone and not client_id:
        return jsonify({"error": "Especifica phone o client_id"}), 400
    c = _db()
    if not c:
        return jsonify({"transactions": []})
    try:
        if phone:
            cid_row = c.execute("SELECT id FROM loyalty_clients WHERE phone=?", (phone,)).fetchone()
            if not cid_row:
                return jsonify({"transactions": []})
            cid = cid_row[0]
        else:
            cid = client_id
        rows = c.execute("SELECT type, points, amount, description, created_at FROM loyalty_transactions WHERE client_id=? ORDER BY id DESC LIMIT ?", (cid, int(limit))).fetchall()
        return jsonify({"transactions": [{"type": r[0], "points": r[1], "amount": r[2], "description": r[3], "date": r[4]} for r in rows]})
    finally:
        c.close()

