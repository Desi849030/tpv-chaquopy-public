"""Rutas de inventario y catálogo — /api/inventario/*, /api/catalogo/*, /api/stock/*, /api/sincronizar-*"""
import json as _json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from validacion_productos import validar_productos_lote, importar_productos_validados
from db_config import limpiar_tablas_completo, reconstruir_desde_productos, sincronizar_estado_completo
from db_connection import agregar_log, obtener_conexion
from db_products import asignar_inventario_diario, cargar_stock_masivo, eliminar_producto_inventario_general, importar_catalogo_a_inventario, limpiar_inventarios_diarios, obtener_historial_entradas, obtener_inventario_diario, obtener_inventario_general, obtener_productos_catalogo, registrar_entrada_producto, sincronizar_productos_catalogo

from modules.inventory_helpers import inv_bp
