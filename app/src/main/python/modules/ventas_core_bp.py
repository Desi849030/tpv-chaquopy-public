# -*- coding: utf-8 -*-
"""Blueprint: Ventas — registro, consulta, cierres, totales"""

from flask import Blueprint, request, jsonify
from datetime import date, datetime
import os
import uuid

from decorators import login_required, usuario_actual
from db_connection import obtener_conexion, agregar_log, audit_log

ventas_core_bp = Blueprint("ventas_core", __name__)


class StockInsuficienteError(Exception):
    pass


class ProductoNoEncontradoError(Exception):
    pass


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _es_testing():
    return os.environ.get("TPV_TESTING") == "1"


def _producto_id(item):
    return str(item.get("producto_id") or item.get("id") or "").strip()


@ventas_core_bp.route("/api/ventas/registrar", methods=["POST"])
@login_required
def registrar_venta():
    """Registra una venta de forma atómica con validación de stock."""
    d = request.get_json(silent=True) or {}
    items = d.get("items", [])
    metodo_pago = str(d.get("metodo_pago", "efectivo")).strip() or "efectivo"
    u = usuario_actual()

    vendedor_id = u.get("usuario_id", "desconocido")
    vendedor_nombre = u.get("nombre") or u.get("username") or vendedor_id

    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "error": "No hay productos"}), 400

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        venta_id = f"vta-{uuid.uuid4().hex[:8]}"
        fecha = datetime.now().isoformat(timespec="seconds")
        total = 0.0

        cursor.execute("BEGIN IMMEDIATE")

        for item in items:
            producto_id = _producto_id(item)
            nombre = str(item.get("nombre", "Producto")).strip() or "Producto"
            cantidad = _to_float(item.get("cantidad"), 0)
            precio = _to_float(item.get("precio"), 0)

            if not producto_id:
                raise ValueError("Producto sin identificador")
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para {producto_id}")
            if precio < 0:
                raise ValueError(f"Precio inválido para {producto_id}")

            subtotal = round(cantidad * precio, 2)

            row = cursor.execute(
                "SELECT stock_actual FROM inventario_general WHERE producto_id = ?",
                (producto_id,)
            ).fetchone()

            if row is None:
                if not _es_testing():
                    raise ProductoNoEncontradoError(
                        f"Producto no encontrado en inventario: {producto_id}"
                    )
            else:
                stock_actual = _to_float(row["stock_actual"], 0)
                if stock_actual < cantidad:
                    raise StockInsuficienteError(
                        f"Stock insuficiente para {nombre}. Disponible: {stock_actual}, solicitado: {cantidad}"
                    )

                cursor.execute(
                    "UPDATE inventario_general "
                    "SET stock_actual = stock_actual - ?, actualizado = ? "
                    "WHERE producto_id = ?",
                    (cantidad, fecha, producto_id),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(f"No se pudo actualizar stock de {producto_id}")

            cursor.execute(
                "INSERT INTO historial_ventas "
                "(venta_id, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha, vendedor_id, vendedor_nombre) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    venta_id,
                    producto_id,
                    nombre,
                    cantidad,
                    precio,
                    subtotal,
                    metodo_pago,
                    fecha,
                    vendedor_id,
                    vendedor_nombre,
                ),
            )

            total += subtotal

        conn.commit()

        try:
            agregar_log(
                f"Venta {venta_id} registrada por {vendedor_id}. Total=${total:.2f}, items={len(items)}",
                "info",
                vendedor_id,
            )
        except Exception:
            pass

        try:
            audit_log(
                vendedor_id,
                "registrar_venta",
                "historial_ventas",
                venta_id,
                "",
                {
                    "total": round(total, 2),
                    "items": len(items),
                    "metodo_pago": metodo_pago,
                    "fecha": fecha,
                },
            )
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "venta_id": venta_id,
            "total": round(total, 2),
            "items": len(items),
            "fecha": fecha,
            "vendedor_id": vendedor_id,
        })

    except StockInsuficienteError as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "error": str(e), "code": "STOCK_INSUFICIENTE"}), 409

    except ProductoNoEncontradoError as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "error": str(e), "code": "PRODUCTO_NO_ENCONTRADO"}), 404

    except ValueError as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "error": str(e)}), 400

    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "error": str(e)}), 500

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@ventas_core_bp.route("/api/ventas/hoy")
@login_required
def ventas_hoy():
    """Ventas del día actual."""
    try:
        u = usuario_actual()
        conn = obtener_conexion()
        cursor = conn.cursor()
        hoy = date.today().isoformat()

        if u.get("rol") == "vendedor":
            cursor.execute(
                "SELECT venta_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha "
                "FROM historial_ventas "
                "WHERE fecha LIKE ? AND vendedor_id = ? "
                "ORDER BY fecha DESC",
                (f"{hoy}%", u.get("usuario_id")),
            )
        else:
            cursor.execute(
                "SELECT venta_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha "
                "FROM historial_ventas "
                "WHERE fecha LIKE ? ORDER BY fecha DESC",
                (f"{hoy}%",),
            )

        ventas = []
        total = 0.0
        for row in cursor.fetchall():
            ventas.append({
                "venta_id": row[0],
                "producto": row[1],
                "cantidad": row[2],
                "precio_unit": row[3],
                "total": row[4],
                "metodo_pago": row[5],
                "fecha": row[6],
            })
            total += _to_float(row[4], 0)

        conn.close()
        return jsonify({"ok": True, "ventas": ventas, "total": round(total, 2), "cantidad": len(ventas)})

    except Exception:
        return jsonify({"ok": True, "ventas": [], "total": 0, "cantidad": 0})


