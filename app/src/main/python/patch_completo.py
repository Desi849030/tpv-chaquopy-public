#!/usr/bin/env python3
"""
PATCH COMPLETO TPV UltraSmart v2.5.5
=====================================
Aplica TODOS los cambios pendientes:
  1. metrics/helpers.py completo
  2. metrics/__init__.py (con fallback)
  3. tpv_storage.js (NUEVO - wrapper IndexedDB que reemplaza localStorage)
  4. Reemplaza localStorage por tpvStorage en 17 archivos JS + 1 HTML

Ejecutar en la raiz del repo:  python3 patch_completo.py
"""
import os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(BASE, 'app', 'src', 'main', 'python')
JS = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'static', 'js', 'tpv')
TPL = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'templates', 'partials')
METRICS = os.path.join(PY, 'metrics')

changed = 0
skipped = 0

def write_file(path, content):
    global changed
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    changed += 1
    print("  [CREADO] " + os.path.relpath(path, BASE))

print("=" * 60)
print("PATCH COMPLETO TPV UltraSmart v2.5.5")
print("=" * 60)

# === 1. metrics/helpers.py ===
print("\n[1/5] metrics/helpers.py")
os.makedirs(METRICS, exist_ok=True)
HELPERS = '''"""
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
        from database import DB_FILE
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
              "disco_total_mb": 0.0, "disco_usado_mb": 0.0, "disco_libre_mb": 0.0, "disco_pct": 0.0}
    if db_path and os.path.exists(db_path):
        try:
            sz = os.path.getsize(db_path)
            result["db_size_kb"] = round(sz / 1024, 2); result["db_size_mb"] = round(sz / 1024 / 1024, 3)
        except Exception: pass
    if HAS_PSUTIL:
        try:
            disk = psutil.disk_usage("/")
            result["disco_total_mb"] = round(disk.total / 1024 / 1024, 2)
            result["disco_usado_mb"] = round(disk.used / 1024 / 1024, 2)
            result["disco_libre_mb"] = round(disk.free / 1024 / 1024, 2); result["disco_pct"] = disk.percent
        except Exception: pass
    else:
        try:
            stat = os.statvfs("/"); total = stat.f_blocks * stat.f_frsize; free = stat.f_bavail * stat.f_frsize
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


def get_system_metrics():
    db_path = _get_db_path()
    return {"ram":_ram_info(),"storage":_storage_info(db_path),"inventario":_inventario_formulas(db_path),"db_path":db_path}
'''
write_file(os.path.join(METRICS, 'helpers.py'), HELPERS)

# === 2. metrics/__init__.py ===
print("\n[2/5] metrics/__init__.py")
write_file(os.path.join(METRICS, '__init__.py'),
    "try:\n    from .helpers import dev_metrics_bp\nexcept ImportError:\n    dev_metrics_bp = None\n\n"
    "try:\n    from .routes import *\nexcept ImportError:\n    pass\n")

# === 3. tpv_storage.js (NUEVO) ===
print("\n[3/5] tpv_storage.js (NUEVO)")
TPV_STORAGE = '''/**
 * tpv_storage.js - IndexedDB wrapper que reemplaza localStorage
 * Sin limite de 5MB, persistencia permanente, 100% offline.
 */
(function() {
    'use strict';
    var DB_NAME = 'tpv_keyvalue_store', DB_VERSION = 1, STORE_NAME = 'kv';
    var _db = null, _dbPromise = null, _cache = {};

    function _openDB() {
        if (_db) return Promise.resolve(_db);
        if (_dbPromise) return _dbPromise;
        _dbPromise = new Promise(function(resolve, reject) {
            var req = indexedDB.open(DB_NAME, DB_VERSION);
            req.onupgradeneeded = function(e) {
                var db = e.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME))
                    db.createObjectStore(STORE_NAME, { keyPath: 'key' });
            };
            req.onsuccess = function(e) { _db = e.target.result; resolve(_db); };
            req.onerror = function(e) { _dbPromise = null; reject(e.target.error); };
        });
        return _dbPromise;
    }

    function _loadAll() {
        return _openDB().then(function(db) {
            return new Promise(function(resolve) {
                var tx = db.transaction(STORE_NAME, 'readonly');
                var req = tx.objectStore(STORE_NAME).openCursor();
                req.onsuccess = function(e) {
                    var c = e.target.result;
                    if (c) { _cache[c.value.key] = c.value.value; c.continue(); }
                    else resolve();
                };
                req.onerror = function() { resolve(); };
            });
        }).catch(function() {});
    }

    function _put(key, val) {
        _openDB().then(function(db) {
            db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put({key:key, value:val});
        });
    }
    function _del(key) {
        _openDB().then(function(db) {
            db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(key);
        });
    }

    window.tpvStorage = {
        init: function() { return _loadAll(); },
        ready: false,
        getItem: function(k) { return (k in _cache) ? _cache[k] : null; },
        setItem: function(k, v) { _cache[k] = v; _put(k, v); },
        removeItem: function(k) { delete _cache[k]; _del(k); },
        getJSON: function(k) { var r = _cache[k]; if(r==null) return null; try{return JSON.parse(r);}catch(e){return null;} },
        setJSON: function(k, o) { var s = JSON.stringify(o); _cache[k] = s; _put(k, s); },
        keys: function(p) { var a = Object.keys(_cache); if(!p) return a; return a.filter(function(k){return k.indexOf(p)===0;}); },
        removeByPrefix: function(p) { this.keys(p).forEach(function(k){delete _cache[k];_del(k);}); },
        clear: function() { _cache = {}; _openDB().then(function(db){db.transaction(STORE_NAME,'readwrite').objectStore(STORE_NAME).clear();}); },
        migrateFromLocalStorage: function() {
            try { if(!window.localStorage) return; var m=0;
                for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k&&!(k in _cache)){_cache[k]=localStorage.getItem(k);_put(k,_cache[k]);m++;}}
                if(m>0) console.log('[tpvStorage] Migrados '+m+' keys desde localStorage');
            } catch(e){}
        }
    };

    tpvStorage.init().then(function() {
        tpvStorage.migrateFromLocalStorage();
        tpvStorage.ready = true;
        console.log('[tpvStorage] IndexedDB lista - ' + Object.keys(_cache).length + ' claves');
    });
})();
'''
write_file(os.path.join(JS, 'tpv_storage.js'), TPV_STORAGE)

