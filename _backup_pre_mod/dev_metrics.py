"""
dev_metrics.py - Blueprint Flask para el panel de desarrollador
Metricas en tiempo real: RAM, almacenamiento, formulas de inventario
v2 corregido: usa inventario_general (schema real del TPV)
"""

import os
import gc
import sys
import time
import sqlite3
import logging
from functools import wraps
from flask import Blueprint, jsonify

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

dev_metrics_bp = Blueprint("dev_metrics", __name__)
_log = logging.getLogger("dev_metrics")
_db_path = None


def _get_db_path():
    """Retorna la ruta real de tpv_datos.db usando database.DB_FILE."""
    global _db_path
    if _db_path and os.path.exists(_db_path):
        return _db_path
    try:
        from database import DB_FILE
        _db_path = DB_FILE
        return _db_path
    except ImportError:
        _log.debug("[dev_metrics] No se pudo importar database.DB_FILE")
    data_dir = os.environ.get("TPV_FILES_DIR", os.getcwd())
    candidate = os.path.join(data_dir, "tpv_datos.db")
    if os.path.exists(candidate):
        _db_path = candidate
    return _db_path


# ─────────────────────────────────────────────
# RAM del proceso y sistema
# ─────────────────────────────────────────────

def _ram_info():
    """Estrategia: psutil > /proc/self/status > resource > gc fallback."""
    result = {
        "proceso_mb": 0.0, "proceso_bytes": 0,
        "sistema_total_mb": 0.0, "sistema_usado_mb": 0.0,
        "sistema_libre_mb": 0.0, "sistema_pct": 0.0,
        "fuente": "desconocido"
    }

    # 1. psutil (mas completo)
    if HAS_PSUTIL:
        try:
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info()
            result["proceso_bytes"] = mem.rss
            result["proceso_mb"] = round(mem.rss / 1024 / 1024, 2)
            vm = psutil.virtual_memory()
            result["sistema_total_mb"] = round(vm.total / 1024 / 1024, 2)
            result["sistema_usado_mb"] = round(vm.used / 1024 / 1024, 2)
            result["sistema_libre_mb"] = round(vm.available / 1024 / 1024, 2)
            result["sistema_pct"] = vm.percent
            result["fuente"] = "psutil"
            return result
        except Exception as e:
            _log.debug("[dev_metrics] psutil error: %s", e)

    # 2. /proc/self/status (Android/Linux nativo)
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    result["proceso_bytes"] = kb * 1024
                    result["proceso_mb"] = round(kb / 1024, 2)
                    result["fuente"] = "/proc/self/status"
                    break
        with open("/proc/meminfo", "r") as f:
            mem_data = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem_data[parts[0].rstrip(":")] = int(parts[1])
            total = mem_data.get("MemTotal", 0)
            free = mem_data.get("MemAvailable", 0)
            used = total - free
            result["sistema_total_mb"] = round(total / 1024, 2)
            result["sistema_usado_mb"] = round(used / 1024, 2)
            result["sistema_libre_mb"] = round(free / 1024, 2)
            result["sistema_pct"] = round((used / total * 100), 1) if total else 0
        return result
    except Exception as e:
        _log.debug("[dev_metrics] /proc error: %s", e)

    # 3. resource (fallback Unix)
    if HAS_RESOURCE:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            kb = usage.ru_maxrss
            result["proceso_bytes"] = kb * 1024
            result["proceso_mb"] = round(kb / 1024, 2)
            result["fuente"] = "resource"
            return result
        except Exception as e:
            _log.debug("[dev_metrics] resource error: %s", e)

    # 4. gc fallback (muy aproximado)
    try:
        gc.collect()
        objetos = len(gc.get_objects())
        estimado = objetos * 256
        result["proceso_bytes"] = estimado
        result["proceso_mb"] = round(estimado / 1024 / 1024, 2)
        result["fuente"] = "gc_estimado"
    except Exception:
        pass

    return result


# ─────────────────────────────────────────────
# Almacenamiento
# ─────────────────────────────────────────────

