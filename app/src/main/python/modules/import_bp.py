# -*- coding: utf-8 -*-
"""Blueprint: Importación inteligente de productos (Excel/JSON)"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

import_bp = Blueprint('importar', __name__)


@import_bp.route('/api/importar/excel', methods=['POST'])
def importar_excel():
    """Importa productos desde JSON (simula carga de Excel)."""
    d = request.get_json(silent=True) or {}
    productos = d.get('productos', [])
    if not productos:
        return jsonify({"ok": False, "error": "No hay productos para importar"}), 400

    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        importados = 0
        actualizados = 0

        for p in productos:
            nombre = p.get('nombre', '').strip()
            if not nombre:
                continue
            precio = float(p.get('precio', 0))
            categoria = p.get('categoria', 'General')
            stock = int(p.get('stock', 0))
            um = p.get('um', 'Un')
            costo = float(p.get('costo', p.get('costoUnitario', p.get('precioCosto', precio * 0.7))))

            # Verificar si existe
            cursor.execute("SELECT producto_id FROM productos WHERE nombre = ?", (nombre,))
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    "UPDATE productos SET precio=?,categoria=?,unidad_medida=?,costo=?,activo=1 "
                    "WHERE producto_id=?",
                    (precio, categoria, um, costo, existente[0]))
                cursor.execute(
                    "UPDATE inventario_general SET stock_actual=?,precio_venta=?,actualizado=? "
                    "WHERE producto_id=?",
                    (stock, precio, datetime.now().isoformat(), existente[0]))
                actualizados += 1
            else:
                pid = f"prod-{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    "INSERT INTO productos (producto_id,nombre,precio,costo,categoria,"
                    "unidad_medida,activo) VALUES (?,?,?,?,?,?,1)",
                    (pid, nombre, precio, costo, categoria, um))
                cursor.execute(
                    "INSERT INTO inventario_general (producto_id,nombre,stock_actual,"
                    "stock_minimo,precio_venta,actualizado) VALUES (?,?,?,5,?,?)",
                    (pid, nombre, stock, precio, datetime.now().isoformat()))
                importados += 1

        conn.commit()
        conn.close()
        return jsonify({"ok": True, "importados": importados, "actualizados": actualizados,
                        "total": len(productos)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@import_bp.route('/api/importar/previsualizar', methods=['POST'])
def previsualizar():
    """Previsualiza datos antes de importar."""
    d = request.get_json(silent=True) or {}
    productos = d.get('productos', [])
    return jsonify({"ok": True, "productos": productos, "total": len(productos),
                    "mensaje": f"{len(productos)} productos listos para importar"})