# === 4. Reemplazar localStorage por tpvStorage ===
print("\n[4/5] Reemplazar localStorage -> tpvStorage en JS")

js_files = [
    'tpv_estado_ui.js', 'tpv_estado_backup.js', 'tpv_licencias_activacion.js',
    'tpv_boot_loader.js', 'tpv_config_central.js', 'tpv_traduccion_i18n.js',
    'catalog_cache.js', 'tpv_ui_enhancements.js',
    'tpv_auth_cliente.js', 'tpv_auth_main.js', 'tpv_sesion_polling.js',
    'tpv_gestion_importer_ia.js', 'tpv_gestion_exports2.js',
    'smart_excel_compat.js', 'smart_excel_importer.js',
    'tpv_tienda_init.js', 'tpv_ventas_registros.js',
]

for fname in js_files:
    fpath = os.path.join(JS, fname)
    if not os.path.exists(fpath):
        print("  [SKIP]   " + fname + " (no encontrado)"); continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'localStorage.' not in content:
        print("  [OK]     " + fname + " (sin localStorage)"); continue
    original = content
    content = re.sub(r'JSON\.parse\(localStorage\.getItem\(([^)]+)\)\)', r'tpvStorage.getJSON(\1)', content)
    content = re.sub(r'localStorage\.setItem\(([^,]+),\s*JSON\.stringify\(([^)]+)\)\)', r'tpvStorage.setJSON(\1, \2)', content)
    content = re.sub(r"Object\.keys\(localStorage\)\.filter\(function\(k\)\s*\{\s*return k\.indexOf\(([^)]+)\)\s*===\s*0;\s*\}\)", r'tpvStorage.keys(\1)', content)
    content = re.sub(r"Object\.keys\(localStorage\)\.filter\(function\(k\)\s*\{\s*return k\.startsWith\(([^)]+)\);\s*\}\)", r'tpvStorage.keys(\1)', content)
    content = re.sub(r"Object\.keys\(localStorage\)\.filter\(k\s*=>\s*k\.startsWith\(([^)]+)\)\)", r'tpvStorage.keys(\1)', content)
    content = re.sub(r"Object\.keys\(localStorage\)\.filter\(k\s*=>\s*k\.indexOf\(([^)]+)\)\s*===\s*0\)", r'tpvStorage.keys(\1)', content)
    content = content.replace('localStorage.setItem(', 'tpvStorage.setItem(')
    content = content.replace('localStorage.getItem(', 'tpvStorage.getItem(')
    content = content.replace('localStorage.removeItem(', 'tpvStorage.removeItem(')
    content = content.replace('Object.keys(localStorage)', 'tpvStorage.keys()')
    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        count = original.count('localStorage.') - content.count('localStorage.')
        changed += 1
        print("  [PATCH]  " + fname + " (" + str(count) + " reemplazos)")
    else:
        print("  [OK]     " + fname + " (sin cambios)")

# === 5. _scripts.html ===
print("\n[5/5] _scripts.html")
scripts_path = os.path.join(TPL, '_scripts.html')
if os.path.exists(scripts_path):
    with open(scripts_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    if 'tpv_storage.js' not in content:
        content = content.replace(
            '<script src="/static/js/tpv/tpv_estado_shim.js"></script>',
            '<script src="/static/js/tpv/tpv_estado_shim.js"></script>\n    <script src="/static/js/tpv/tpv_storage.js"></script>'
        )
    content = content.replace('localStorage.getItem(', 'tpvStorage.getItem(')
    if content != original:
        with open(scripts_path, 'w', encoding='utf-8') as f:
            f.write(content)
        changed += 1
        print("  [PATCH]  _scripts.html")
    else:
        print("  [OK]     _scripts.html (sin cambios)")
else:
    print("  [SKIP]   _scripts.html (no encontrado)")

print("\n" + "=" * 60)
print("RESUMEN: " + str(changed) + " archivos modificados/creados")
print("\nSiguiente paso:")
print("  cd ~/tpv-chaquopy")
print("  python3 patch_completo.py")
print("  rm -f tpv_datos.db")
print("  python3 test_simulacion_apk_full.py")
print("=" * 60)