def _storage_info(db_path=None):
    """Retorna uso de almacenamiento y tamano de la BD SQLite."""
    result = {
        "db_path": db_path or "desconocido",
        "db_size_kb": 0.0, "db_size_mb": 0.0,
        "disco_total_mb": 0.0, "disco_usado_mb": 0.0,
        "disco_libre_mb": 0.0, "disco_pct": 0.0,
    }

    # Tamano de la BD
    if db_path and os.path.exists(db_path):
        try:
            sz = os.path.getsize(db_path)
            result["db_size_kb"] = round(sz / 1024, 2)
            result["db_size_mb"] = round(sz / 1024 / 1024, 3)
        except Exception as e:
            _log.debug("[dev_metrics] db size error: %s", e)

    # Disco (psutil o os.statvfs)
    if HAS_PSUTIL:
        try:
            disk = psutil.disk_usage("/")
            result["disco_total_mb"] = round(disk.total / 1024 / 1024, 2)
            result["disco_usado_mb"] = round(disk.used / 1024 / 1024, 2)
            result["disco_libre_mb"] = round(disk.free / 1024 / 1024, 2)
            result["disco_pct"] = disk.percent
        except Exception as e:
            _log.debug("[dev_metrics] psutil disk error: %s", e)
    else:
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            result["disco_total_mb"] = round(total / 1024 / 1024, 2)
            result["disco_usado_mb"] = round(used / 1024 / 1024, 2)
            result["disco_libre_mb"] = round(free / 1024 / 1024, 2)
            result["disco_pct"] = round(used / total * 100, 1) if total else 0
        except Exception as e:
            _log.debug("[dev_metrics] statvfs error: %s", e)

    return result


# ─────────────────────────────────────────────
# Formulas de inventario (inventario_general)
# ─────────────────────────────────────────────

