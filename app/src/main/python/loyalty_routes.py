"""loyalty_routes.py v8.0.0 — Lealtad Omnicanal + Headless Commerce (funcional)"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3, json, random

loyalty_bp = Blueprint('loyalty', __name__, url_prefix='/api/loyalty')

TIERS = {
    "bronze": {"min": 0, "discount": 0, "label": "Bronze", "color": "#9E9E9E"},
    "silver": {"min": 1000, "discount": 5, "label": "Silver", "color": "#607D8B"},
    "gold": {"min": 5000, "discount": 10, "label": "Gold", "color": "#FFD700"},
    "platinum": {"min": 15000, "discount": 15, "label": "Platinum", "color": "#E5E4E2"}
}

def _db():
    try:
        from database import obtener_conexion
        return obtener_conexion()
    except:
        return None

def _get_tier(points):
    tier = "bronze"
    for name, t in sorted(TIERS.items(), key=lambda x: x[1]["min"], reverse=True):
        if points >= t["min"]:
            tier = name
            break
    return tier

def _ensure_loyalty_table():
    c = _db()
    if not c:
        return False
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS loyalty_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            email TEXT,
            points INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'bronze',
            total_spent REAL DEFAULT 0,
            visits INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            type TEXT,
            points INTEGER,
            amount REAL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS headless_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            channel TEXT DEFAULT 'online',
            items TEXT,
            total REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            processed_at TEXT
        )""")
        c.commit()
        return True
    except:
        return False
    finally:
        c.close()

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
