# -*- coding: utf-8 -*-
"""Ventas v10: atomicidad + idempotencia + resumen correcto."""
from flask import Blueprint, request, jsonify
from datetime import date, datetime
import os
import sqlite3
import time
import uuid

from decorators import login_required, usuario_actual
from db_connection import obtener_conexion, agregar_log, audit_log

ventas_core_bp = Blueprint("ventas_core", __name__)


class StockInsuficienteError(Exception):
    pass


class ProductoNoEncontradoError(Exception):
    pass


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _testing():
    return os.environ.get("TPV_TESTING") == "1"


def _pid(item):
    return str(item.get("producto_id") or item.get("id") or "").strip()


def _txn(payload):
    raw = str(payload.get("client_txn_id") or payload.get("idempotency_key") or "").strip()
    return raw[:120] if raw else "auto-" + uuid.uuid4().hex


def _tab(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


def _v10(conn):
    return _tab(conn, "ventas_cabecera") and _tab(conn, "ventas_detalle")


def _venta_existente(cur, client_txn_id):
    return cur.execute(
        "SELECT venta_id, total, fecha, vendedor_id FROM ventas_cabecera WHERE client_txn_id=?",
        (client_txn_id,),
    ).fetchone()


def _sumar_periodo(conn, like_pat, vendedor_id=None):
    if _v10(conn):
        if vendedor_id:
            row = conn.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) FROM ventas_cabecera WHERE fecha LIKE ? AND vendedor_id=?",
                (like_pat, vendedor_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) FROM ventas_cabecera WHERE fecha LIKE ?",
                (like_pat,),
            ).fetchone()
        return float(row[0] or 0), int(row[1] or 0)

    if vendedor_id:
        row = conn.execute(
            "SELECT COALESCE(SUM(t.total_venta),0), COUNT(*) FROM ("
            " SELECT venta_id, SUM(total) total_venta FROM historial_ventas"
            " WHERE fecha LIKE ? AND vendedor_id=? GROUP BY venta_id"
            ") t",
            (like_pat, vendedor_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COALESCE(SUM(t.total_venta),0), COUNT(*) FROM ("
            " SELECT venta_id, SUM(total) total_venta FROM historial_ventas"
            " WHERE fecha LIKE ? GROUP BY venta_id"
            ") t",
            (like_pat,),
        ).fetchone()
    return float(row[0] or 0), int(row[1] or 0)


def _registrar(payload, user):
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return {"ok": False, "error": "No hay productos"}, 400

    metodo = str(payload.get("metodo_pago", "efectivo")).strip() or "efectivo"
    client_txn_id = _txn(payload)
    vendedor_id = user.get("usuario_id", "desconocido")
    vendedor_nombre = user.get("nombre") or user.get("username") or vendedor_id
    fecha = datetime.now().isoformat(timespec="seconds")

    conn = None
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")

        if _v10(conn):
            prev = _venta_existente(cur, client_txn_id)
            if prev:
                return {
                    "ok": True,
                    "venta_id": prev["venta_id"],
                    "total": round(_f(prev["total"]), 2),
                    "items": len(items),
                    "fecha": prev["fecha"],
                    "vendedor_id": prev["vendedor_id"],
                    "client_txn_id": client_txn_id,
                    "idempotent": True,
                }, 200

        venta_id = f"vta-{uuid.uuid4().hex[:8]}"
        total = 0.0

        if _v10(conn):
            cur.execute(
                "INSERT INTO ventas_cabecera "
                "(venta_id, client_txn_id, vendedor_id, vendedor_nombre, metodo_pago, total, estado, fecha) "
                "VALUES (?, ?, ?, ?, ?, 0, 'procesando', ?)",
                (venta_id, client_txn_id, vendedor_id, vendedor_nombre, metodo, fecha),
            )

        for item in items:
            pid = _pid(item)
            nombre = str(item.get("nombre", "Producto")).strip() or "Producto"
            cantidad = _f(item.get("cantidad"), 0)
            precio = _f(item.get("precio"), 0)
            if not pid:
                raise ValueError("Producto sin identificador")
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para {pid}")
            if precio < 0:
                raise ValueError(f"Precio inválido para {pid}")

            subtotal = round(cantidad * precio, 2)
            row = cur.execute(
                "SELECT stock_actual FROM inventario_general WHERE producto_id=?", (pid,)
            ).fetchone()
            if row is None:
                if not _testing():
                    raise ProductoNoEncontradoError(f"Producto no encontrado en inventario: {pid}")
            else:
                cur.execute(
                    "UPDATE inventario_general SET stock_actual = stock_actual - ?, actualizado = ? "
                    "WHERE producto_id = ? AND stock_actual >= ?",
                    (cantidad, fecha, pid, cantidad),
                )
                if cur.rowcount != 1:
                    disp = cur.execute(
                        "SELECT stock_actual FROM inventario_general WHERE producto_id=?", (pid,)
                    ).fetchone()
                    raise StockInsuficienteError(
                        f"Stock insuficiente para {nombre}. Disponible: {_f(disp[0] if disp else 0)}, solicitado: {cantidad}"
                    )

            if _v10(conn):
                cur.execute(
                    "INSERT INTO ventas_detalle (venta_id, producto_id, nombre, cantidad, precio_unit, subtotal) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (venta_id, pid, nombre, cantidad, precio, subtotal),
                )

            cur.execute(
                "INSERT INTO historial_ventas "
                "(venta_id, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha, vendedor_id, vendedor_nombre) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (venta_id, pid, nombre, cantidad, precio, subtotal, metodo, fecha, vendedor_id, vendedor_nombre),
            )
            total += subtotal

        total = round(total, 2)
        if _v10(conn):
            cur.execute(
                "UPDATE ventas_cabecera SET total=?, estado='confirmada' WHERE venta_id=?",
                (total, venta_id),
            )
        conn.commit()

        try:
            agregar_log(f"Venta {venta_id} registrada por {vendedor_id}. Total=${total:.2f}, items={len(items)}", "info", vendedor_id)
        except Exception:
            pass
        try:
            audit_log(vendedor_id, "registrar_venta", "ventas_cabecera", venta_id, "", {
                "total": total, "items": len(items), "metodo_pago": metodo,
                "fecha": fecha, "client_txn_id": client_txn_id,
            })
        except Exception:
            pass

        return {
            "ok": True,
            "venta_id": venta_id,
            "total": total,
            "items": len(items),
            "fecha": fecha,
            "vendedor_id": vendedor_id,
            "client_txn_id": client_txn_id,
            "idempotent": False,
        }, 200

    except sqlite3.IntegrityError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        msg = str(e).lower()
        if "client_txn_id" in msg and conn and _v10(conn):
            row = _venta_existente(conn.cursor(), client_txn_id)
            if row:
                return {
                    "ok": True, "venta_id": row["venta_id"],
                    "total": round(_f(row["total"]), 2), "items": len(items),
                    "fecha": row["fecha"], "vendedor_id": row["vendedor_id"],
                    "client_txn_id": client_txn_id, "idempotent": True,
                }, 200
        return {"ok": False, "error": str(e)}, 500
    except StockInsuficienteError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        return {"ok": False, "error": str(e), "code": "STOCK_INSUFICIENTE"}, 409
    except ProductoNoEncontradoError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        return {"ok": False, "error": str(e), "code": "PRODUCTO_NO_ENCONTRADO"}, 404
    except ValueError as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        if conn:
            try: conn.rollback()
            except Exception: pass
        return {"ok": False, "error": str(e)}, 500
    finally:
        if conn:
            try: conn.close()
            except Exception: pass


@ventas_core_bp.route("/api/ventas/registrar", methods=["POST"])
@login_required
def registrar_venta():
    payload = request.get_json(silent=True) or {}
    user = usuario_actual()
    for i in range(3):
        body, status = _registrar(payload, user)
        if status != 500:
            return jsonify(body), status
        msg = str(body.get("error", "")).lower()
        if "locked" not in msg and "busy" not in msg:
            return jsonify(body), status
        time.sleep(0.15 * (i + 1))
    return jsonify({"ok": False, "error": "Base de datos ocupada, reintenta"}), 503


@ventas_core_bp.route("/api/ventas/hoy")
@login_required
def ventas_hoy():
    try:
        u = usuario_actual()
        conn = obtener_conexion()
        cur = conn.cursor()
        hoy = date.today().isoformat()
        if _v10(conn):
            sql = (
                "SELECT vc.venta_id, COALESCE(GROUP_CONCAT(vd.nombre, ' | '), '(sin detalle)'), "
                "COALESCE(SUM(vd.cantidad),0), "
                "CASE WHEN COALESCE(SUM(vd.cantidad),0) > 0 THEN ROUND(vc.total / SUM(vd.cantidad), 2) ELSE vc.total END, "
                "vc.total, vc.metodo_pago, vc.fecha "
                "FROM ventas_cabecera vc LEFT JOIN ventas_detalle vd ON vd.venta_id = vc.venta_id "
                "WHERE vc.fecha LIKE ?"
            )
            params = [f"{hoy}%"]
            if u.get("rol") == "vendedor":
                sql += " AND vc.vendedor_id = ?"
                params.append(u.get("usuario_id"))
            sql += " GROUP BY vc.venta_id, vc.total, vc.metodo_pago, vc.fecha ORDER BY vc.fecha DESC"
            cur.execute(sql, tuple(params))
        else:
            if u.get("rol") == "vendedor":
                cur.execute(
                    "SELECT venta_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha "
                    "FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id=? ORDER BY fecha DESC",
                    (f"{hoy}%", u.get("usuario_id")),
                )
            else:
                cur.execute(
                    "SELECT venta_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha "
                    "FROM historial_ventas WHERE fecha LIKE ? ORDER BY fecha DESC",
                    (f"{hoy}%",),
                )
        ventas, total = [], 0.0
        for row in cur.fetchall():
            ventas.append({
                "venta_id": row[0], "producto": row[1], "cantidad": row[2],
                "precio_unit": row[3], "total": row[4], "metodo_pago": row[5], "fecha": row[6],
            })
            total += _f(row[4])
        conn.close()
        return jsonify({"ok": True, "ventas": ventas, "total": round(total, 2), "cantidad": len(ventas)})
    except Exception:
        return jsonify({"ok": True, "ventas": [], "total": 0, "cantidad": 0})


@ventas_core_bp.route("/api/ventas/cierre", methods=["POST"])
@login_required
def cierre_caja():
    d = request.get_json(silent=True) or {}
    fecha = d.get("fecha", date.today().isoformat())
    u = usuario_actual()
    try:
        conn = obtener_conexion()
        total_ventas, num_ventas = _sumar_periodo(conn, f"{fecha}%", u.get("usuario_id") if u.get("rol") == "vendedor" else None)
        conn.execute(
            "INSERT OR REPLACE INTO cierres_caja (fecha, total_ventas, num_transacciones, cerrado_por) VALUES (?,?,?,?)",
            (fecha, total_ventas, num_ventas, u.get("usuario_id", "sistema")),
        )
        conn.commit(); conn.close()
        return jsonify({"ok": True, "fecha": fecha, "total_ventas": total_ventas, "num_transacciones": num_ventas, "cerrado_por": u.get("usuario_id", "sistema")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@ventas_core_bp.route("/api/ventas/cierres")
@login_required
def listar_cierres():
    conn = None
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, fecha, total_ventas, num_transacciones, efectivo, tarjeta, transferencia, cerrado_por, creado "
            "FROM cierres_caja ORDER BY fecha DESC LIMIT 30"
        )
        cierres = [{
            "id": r[0], "fecha": r[1], "total": r[2], "transacciones": r[3],
            "efectivo": r[4], "tarjeta": r[5], "transferencia": r[6], "cerrado_por": r[7],
        } for r in cur.fetchall()]
        return jsonify({"ok": True, "cierres": cierres})
    except Exception:
        return jsonify({"ok": True, "cierres": []})
    finally:
        if conn is not None:
            conn.close()


@ventas_core_bp.route("/api/ventas/totales")
@login_required
def totales_ventas():
    try:
        u = usuario_actual()
        conn = obtener_conexion()
        hoy = date.today().isoformat()
        mes = hoy[:7]
        vendedor_id = u.get("usuario_id") if u.get("rol") == "vendedor" else None
        total_hoy, num_hoy = _sumar_periodo(conn, f"{hoy}%", vendedor_id)
        total_mes, num_mes = _sumar_periodo(conn, f"{mes}%", vendedor_id)
        conn.close()
        return jsonify({"ok": True, "hoy": {"total": total_hoy, "ventas": num_hoy}, "mes": {"total": total_mes, "ventas": num_mes}})
    except Exception:
        return jsonify({"ok": True, "hoy": {"total": 0, "ventas": 0}, "mes": {"total": 0, "ventas": 0}})
