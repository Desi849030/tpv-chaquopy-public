"""Ventas: Blueprint y helpers compartidos"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    agregar_log, obtener_conexion,
    consultar_ventas_por_fecha, consultar_resumen_ventas,
    consultar_ganancias_por_dia,
    guardar_historial_diario_local, obtener_historial_diario_local,
    obtener_historial_detalle_local,
)
from sync.supabase_sync import (
    guardar_historial_diario, obtener_historial_diario,
    obtener_historial_detalle, obtener_config_actual,
    verificar_tablas_supabase, obtener_sql_completo, setup_supabase,
)
import sync.supabase_sync as _sb

ventas_bp = Blueprint('ventas', __name__)