def _inventario_formulas(db_path):
    """
    Calcula metricas del inventario desde inventario_general.

    Schema real:
        producto_id, nombre, stock_actual, stock_minimo,
        precio_compra, precio_venta, categoria, unidad_medida, actualizado

    Formulas:
        Margen bruto = (Valor_venta - Valor_costo) / Valor_venta * 100
        Cobertura    = (Total - Sin_stock) / Total * 100
        Ganancia     = Sum(precio_venta * stock) - Sum(precio_compra * stock)
    """
    result = {
        "total_productos": 0,
        "total_unidades": 0,
        "valor_venta_total": 0.0,
        "valor_costo_total": 0.0,
        "margen_bruto_total": 0.0,
        "margen_bruto_pct": 0.0,
        "ganancia_potencial": 0.0,
        "productos_sin_stock": 0,
        "productos_precio_invalido": 0,
        "productos_sin_precio": 0,
        "categorias": [],
        "top5_valor": [],
        "formula_rentabilidad": "N/A",
        "formula_cobertura": "N/A",
        "error": None
    }

    if not db_path or not os.path.exists(db_path):
        result["error"] = "BD no encontrada: {}".format(db_path)
        return result

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # -- Totales generales --
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(stock_actual), 0) as unidades,
                COALESCE(SUM(precio_venta * COALESCE(stock_actual, 0)), 0) as val_venta,
                COALESCE(SUM(COALESCE(precio_compra, 0) * COALESCE(stock_actual, 0)), 0) as val_costo,
                COUNT(CASE WHEN COALESCE(stock_actual, 0) = 0 THEN 1 END) as sin_stock,
                COUNT(CASE WHEN precio_venta < COALESCE(precio_compra, 0) THEN 1 END) as precio_invalido,
                COUNT(CASE WHEN precio_venta IS NULL OR precio_venta = 0 THEN 1 END) as sin_precio
            FROM inventario_general
        """)
        row = cur.fetchone()
        if row:
            result["total_productos"]           = row["total"] or 0
            result["total_unidades"]            = row["unidades"] or 0
            result["valor_venta_total"]         = round(float(row["val_venta"] or 0), 2)
            result["valor_costo_total"]         = round(float(row["val_costo"] or 0), 2)
            result["productos_sin_stock"]       = row["sin_stock"] or 0
            result["productos_precio_invalido"] = row["precio_invalido"] or 0
            result["productos_sin_precio"]      = row["sin_precio"] or 0

        # -- Formula de rentabilidad --
        vv = result["valor_venta_total"]
        vc = result["valor_costo_total"]
        if vv > 0:
            margen = vv - vc
            result["margen_bruto_total"] = round(margen, 2)
            result["margen_bruto_pct"]   = round((margen / vv) * 100, 1)
            result["ganancia_potencial"] = round(margen, 2)
            result["formula_rentabilidad"] = "({} - {}) / {} x 100 = {}%".format(
                vv, vc, vv, result["margen_bruto_pct"])

        # -- Formula de cobertura de stock --
        tot = result["total_productos"]
        sin = result["productos_sin_stock"]
        if tot > 0:
            pct = round(((tot - sin) / tot) * 100, 1)
            result["formula_cobertura"] = "({} - {}) / {} x 100 = {}% con stock".format(
                tot, sin, tot, pct)

        # -- Categorias --
        try:
            cur.execute("""
                SELECT
                    COALESCE(categoria, 'General') as cat,
                    COUNT(*) as qty,
                    COALESCE(SUM(stock_actual), 0) as units,
                    COALESCE(SUM(precio_venta * COALESCE(stock_actual, 0)), 0) as valor
                FROM inventario_general
                GROUP BY cat
                ORDER BY valor DESC
                LIMIT 8
            """)
            result["categorias"] = [
                {"nombre": r["cat"], "productos": r["qty"],
                 "unidades": r["units"], "valor": round(float(r["valor"]), 2)}
                for r in cur.fetchall()
            ]
        except Exception as e:
            _log.debug("[dev_metrics] categorias error: %s", e)

        # -- Top 5 por valor de inventario --
        try:
            cur.execute("""
                SELECT
                    nombre,
                    precio_venta,
                    COALESCE(stock_actual, 0) as cantidad,
                    precio_venta * COALESCE(stock_actual, 0) as valor_total
                FROM inventario_general
                ORDER BY valor_total DESC
                LIMIT 5
            """)
            result["top5_valor"] = [
                {"nombre": r["nombre"],
                 "precio": round(float(r["precio_venta"] or 0), 2),
                 "cantidad": r["cantidad"],
                 "valor_total": round(float(r["valor_total"] or 0), 2)}
                for r in cur.fetchall()
            ]
        except Exception as e:
            _log.debug("[dev_metrics] top5 error: %s", e)

        conn.close()

    except sqlite3.OperationalError as e:
        result["error"] = "OperationalError: {}".format(str(e))
        _log.debug("[dev_metrics] sqlite error: %s", e)
    except Exception as e:
        result["error"] = str(e)
        _log.debug("[dev_metrics] inventario error: %s", e)

    return result


# ─────────────────────────────────────────────
# Decorador: solo rol desarrollador/admin
# ─────────────────────────────────────────────

def _dev_only(f):
    """Verifica que el usuario tenga rol desarrollador o administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            from flask import session
            # FIX: el rol esta dentro del objeto usuario
            usuario = session.get("usuario", {})
            rol = usuario.get("rol", "") if isinstance(usuario, dict) else str(session.get("rol", ""))
            if rol not in ("desarrollador", "administrador"):
                return jsonify({"ok": False, "error": "Acceso restringido al panel de desarrollador"}), 403
        except Exception:
            pass
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@dev_metrics_bp.route("/api/dev/metrics", methods=["GET"])
@_dev_only
def get_dev_metrics():
    """GET /api/dev/metrics - Todas las metricas de un golpe."""
    db_path = _get_db_path()
    ram     = _ram_info()
    storage = _storage_info(db_path)
    inv     = _inventario_formulas(db_path)

    try:
        from flask import current_app
        server_start = current_app.config.get("SERVER_START_TIME", None)
    except Exception:
        server_start = None
    uptime_s = round(time.time() - server_start, 1) if server_start else None

    return jsonify({
        "ok": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_epoch": int(time.time()),
        "uptime_s": uptime_s,
        "ram": ram,
        "storage": storage,
        "inventario": inv
    })


@dev_metrics_bp.route("/api/dev/metrics/ram", methods=["GET"])
@_dev_only
def get_ram_only():
    return jsonify({"ok": True, "ram": _ram_info()})