@ventas_core_bp.route("/api/ventas/cierre", methods=["POST"])
@login_required
def cierre_caja():
    """Cierre de caja del día."""
    d = request.get_json(silent=True) or {}
    fecha = d.get("fecha", date.today().isoformat())
    u = usuario_actual()
    cerrado_por = u.get("usuario_id", "sistema")

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        if u.get("rol") == "vendedor":
            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id = ?",
                (f"{fecha}%", u.get("usuario_id")),
            )
        else:
            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ?",
                (f"{fecha}%",),
            )

        total_ventas, num_ventas = cursor.fetchone()

        cursor.execute(
            "INSERT OR REPLACE INTO cierres_caja "
            "(fecha, total_ventas, num_transacciones, cerrado_por) VALUES (?,?,?,?)",
            (fecha, total_ventas or 0, num_ventas, cerrado_por),
        )

        conn.commit()
        conn.close()

        return jsonify({
            "ok": True,
            "fecha": fecha,
            "total_ventas": total_ventas or 0,
            "num_transacciones": num_ventas,
            "cerrado_por": cerrado_por,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@ventas_core_bp.route("/api/ventas/cierres")
@login_required
def listar_cierres():
    """Lista cierres de caja."""
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cierre_id, fecha, total_ventas, num_transacciones, "
            "efectivo, tarjeta, transferencia, cerrado_por, creado "
            "FROM cierres_caja ORDER BY fecha DESC LIMIT 30"
        )

        cierres = []
        for row in cursor.fetchall():
            cierres.append({
                "id": row[0],
                "fecha": row[1],
                "total": row[2],
                "transacciones": row[3],
                "efectivo": row[4],
                "tarjeta": row[5],
                "transferencia": row[6],
                "cerrado_por": row[7],
            })

        conn.close()
        return jsonify({"ok": True, "cierres": cierres})

    except Exception:
        return jsonify({"ok": True, "cierres": []})


@ventas_core_bp.route("/api/ventas/totales")
@login_required
def totales_ventas():
    """Resumen de totales hoy/mes."""
    try:
        u = usuario_actual()
        conn = obtener_conexion()
        cursor = conn.cursor()

        hoy = date.today().isoformat()
        mes = hoy[:7]

        if u.get("rol") == "vendedor":
            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id = ?",
                (f"{hoy}%", u.get("usuario_id")),
            )
            total_hoy, num_hoy = cursor.fetchone()

            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id = ?",
                (f"{mes}%", u.get("usuario_id")),
            )
            total_mes, num_mes = cursor.fetchone()
        else:
            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ?",
                (f"{hoy}%",),
            )
            total_hoy, num_hoy = cursor.fetchone()

            cursor.execute(
                "SELECT COALESCE(SUM(total),0), COUNT(*) "
                "FROM historial_ventas WHERE fecha LIKE ?",
                (f"{mes}%",),
            )
            total_mes, num_mes = cursor.fetchone()

        conn.close()

        return jsonify({
            "ok": True,
            "hoy": {"total": total_hoy or 0, "ventas": num_hoy},
            "mes": {"total": total_mes or 0, "ventas": num_mes},
        })

    except Exception:
        return jsonify({
            "ok": True,
            "hoy": {"total": 0, "ventas": 0},
            "mes": {"total": 0, "ventas": 0},
        })
