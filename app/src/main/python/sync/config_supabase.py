"""config_supabase.py - Extracted from config.py"""
"""
╔══════════════════════════════════════════════════════════════╗
║   supabase_sync.py  —  TPV ULTRA SMART  v6.1               ║
║   Sincronización dinámica + Historial Diario                ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════
#  PERSISTENCIA DE CONFIGURACION A DISCO
# ══════════════════════════════════════════════════════════════
_CONFIG_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), ".supabase_config.json")

def verificar_supabase():
    global SUPABASE_OK
    url = SUPABASE_CONFIG.get("url", "")
    key = SUPABASE_CONFIG.get("anon_key", "")
    if (url.startswith("https://") and
            "TU-PROYECTO" not in url and
            "TU_ANON_KEY"  not in key and
            len(key) > 20):
        SUPABASE_OK = True
        print(f"✅ Supabase configurado: {url}")
    else:
        SUPABASE_OK = False
        print("⚠️  Supabase no configurado — solo SQLite local.")
    return SUPABASE_OK

def mostrar_sql_configuracion():
    print("\n" + "═"*60)
    print("SQL PARA EJECUTAR EN SUPABASE DASHBOARD → SQL EDITOR:")
    print("═"*60)
    print(SQL_COMPLETO)
    print("═"*60 + "\n")

def _headers():
    return {
        "apikey":        SUPABASE_CONFIG["anon_key"],
        "Authorization": f"Bearer {SUPABASE_CONFIG['anon_key']}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation"
    }

def _peticion(url, metodo="GET", datos=None, timeout=10, reintentos=2):
    """HTTP genérico a Supabase con reintentos automáticos."""
    ultimo_error = None
    for intento in range(reintentos + 1):
        try:
            body = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos else None
            req  = urllib.request.Request(url, data=body, method=metodo)
            for k, v in _headers().items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                contenido = resp.read().decode("utf-8")
                return json.loads(contenido) if contenido else {}
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8") if e.fp else ""
            ultimo_error = f"HTTP {e.code}: {cuerpo[:200]}"
            if e.code < 500:  # 4xx → no reintentar
                break
        except urllib.error.URLError as e:
            ultimo_error = f"Red: {e.reason}"
        except Exception as e:
            ultimo_error = str(e)
            break
    print(f"⚠️  Supabase [{metodo}] {url.split('?')[0]} → {ultimo_error}")
    return None

# ══════════════════════════════════════════════════════════════
#  VERIFICACIÓN DINÁMICA DE TABLAS
# ══════════════════════════════════════════════════════════════
def verificar_tablas_supabase() -> dict:
    """
    Verifica qué tablas existen en Supabase haciendo un HEAD/GET a cada una.
    Devuelve: { nombre_tabla: True/False, ... }
    """
    if not SUPABASE_OK:
        return {t: None for t in TABLAS_SQL}

    resultado = {}
    for tabla in TABLAS_SQL:
        url = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}?limit=0"
        res = _peticion(url, timeout=5)
        # Si devuelve lista (vacía o con datos) → existe
        resultado[tabla] = isinstance(res, list)

    return resultado

# ══════════════════════════════════════════════════════════════
#  SETUP DINÁMICO — CREAR TABLAS FALTANTES
# ══════════════════════════════════════════════════════════════
def _verificar_rpc_exec_sql() -> bool:
    """Verifica si la RPC exec_sql existe en Supabase."""
    try:
        res = _peticion(
            f"{SUPABASE_CONFIG['url']}/rest/v1/rpc/exec_sql",
            metodo="POST",
            datos={"sql_query": "SELECT 1"},
            timeout=5
        )
        if res is not None and not isinstance(res, dict):
            return True
        if isinstance(res, dict) and "error" not in str(res):
            return True
    except Exception:
        pass
    return False


def setup_supabase() -> dict:
    """
    Verifica qué tablas faltan y las crea usando la RPC exec_sql de Supabase
    o devuelve el SQL para ejecutarlo manualmente.
    """
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}

    # 1. Verificar tablas existentes
    estado_tablas  = verificar_tablas_supabase()
    tablas_ok      = [t for t, v in estado_tablas.items() if v is True]
    tablas_faltantes = [t for t, v in estado_tablas.items() if v is False]
    tablas_error     = [t for t, v in estado_tablas.items() if v is None]

    if not tablas_faltantes and not tablas_error:
        return {
            "ok": True,
            "mensaje": f"Todas las tablas existen ({len(tablas_ok)} tablas)",
            "tablas_existentes": tablas_ok,
            "tablas_creadas": [],
            "tablas": estado_tablas,
        }

    # 2. Verificar si RPC exec_sql existe
    tiene_rpc = _verificar_rpc_exec_sql()

    if not tiene_rpc:
        sql_manual = "\n\n".join(
            f"-- {tabla}\n{TABLAS_SQL[tabla]}" for tabla in tablas_faltantes
        )
        if tablas_error:
            sql_manual += "\n\n-- Tablas con error de conexión (verificar manualmente):\n"
            sql_manual += "\n".join(f"-- {t}" for t in tablas_error)
        return {
            "ok": False,
            "mensaje": f"RPC exec_sql no existe. {len(tablas_ok)} tablas OK, {len(tablas_faltantes)} faltan.",
            "tablas_existentes": tablas_ok,
            "tablas_creadas": [],
            "tablas_fallidas": tablas_faltantes,
            "tablas_error": tablas_error,
            "sql_pendiente": sql_manual,
            "tablas": estado_tablas,
            "instruccion": "Ejecuta el SQL en Supabase Dashboard > SQL Editor, o crea la RPC exec_sql primero.",
        }

    # 3. Intentar crear via RPC exec_sql
    creadas  = []
    fallidas = []
    sql_pendiente = []

    for tabla in tablas_faltantes:
        sql = TABLAS_SQL[tabla]
        res = _peticion(
            f"{SUPABASE_CONFIG['url']}/rest/v1/rpc/exec_sql",
            metodo="POST",
            datos={"sql_query": sql},
            timeout=15
        )
        if res is not None and not isinstance(res, dict) or (isinstance(res, dict) and "error" not in res):
            creadas.append(tabla)
            print(f"Tabla creada en Supabase: {tabla}")
        else:
            fallidas.append(tabla)
            sql_pendiente.append(f"-- {tabla}\n{sql}")
            print(f"Tabla '{tabla}' no se pudo crear via RPC")

    # 4. Reverificar
    nuevo_estado = verificar_tablas_supabase()

    return {
        "ok":                len(fallidas) == 0 or len(creadas) > 0,
        "mensaje":           f"{len(creadas)} creadas, {len(tablas_ok)} existian, {len(fallidas)} requieren SQL manual",
        "tablas_existentes": tablas_ok,
        "tablas_creadas":    creadas,
        "tablas_fallidas":   fallidas,
        "sql_pendiente":     "\n\n".join(sql_pendiente) if sql_pendiente else None,
        "tablas":            nuevo_estado,
        "instruccion":       "Ejecuta el SQL en Supabase Dashboard > SQL Editor" if fallidas else None,
    }

def obtener_sql_completo() -> str:
    return SQL_COMPLETO

# ══════════════════════════════════════════════════════════════
#  HISTORIAL DIARIO
# ══════════════════════════════════════════════════════════════
def guardar_historial_diario(snapshot: dict) -> dict:
    """
    Guarda un snapshot diario en Supabase tpv_historial_diario.
    """
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}

    tabla = SUPABASE_CONFIG["tabla_historial"]
    fecha = snapshot.get("fecha", datetime.now().strftime("%Y-%m-%d"))

    datos = {
        "fecha":             fecha,
        "total_ventas":      float(snapshot.get("total_ventas", 0)),
        "num_transacciones": int(snapshot.get("num_transacciones", 0)),
        "productos_activos": int(snapshot.get("productos_activos", 0)),
        "inventario_items":  int(snapshot.get("inventario_items", 0)),
        "ventas_data":       snapshot.get("ventas_data", []),
        "inventario_data":   snapshot.get("inventario_data", []),
        "config_snapshot":   snapshot.get("config_snapshot", {}),
        "ts_guardado":       snapshot.get("ts_guardado", datetime.now().isoformat()),
    }

    url = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"

    headers_upsert = _headers()
    headers_upsert["Prefer"] = "return=representation,resolution=merge-duplicates"
    try:
        body = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        req  = urllib.request.Request(url, data=body, method="POST")
        for k, v in headers_upsert.items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print(f"☁️  Historial diario guardado: {fecha}")
        return {"ok": True, "fecha": fecha, "mensaje": f"Snapshot {fecha} guardado en Supabase"}
    except Exception as e:
        print(f"⚠️  Error guardando historial: {e}")
        return {"ok": False, "mensaje": str(e)}


def obtener_historial_diario(limite=30) -> dict:
    """Obtiene los últimos N días del historial desde Supabase."""
    if not SUPABASE_OK:
        return {"ok": False, "historial": [], "mensaje": "Supabase no configurado"}

    tabla = SUPABASE_CONFIG["tabla_historial"]
    url   = (f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}"
             f"?select=fecha,total_ventas,num_transacciones,productos_activos,"
             f"inventario_items,ts_guardado"
             f"&order=fecha.desc&limit={limite}")
    res = _peticion(url)
    if isinstance(res, list):
        return {"ok": True, "historial": res, "total": len(res)}
    return {"ok": False, "historial": [], "mensaje": "Error obteniendo historial"}


def obtener_historial_detalle(fecha: str) -> dict:
    """Obtiene el detalle completo de un día específico."""
    if not SUPABASE_OK:
        return {"ok": False, "mensaje": "Supabase no configurado"}

    tabla = SUPABASE_CONFIG["tabla_historial"]
    url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}?fecha=eq.{fecha}&select=*"
    res   = _peticion(url)
    if isinstance(res, list) and res:
        return {"ok": True, "dia": res[0]}
    return {"ok": False, "mensaje": f"No hay historial para {fecha}"}

# ══════════════════════════════════════════════════════════════
#  ESTADO TPV
# ══════════════════════════════════════════════════════════════
def cargar_desde_supabase():
    if not SUPABASE_OK:
        return None
    tabla = SUPABASE_CONFIG["tabla_estado"]
    rid   = SUPABASE_CONFIG["registro_id"]
    url   = f"{SUPABASE_CONFIG['url']}/rest/v1/{tabla}?id=eq.{rid}&select=estado"
    res   = _peticion(url)
    if res and isinstance(res, list) and res:
        estado = res[0].get("estado")
        if estado and isinstance(estado, dict) and estado:
            print(f"☁️  Estado cargado desde Supabase ({datetime.now().strftime('%H:%M:%S')})")
            return estado
    return None
