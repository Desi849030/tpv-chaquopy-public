"""
dev_metrics.py - Blueprint Flask para el panel de desarrollador
Metricas en tiempo real: RAM, almacenamiento, formulas de inventario
v2 corregido: usa inventario_general (schema real del TPV)
"""

import os, gc, sys, time, sqlite3, logging
from functools import wraps

try:
    from flask import Blueprint, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    Blueprint = None
    jsonify = lambda x: x

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

dev_metrics_bp = None
if HAS_FLASK:
    dev_metrics_bp = Blueprint("dev_metrics", __name__)
_log = logging.getLogger("dev_metrics")
_db_path = None


def _get_db_path():
    """Retorna la ruta real de tpv_datos.db buscando en multiples ubicaciones."""
    global _db_path
    if _db_path and os.path.exists(_db_path):
        return _db_path
    try:
        from db_connection import DB_FILE
        if DB_FILE and os.path.exists(DB_FILE):
            _db_path = DB_FILE
            return _db_path
    except ImportError:
        pass
    for p in sys.path:
        if p and os.path.isdir(p):
            candidate = os.path.join(p, 'tpv_datos.db')
            if os.path.exists(candidate):
                _db_path = candidate
                return _db_path
            parent = os.path.dirname(p)
            candidate = os.path.join(parent, 'tpv_datos.db')
            if os.path.exists(candidate):
                _db_path = candidate
                return _db_path
    for d in [os.getcwd(), os.path.dirname(os.getcwd()),
              os.path.join(os.path.abspath('.'), 'app', 'src', 'main', 'python')]:
        if not d:
            continue
        candidate = os.path.join(d, 'tpv_datos.db')
        if os.path.exists(candidate):
            _db_path = candidate
            return _db_path
    data_dir = os.environ.get("TPV_FILES_DIR", os.getcwd())
    _db_path = os.path.join(data_dir, 'tpv_datos.db')
    return _db_path


def _ram_info():
    result = {"proceso_mb": 0.0, "proceso_bytes": 0, "sistema_total_mb": 0.0,
              "sistema_usado_mb": 0.0, "sistema_libre_mb": 0.0, "sistema_pct": 0.0, "fuente": "desconocido"}
    if HAS_PSUTIL:
        try:
            proc = psutil.Process(os.getpid()); mem = proc.memory_info()
            result["proceso_bytes"] = mem.rss; result["proceso_mb"] = round(mem.rss / 1024 / 1024, 2)
            vm = psutil.virtual_memory()
            result["sistema_total_mb"] = round(vm.total / 1024 / 1024, 2)
            result["sistema_usado_mb"] = round(vm.used / 1024 / 1024, 2)
            result["sistema_libre_mb"] = round(vm.available / 1024 / 1024, 2)
            result["sistema_pct"] = vm.percent; result["fuente"] = "psutil"; return result
        except Exception: pass
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1]); result["proceso_bytes"] = kb * 1024
                    result["proceso_mb"] = round(kb / 1024, 2); result["fuente"] = "/proc/self/status"; break
        with open("/proc/meminfo", "r") as f:
            mem_data = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2: mem_data[parts[0].rstrip(":")] = int(parts[1])
            total = mem_data.get("MemTotal", 0); free = mem_data.get("MemAvailable", 0); used = total - free
            result["sistema_total_mb"] = round(total / 1024, 2)
            result["sistema_usado_mb"] = round(used / 1024, 2)
            result["sistema_libre_mb"] = round(free / 1024, 2)
            result["sistema_pct"] = round((used / total * 100), 1) if total else 0
        return result
    except Exception: pass
    if HAS_RESOURCE:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF); kb = usage.ru_maxrss
            result["proceso_bytes"] = kb * 1024; result["proceso_mb"] = round(kb / 1024, 2)
            result["fuente"] = "resource"; return result
        except Exception: pass
    try:
        gc.collect(); objetos = len(gc.get_objects()); estimado = objetos * 256
        result["proceso_bytes"] = estimado; result["proceso_mb"] = round(estimado / 1024 / 1024, 2)
        result["fuente"] = "gc_estimado"
    except Exception: pass
    return result


