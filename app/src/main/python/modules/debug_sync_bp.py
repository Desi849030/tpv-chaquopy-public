# -*- coding: utf-8 -*-
"""Blueprint: Debug - Tablas SQLite + Estado Sync Supabase (solo admin/dev)"""

from flask import Blueprint, jsonify
from decorators import login_required, requiere_rol, usuario_actual
from db_connection import obtener_conexion

debug_sync_bp = Blueprint('debug_sync', __name__)


@debug_sync_bp.route('/api/debug/tables')
@login_required
def debug_tables():
    """Muestra conteo de registros de TODAS las tablas SQLite."""
    u = usuario_actual()
    if u.get('rol') not in ('desarrollador', 'administrador'):
        return jsonify({"error": "Sin permisos"}), 403

    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        # Obtener todas las tablas
        tablas = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        resultado = {}
        for (tbl,) in tablas:
            try:
                count = cursor.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                resultado[tbl] = count
            except Exception:
                resultado[tbl] = "error"

        # Info de la BD
        import os
        from db_connection import DB_FILE
        size_kb = round(os.path.getsize(DB_FILE) / 1024, 2) if os.path.exists(DB_FILE) else 0
        quick = cursor.execute("PRAGMA quick_check").fetchone()[0]
        wal = cursor.execute("PRAGMA journal_mode").fetchone()[0]

        return jsonify({
            "ok": True,
            "tablas": resultado,
            "total_tablas": len(resultado),
            "total_registros": sum(v for v in resultado.values() if isinstance(v, int)),
            "db_size_kb": size_kb,
            "integrity": quick,
            "journal_mode": wal,
        })
    finally:
        conn.close()


@debug_sync_bp.route('/api/debug/supabase')
@login_required
def debug_supabase():
    """Estado de la sincronización con Supabase."""
    u = usuario_actual()
    if u.get('rol') not in ('desarrollador', 'administrador'):
        return jsonify({"error": "Sin permisos"}), 403

    resultado = {
        "supabase_configurado": False,
        "supabase_online": False,
        "tablas_sincronizadas": [],
        "ultima_sync": None,
        "errores_recientes": [],
    }

    try:
        from sync.config_supabase import SUPABASE_CONFIG
        resultado["supabase_configurado"] = bool(SUPABASE_CONFIG.get("url"))
        resultado["url"] = SUPABASE_CONFIG.get("url", "")[:30] + "..."
    except Exception:
        pass

    try:
        from supabase_sync import SUPABASE_OK, supabase
        resultado["supabase_online"] = SUPABASE_OK
        if SUPABASE_OK and supabase:
            # Intentar leer una tabla remota
            try:
                res = supabase.table("usuarios").select("count", count="exact").execute()
                resultado["tablas_sincronizadas"].append("usuarios")
            except Exception:
                pass
            try:
                res = supabase.table("productos").select("count", count="exact").execute()
                resultado["tablas_sincronizadas"].append("productos")
            except Exception:
                pass
            try:
                res = supabase.table("historial_ventas").select("count", count="exact").execute()
                resultado["tablas_sincronizadas"].append("historial_ventas")
            except Exception:
                pass
    except Exception:
        pass

    # Revisar logs recientes de sync
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT fecha, mensaje FROM logs_sistema "
            "WHERE mensaje LIKE '%sync%' OR mensaje LIKE '%supabase%' "
            "ORDER BY fecha DESC LIMIT 5"
        ).fetchall()
        resultado["ultima_sync"] = rows[0]["fecha"] if rows else None
        resultado["errores_recientes"] = [{"fecha": r["fecha"], "msg": r["mensaje"]} for r in rows]
        conn.close()
    except Exception:
        pass

    return jsonify(resultado)


@debug_sync_bp.route('/api/debug/agent_status')
@login_required
def debug_agent():
    """Estado del agente IA y sus módulos."""
    u = usuario_actual()
    if u.get('rol') not in ('desarrollador',):
        return jsonify({"error": "Solo desarrollador"}), 403

    try:
        from ia.agent_master import agent
        status = agent.get_status()
    except Exception as e:
        status = {"active": False, "error": str(e)}

    return jsonify({"ok": True, "agent": status})
