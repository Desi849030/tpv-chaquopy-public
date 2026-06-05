"""database.py - Facade DAO: re-exporta funciones de modulos DAO para compatibilidad.
Los modulos reales estan en: db_connection, db_users, db_products, db_ventas, db_config"""
from __future__ import annotations
from models import Producto, Venta, Usuario, Cliente, DetalleVenta
from typing import Optional, List, Dict, Any, Tuple
from db_connection import (DB_FILE, DB_PATH, _hash_password, verificar_password,
    obtener_conexion, agregar_log, obtener_info_db, crear_tabla_audit, audit_log)
from db_users import (_crear_desarrollador_default, login_usuario, crear_usuario,
    cambiar_password, resetear_password, listar_usuarios, desactivar_usuario)
from db_products import (cargar_stock_masivo, registrar_entrada_producto,
    obtener_inventario_general, obtener_historial_entradas, asignar_inventario_diario,
    obtener_inventario_diario, actualizar_vendido_diario, limpiar_inventarios_diarios,
    obtener_productos_catalogo, sincronizar_productos_catalogo,
    importar_catalogo_a_inventario, eliminar_producto_inventario_general,
    consultar_inventario_actual)
from db_ventas import (consultar_ventas_por_fecha, consultar_resumen_ventas,
    consultar_ganancias_por_dia, guardar_historial_diario_local,
    obtener_historial_diario_local, obtener_historial_detalle_local)
from db_config import (crear_tablas, crear_licencia, listar_licencias,
    verificar_licencia_activa, desactivar_licencia, sincronizar_estado_completo,
    limpiar_tablas_completo, reconstruir_desde_productos, cargar_estado,
    guardar_estado, _sincronizar_tablas_relacionales)