def _storage_info(db_path=None):
    result = {"db_path": db_path or "desconocido", "db_size_kb": 0.0, "db_size_mb": 0.0,
              "num_indexes": 0,
              "disco_total_mb": 0.0, "disco_usado_mb": 0.0, "disco_libre_mb": 0.0, "disco_pct": 0.0}
    if db_path and os.path.exists(db_path):
        try:
            sz = os.path.getsize(db_path)
            result["db_size_kb"] = round(sz / 1024, 2); result["db_size_mb"] = round(sz / 1024 / 1024, 3)
        except Exception: pass
        # Nº de índices reales de la BD
        try:
            import sqlite3
            con = sqlite3.connect(db_path)
            result["num_indexes"] = con.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
            con.close()
        except Exception: pass

    # Medir el almacenamiento del directorio donde vive la BD (NO '/', que en
    # Termux/Android es una partición de sistema que aparece llena al 100%).
    medir_dir = os.path.dirname(db_path) if db_path else os.getcwd()
    if not medir_dir or not os.path.exists(medir_dir):
        medir_dir = os.path.expanduser("~") or "."

    if HAS_PSUTIL:
        try:
            disk = psutil.disk_usage(medir_dir)
            result["disco_total_mb"] = round(disk.total / 1024 / 1024, 2)
            result["disco_usado_mb"] = round(disk.used / 1024 / 1024, 2)
            result["disco_libre_mb"] = round(disk.free / 1024 / 1024, 2); result["disco_pct"] = disk.percent
        except Exception: pass
    else:
        try:
            stat = os.statvfs(medir_dir); total = stat.f_blocks * stat.f_frsize; free = stat.f_bavail * stat.f_frsize
            used = total - free
            result["disco_total_mb"] = round(total / 1024 / 1024, 2)
            result["disco_usado_mb"] = round(used / 1024 / 1024, 2)
            result["disco_libre_mb"] = round(free / 1024 / 1024, 2)
            result["disco_pct"] = round(used / total * 100, 1) if total else 0
        except Exception: pass
    return result