@dev_metrics_bp.route("/api/dev/metrics/storage", methods=["GET"])
@_dev_only
def get_storage_only():
    return jsonify({"ok": True, "storage": _storage_info(_get_db_path())})


@dev_metrics_bp.route("/api/dev/metrics/inventario", methods=["GET"])
@_dev_only
def get_inventario_only():
    return jsonify({"ok": True, "inventario": _inventario_formulas(_get_db_path())})


# --- Página HTML del panel de métricas ---
@dev_metrics_bp.route("/dev/metricas")
def panel_metricas():
    """Página HTML del panel de métricas del sistema."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Métricas del Sistema</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e0e0e0;font-family:system-ui,sans-serif;padding:12px;font-size:14px}
h2{color:#e94560;margin-bottom:12px;font-size:16px}
.card{background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:12px;margin-bottom:10px}
.card h3{color:#60a5fa;font-size:14px;margin-bottom:8px}
.row{display:flex;gap:10px;flex-wrap:wrap}
.col{flex:1;min-width:140px}
.val{font-size:20px;font-weight:bold;color:#22c55e}
.val.warn{color:#f59e0b}
.val.err{color:#ef4444}
.bar{height:8px;background:#1a1a2e;border-radius:4px;margin-top:6px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;background:#22c55e;transition:width .5s}
.bar-fill.warn{background:#f59e0b}
.bar-fill.err{background:#ef4444}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#0f3460;color:#60a5fa;padding:6px;text-align:left}
td{padding:5px;border-bottom:1px solid #1a1a2e}
.refresh{background:#e94560;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;margin-bottom:10px}
#status{color:#888;font-size:11px;margin-left:8px}
</style>
</head>
<body>
<button class="refresh" onclick="cargar()">Actualizar</button><span id="status"></span>
<div class="row"><div class="col"><div class="card"><h3>RAM</h3><div class="val" id="ram-val">--</div><div class="bar"><div class="bar-fill" id="ram-bar"></div></div></div></div>
<div class="col"><div class="card"><h3>Almacenamiento</h3><div class="val" id="stor-val">--</div><div class="bar"><div class="bar-fill" id="stor-bar"></div></div></div></div></div>
<div class="card"><h3>Inventario</h3><div id="inv-table"></div></div>
<div class="card"><h3>Detalle del Sistema</h3><pre id="detail" style="font-size:11px;white-space:pre-wrap;color:#aaa">Cargando...</pre></div>
<script>
function cargar(){var s=document.getElementById('status');s.textContent='Cargando...';
fetch('/api/dev/metrics').then(function(r){if(!r.ok)throw new Error(r.status);return r.json();}).then(function(d){
document.getElementById('ram-val').textContent=d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0+'%';
var rb=document.getElementById('ram-bar');rb.style.width=d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0+'%';rb.className='bar-fill'+(d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0>80?' err':d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0>60?' warn':'');
document.getElementById('ram-val').className='val'+(d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0>80?' err':d.ram && d.ram.sistema_pct ? d.ram.sistema_pct : 0>60?' warn':'');
document.getElementById('stor-val').textContent=d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0+'%';
var sb=document.getElementById('stor-bar');sb.style.width=d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0+'%';sb.className='bar-fill'+(d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0>80?' err':d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0>60?' warn':'');
document.getElementById('stor-val').className='val'+(d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0>80?' err':d.storage && d.storage.disco_pct ? d.storage.disco_pct : 0>60?' warn':'');
document.getElementById('detail').textContent=JSON.stringify(d,null,2);
s.textContent='Actualizado: '+new Date().toLocaleTimeString();
}).catch(function(e){s.textContent='Error: '+e.message;});}
function cargarInv(){fetch('/api/dev/metrics/inventario').then(function(r){return r.json();}).then(function(d){
var h='<table><tr><th>Producto</th><th>Stock</th><th>Precio</th></tr>';
(d.items||d||[]).forEach(function(i){h+='<tr><td>'+i.nombre+'</td><td>'+(i.stock||i.stock_actual||0)+'</td><td>'+(i.precio||i.precio_venta||0)+'</td></tr>';});
h+='</table>';document.getElementById('inv-table').innerHTML=h;}).catch(function(){});}
cargar();cargarInv();
</script>
</body></html>"""
