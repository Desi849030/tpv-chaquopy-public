"""Rutas de inventario y catálogo — /api/inventario/*, /api/catalogo/*, /api/stock/*, /api/sincronizar-*"""
import json as _json
from datetime import datetime, timedelta
from flask import request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from validacion_productos import validar_productos_lote, importar_productos_validados
from database import (
    registrar_entrada_producto, obtener_inventario_general,
    importar_catalogo_a_inventario, eliminar_producto_inventario_general,
    obtener_productos_catalogo, sincronizar_productos_catalogo,
    sincronizar_estado_completo, cargar_stock_masivo, limpiar_tablas_completo,
    reconstruir_desde_productos, obtener_historial_entradas,
    asignar_inventario_diario, obtener_inventario_diario,
    limpiar_inventarios_diarios, agregar_log, obtener_conexion
)

from routes.inventory_bp import inv_bp
from routes.inventory_helpers import *
from routes.inventory_crud import *
from routes.inventory_catalogo import *
from routes.inventory_diario import *
from routes.inventory_other import *