def _inventario_formulas(db_path):
    result = {"total_productos": 0, "total_unidades": 0, "valor_venta_total": 0.0,
              "valor_costo_total": 0.0, "margen_bruto_total": 0.0, "margen_bruto_pct": 0.0,
              "ganancia_potencial": 0.0, "productos_sin_stock": 0, "productos_precio_invalido": 0,
              "productos_sin_precio": 0, "categorias": [], "top5_valor": [],
              "formula_rentabilidad": "N/A", "formula_cobertura": "N/A", "error": None}
    if not db_path or not os.path.exists(db_path):
        result["error"] = "BD no encontrada: " + str(db_path); return result
    try:
        conn = sqlite3.connect(db_path, timeout=5); conn.row_factory = sqlite3.Row; cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total, COALESCE(SUM(stock_actual),0) as unidades, "
            "COALESCE(SUM(precio_venta*COALESCE(stock_actual,0)),0) as val_venta, "
            "COALESCE(SUM(COALESCE(precio_compra,0)*COALESCE(stock_actual,0)),0) as val_costo, "
            "COUNT(CASE WHEN COALESCE(stock_actual,0)=0 THEN 1 END) as sin_stock, "
            "COUNT(CASE WHEN precio_venta<COALESCE(precio_compra,0) THEN 1 END) as precio_invalido, "
            "COUNT(CASE WHEN precio_venta IS NULL OR precio_venta=0 THEN 1 END) as sin_precio "
            "FROM inventario_general")
        row = cur.fetchone()
        if row:
            result["total_productos"]=row["total"] or 0; result["total_unidades"]=row["unidades"] or 0
            result["valor_venta_total"]=round(float(row["val_venta"] or 0),2)
            result["valor_costo_total"]=round(float(row["val_costo"] or 0),2)
            result["productos_sin_stock"]=row["sin_stock"] or 0
            result["productos_precio_invalido"]=row["precio_invalido"] or 0
            result["productos_sin_precio"]=row["sin_precio"] or 0
        vv=result["valor_venta_total"]; vc=result["valor_costo_total"]
        if vv > 0:
            margen=vv-vc; result["margen_bruto_total"]=round(margen,2)
            result["margen_bruto_pct"]=round((margen/vv)*100,1); result["ganancia_potencial"]=round(margen,2)
            result["formula_rentabilidad"]="({} - {}) / {} x 100 = {}%".format(vv,vc,vv,result["margen_bruto_pct"])
        tot=result["total_productos"]; sin=result["productos_sin_stock"]
        if tot > 0:
            pct=round(((tot-sin)/tot)*100,1)
            result["formula_cobertura"]="({} - {}) / {} x 100 = {}% con stock".format(tot,sin,tot,pct)
        try:
            cur.execute("SELECT COALESCE(categoria,'General') as cat, COUNT(*) as qty, "
                "COALESCE(SUM(stock_actual),0) as units, "
                "COALESCE(SUM(precio_venta*COALESCE(stock_actual,0)),0) as valor "
                "FROM inventario_general GROUP BY cat ORDER BY valor DESC LIMIT 8")
            result["categorias"]=[{"nombre":r["cat"],"productos":r["qty"],"unidades":r["units"],
                "valor":round(float(r["valor"]),2)} for r in cur.fetchall()]
        except Exception: pass
        try:
            cur.execute("SELECT nombre, precio_venta, COALESCE(stock_actual,0) as cantidad, "
                "precio_venta*COALESCE(stock_actual,0) as valor_total "
                "FROM inventario_general ORDER BY valor_total DESC LIMIT 5")
            result["top5_valor"]=[{"nombre":r["nombre"],"precio":round(float(r["precio_venta"] or 0),2),
                "cantidad":r["cantidad"],"valor_total":round(float(r["valor_total"] or 0),2)} for r in cur.fetchall()]
        except Exception: pass
        conn.close()
    except sqlite3.OperationalError as e: result["error"] = "OperationalError: " + str(e)
    except Exception as e: result["error"] = str(e)
    return result


def _dev_only(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            from flask import session
            usuario = session.get("usuario", {})
            rol = usuario.get("rol","") if isinstance(usuario,dict) else str(session.get("rol",""))
            if rol not in ("desarrollador","administrador"):
                return jsonify({"ok":False,"error":"Acceso restringido"}), 403
        except Exception: pass
        return func(*args, **kwargs)
    return decorated


def _tablas_info(db_path):
    """Lista las tablas reales de la BD con su número de filas."""
    result = {"tablas": [], "total_tablas": 0, "total_filas": 0, "error": None}
    if not db_path or not os.path.exists(db_path):
        result["error"] = "BD no encontrada"
        return result
    try:
        import sqlite3
        con = sqlite3.connect(db_path)
        nombres = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in nombres:
            try:
                n = con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
            except Exception:
                n = -1
            result["tablas"].append({"nombre": t, "filas": n})
            if n > 0:
                result["total_filas"] += n
        result["total_tablas"] = len(nombres)
        con.close()
    except Exception as e:
        result["error"] = str(e)
    return result


def get_system_metrics():
    # Métricas de SISTEMA: RAM, almacenamiento y tablas de la BD.
    # (Se quitó "inventario": esas son métricas de negocio, no de sistema, y
    #  ya se ven en el panel de Inventario/Dashboard.)
    db_path = _get_db_path()
    return {
        "ram": _ram_info(),
        "storage": _storage_info(db_path),
        "tablas": _tablas_info(db_path),
        "db_path": db_path,
    }
