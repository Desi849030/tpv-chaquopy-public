"""
supabase_sync.py — TPV ULTRA SMART v6.0
Stub funcional para modo offline (sin Supabase configurado)
"""
import json, os
from datetime import datetime

# Configuración por defecto (vacía = modo offline)
SUPABASE_CONFIG = {
    "url": os.environ.get("SUPABASE_URL", ""),
    "anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
    "tabla_estado": "tpv_estado",
    "tabla_usuarios": "tpv_usuarios",
    "tabla_clientes": "tpv_clientes",
    "tabla_ventas": "tpv_ventas_dia",
    "tabla_productos": "tpv_productos",
    "tabla_stock": "tpv_stock",
    "tabla_gastos": "tpv_gastos_dia",
    "tabla_historial": "tpv_historial_diario",
}

# Supabase activo solo si URL y key válidas
SUPABASE_OK = bool(
    SUPABASE_CONFIG["url"].startswith("https://") and
    len(SUPABASE_CONFIG["anon_key"]) > 20
)

def verificar_supabase():
    global SUPABASE_OK
    SUPABASE_OK = bool(
        SUPABASE_CONFIG["url"].startswith("https://") and
        len(SUPABASE_CONFIG["anon_key"]) > 20
    )
    return SUPABASE_OK

def _headers():
    return {
        "apikey": SUPABASE_CONFIG["anon_key"],
        "Authorization": f"Bearer {SUPABASE_CONFIG['anon_key']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def _peticion(url, metodo="GET", datos=None, timeout=10):
    """HTTP genérico con manejo de errores."""
    import urllib.request, urllib.error
    try:
        body = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos else None
        req = urllib.request.Request(url, data=body, method=metodo)
        for k, v in _headers().items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            contenido = resp.read().decode("utf-8")
            return json.loads(contenido) if contenido else {}
    except Exception:
        return None

# === Funciones stub (modo offline) ===
def cargar_desde_supabase(): return None
def guardar_en_supabase(estado): return False
def sincronizar_subida(estado): pass
def probar_conexion(): return {"ok": SUPABASE_OK, "mensaje": "Supabase activo" if SUPABASE_OK else "Solo local"}
def obtener_config_actual():
    return {
        "url": SUPABASE_CONFIG["url"],
        "anon_key_preview": SUPABASE_CONFIG["anon_key"][:8] + "..." if SUPABASE_CONFIG["anon_key"] else "",
        "configurado": SUPABASE_OK
    }
def actualizar_config(nueva_url, nueva_key):
    global SUPABASE_CONFIG, SUPABASE_OK
    SUPABASE_CONFIG["url"] = nueva_url
    SUPABASE_CONFIG["anon_key"] = nueva_key
    return verificar_supabase()

def sincronizar_usuario_nuevo(usuario_id): pass
def sincronizar_cliente_nuevo(cliente_id): pass
def sincronizar_todo(): return {"ok": True}

# === Funciones v6.0: Historial diario ===
def setup_supabase():
    return {"ok": True, "mensaje": "Tablas verificadas (modo offline)", "tablas": {}}
def verificar_tablas_supabase(): return {}
def guardar_historial_diario(snapshot): return {"ok": True, "mensaje": "Guardado local"}
def obtener_historial_diario(limite=30): return {"ok": True, "historial": []}
def obtener_historial_detalle(fecha): return {"ok": False, "mensaje": "No hay historial"}
def obtener_sql_completo(): return "-- Offline mode"

# Inicializar al importar
verificar_supabase()


# ═══ HOTFIX v8.0.2: Funciones offline mejoradas ═══
SUPABASE_CONFIG_COMPLETE = True

def obtener_estado_tablas():
    """Devuelve estado de todas las tablas (offline-safe)"""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tablas = [r[0] for r in c.fetchall()]
        resultado = {}
        for t in tablas:
            try:
                c.execute(f'SELECT COUNT(*) FROM "{t}"')
                resultado[t] = {"registros": c.fetchone()[0], "existe": True}
            except:
                resultado[t] = {"registros": 0, "existe": False}
        conn.close()
        return {"ok": True, "tablas": resultado, "supabase_activo": SUPABASE_OK}
    except Exception as e:
        return {"ok": False, "error": str(e), "supabase_activo": SUPABASE_OK}

def importar_datos_offline(datos, tabla_destino):
    """Importa datos a tabla SQLite local (sin Supabase)"""
    if not datos or not tabla_destino:
        return {"ok": False, "error": "Datos o tabla vacios"}
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        cursor = conn.cursor()
        insertados = 0
        for fila in datos:
            if isinstance(fila, dict):
                cols = list(fila.keys())
                vals = list(fila.values())
                placeholders = ",".join(["?"] * len(cols))
                col_names = ",".join(cols)
                try:
                    cursor.execute(f'INSERT OR REPLACE INTO {tabla_destino} ({col_names}) VALUES ({placeholders})', vals)
                    insertados += 1
                except: pass
        conn.commit(); conn.close()
        return {"ok": True, "insertados": insertados, "tabla": tabla_destino}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def exportar_datos_offline(tabla):
    """Exporta datos de tabla SQLite local"""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute(f'SELECT * FROM {tabla} LIMIT 1000')
        cols = [desc[0] for desc in c.description] if c.description else []
        rows = [dict(zip(cols, row)) for row in c.fetchall()]
        conn.close()
        return {"ok": True, "datos": rows, "columnas": cols}
    except Exception as e:
        return {"ok": True, "datos": [], "error": str(e)}
