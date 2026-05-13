"""Rutas de estado, supabase, SSE, debug, biometric, payment, branch, IA"""
import json, os, time, threading, webbrowser, queue as _queue
import urllib.request
from datetime import datetime
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from decorators import requiere_login, requiere_rol, usuario_actual
from database import (
    cargar_estado, guardar_estado, agregar_log, crear_tablas,
    obtener_info_db, DB_FILE,
)
from supabase_sync import (
    obtener_config_actual, actualizar_config,
    cargar_desde_supabase, guardar_en_supabase,
    sincronizar_todo, sincronizar_subida, probar_conexion,
    verificar_tablas_supabase, setup_supabase, obtener_sql_completo,
    guardar_historial_diario, obtener_historial_diario,
    obtener_historial_detalle, TABLAS_SQL,
)
import supabase_sync as _sb
from biometric_auth import check_biometric_availability, quick_login_setup
from payment_tokenizer import create_payment_record
from supabase_rls import get_branch_id, get_rls_headers

from routes.settings_helpers import settings_bp
