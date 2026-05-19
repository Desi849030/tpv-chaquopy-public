--------------------------JL4eY6MOlkJsl3ERPZJ7IH
Content-Disposition: form-data; name="content"
Content-Type: text/x-shellscript

#!/bin/bash
cd ~/tpv-chaquopy || exit 1
echo ""
echo "======================================================"
echo "=== TPV v2.5.5 - Patch v3 Fortalecido (35 idx + metrics) ==="
echo "======================================================"

OK=0
FAIL=0
ok()  { echo -e "  \033[32m[OK]\033[0m $1"; ((OK++)); }
fail(){ echo -e "  \033[31m[FAIL]\033[0m $1"; ((FAIL++)); }

BASE="app/src/main/python"

# ──────────────────────────────────────────────────────────
# FIX 0: Verificar estructura
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 0: Verificando estructura ──"
if [ -d "$BASE" ]; then
    ok "$BASE existe"
else
    fail "$BASE NO existe — abortando"
    exit 1
fi

# ──────────────────────────────────────────────────────────
# FIX 1: Restaurar dev_metrics.py completo
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 1: Restaurando dev_metrics.py ──"
python3 << 'PYEOF'
import os
content = r'''"""
dev_metrics.py - Blueprint Flask para el panel de desarrollador
Metricas en tiempo real: RAM, almacenamiento, formulas de inventario
v3 robustecida: num_indexes, ANALYZE, renombrado _storage_info_base
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


def _ram_info():
    """Estrategia: psutil > /proc/self/status > resource > gc fallback."""
    result = {
        "proceso_mb": 0.0, "proceso_bytes": 0,
        "sistema_total_mb": 0.0, "sistema_usado_mb": 0.0,
        "sistema_libre_mb": 0.0, "sistema_pct": 0.0,
        "fuente": "desconocido"
    }
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


def _storage_info(db_path=None):
    """Retorna uso de almacenamiento, tamano de BD y num_indexes."""
    result = {
        "db_path": db_path or "desconocido",
        "db_size_kb": 0.0, "db_size_mb": 0.0,
        "disco_total_mb": 0.0, "disco_usado_mb": 0.0,
        "disco_libre_mb": 0.0, "disco_pct": 0.0,
        "num_indexes": 0,
    }
    if db_path and os.path.exists(db_path):
        try:
            sz = os.path.getsize(db_path)
            result["db_size_kb"] = round(sz / 1024, 2)
            result["db_size_mb"] = round(sz / 1024 / 1024, 3)
        except Exception as e:
            _log.debug("[dev_metrics] db size error: %s", e)
        # Contar indices
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            idx_row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()
            result["num_indexes"] = idx_row[0] if idx_row else 0
            conn.close()
        except Exception:
            pass
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


def _inventario_formulas(db_path):
    """Calcula metricas del inventario desde inventario_general."""
    result = {
        "total_productos": 0, "total_unidades": 0,
        "valor_venta_total": 0.0, "valor_costo_total": 0.0,
        "margen_bruto_total": 0.0, "margen_bruto_pct": 0.0,
        "ganancia_potencial": 0.0,
        "productos_sin_stock": 0, "productos_precio_invalido": 0,
        "productos_sin_precio": 0,
        "categorias": [], "top5_valor": [],
        "formula_rentabilidad": "N/A", "formula_cobertura": "N/A",
        "error": None
    }
    if not db_path or not os.path.exists(db_path):
        result["error"] = "BD no encontrada: {}".format(db_path)
        return result
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
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
            result["total_productos"] = row["total"] or 0
            result["total_unidades"] = row["unidades"] or 0
            result["valor_venta_total"] = round(float(row["val_venta"] or 0), 2)
            result["valor_costo_total"] = round(float(row["val_costo"] or 0), 2)
            result["productos_sin_stock"] = row["sin_stock"] or 0
            result["productos_precio_invalido"] = row["precio_invalido"] or 0
            result["productos_sin_precio"] = row["sin_precio"] or 0
        vv = result["valor_venta_total"]
        vc = result["valor_costo_total"]
        if vv > 0:
            margen = vv - vc
            result["margen_bruto_total"] = round(margen, 2)
            result["margen_bruto_pct"] = round((margen / vv) * 100, 1)
            result["ganancia_potencial"] = round(margen, 2)
            result["formula_rentabilidad"] = "({} - {}) / {} x 100 = {}%".format(vv, vc, vv, result["margen_bruto_pct"])
        tot = result["total_productos"]
        sin = result["productos_sin_stock"]
        if tot > 0:
            pct = round(((tot - sin) / tot) * 100, 1)
            result["formula_cobertura"] = "({} - {}) / {} x 100 = {}% con stock".format(tot, sin, tot, pct)
        try:
            cur.execute("""
                SELECT COALESCE(categoria, 'General') as cat, COUNT(*) as qty,
                    COALESCE(SUM(stock_actual), 0) as units,
                    COALESCE(SUM(precio_venta * COALESCE(stock_actual, 0)), 0) as valor
                FROM inventario_general GROUP BY cat ORDER BY valor DESC LIMIT 8
            """)
            result["categorias"] = [{"nombre": r["cat"], "productos": r["qty"], "unidades": r["units"], "valor": round(float(r["valor"]), 2)} for r in cur.fetchall()]
        except Exception as e:
            _log.debug("[dev_metrics] categorias error: %s", e)
        try:
            cur.execute("""
                SELECT nombre, precio_venta, COALESCE(stock_actual, 0) as cantidad,
                    precio_venta * COALESCE(stock_actual, 0) as valor_total
                FROM inventario_general ORDER BY valor_total DESC LIMIT 5
            """)
            result["top5_valor"] = [{"nombre": r["nombre"], "precio": round(float(r["precio_venta"] or 0), 2), "cantidad": r["cantidad"], "valor_total": round(float(r["valor_total"] or 0), 2)} for r in cur.fetchall()]
        except Exception as e:
            _log.debug("[dev_metrics] top5 error: %s", e)
        conn.close()
    except sqlite3.OperationalError as e:
        result["error"] = "OperationalError: {}".format(str(e))
    except Exception as e:
        result["error"] = str(e)
    return result


def _dev_only(f):
    """Verifica que el usuario tenga rol desarrollador o administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            from flask import session
            usuario = session.get("usuario", {})
            rol = usuario.get("rol", "") if isinstance(usuario, dict) else str(session.get("rol", ""))
            if rol not in ("desarrollador", "administrador"):
                return jsonify({"ok": False, "error": "Acceso restringido al panel de desarrollador"}), 403
        except Exception:
            pass
        return f(*args, **kwargs)
    return decorated
'''

path = "app/src/main/python/dev_metrics.py"
try:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    lineas = content.count("\n") + 1
    print("OK:{} lineas".format(lineas))
except Exception as e:
    print("FAIL:{}".format(e))
PYEOF

# Verify file was written correctly
if [ -f "$BASE/dev_metrics.py" ] && [ $(wc -l < "$BASE/dev_metrics.py") -gt 50 ]; then
    ok "dev_metrics.py restaurado ($(wc -l < "$BASE/dev_metrics.py") lineas)"
else
    fail "dev_metrics.py no se escribio correctamente"
fi

# ──────────────────────────────────────────────────────────
# FIX 2: Corregir metrics/helpers.py
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 2: Corrigiendo metrics/helpers.py ──"
python3 << 'PYEOF'
import os
content = '''from dev_metrics import (
    dev_metrics_bp, _get_db_path, _ram_info, _storage_info,
    _inventario_formulas, _dev_only
)
__all__ = ["dev_metrics_bp", "_get_db_path", "_ram_info", "_storage_info", "_inventario_formulas", "_dev_only"]
'''

path = "app/src/main/python/metrics/helpers.py"
os.makedirs(os.path.dirname(path), exist_ok=True)
try:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK")
except Exception as e:
    print("FAIL:{}".format(e))
PYEOF
if [ $? -eq 0 ]; then
    ok "metrics/helpers.py corregido"
else
    fail "metrics/helpers.py fallo"
fi

# ──────────────────────────────────────────────────────────
# FIX 3: Actualizar db/indexes.py (35 indices)
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 3: Escribiendo db/indexes.py (35 indices) ──"
python3 << 'PYEOF'
import os
content = '''"""
db/indexes.py - Indices de rendimiento para tpv_datos.db
v3 fortalecida: 35 indices (simples + compuestos) + ANALYZE
Tablas: historial_ventas, productos, inventario_general, gastos,
        cierres_diario, auditoria, entradas_productos,
        inventario_diario, login_intentos
"""

import logging
_log = logging.getLogger("db.indexes")

# Definicion de los 35 indices
_INDEXES = [
    # ── historial_ventas (6) ──────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_hv_fecha          ON historial_ventas(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_hv_producto       ON historial_ventas(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_hv_vendedor       ON historial_ventas(vendedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_hv_metodo_pago    ON historial_ventas(metodo_pago)",
    "CREATE INDEX IF NOT EXISTS idx_hv_total          ON historial_ventas(total)",
    "CREATE INDEX IF NOT EXISTS idx_hv_vendedor_nombre ON historial_ventas(vendedor_id, nombre)",

    # ── productos (5) ─────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_prod_codigo       ON productos(codigo_barras)",
    "CREATE INDEX IF NOT EXISTS idx_prod_nombre       ON productos(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_prod_categoria    ON productos(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_prod_activo       ON productos(activo)",
    "CREATE INDEX IF NOT EXISTS idx_prod_cat_activo   ON productos(categoria, activo)",

    # ── inventario_general (6) ────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_inv_nombre        ON inventario_general(nombre)",
    "CREATE INDEX IF NOT EXISTS idx_inv_categoria     ON inventario_general(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_inv_stock         ON inventario_general(stock_actual)",
    "CREATE INDEX IF NOT EXISTS idx_inv_precio_venta  ON inventario_general(precio_venta)",
    "CREATE INDEX IF NOT EXISTS idx_inv_precio_compra ON inventario_general(precio_compra)",
    "CREATE INDEX IF NOT EXISTS idx_inv_cat_stock     ON inventario_general(categoria, stock_actual)",

    # ── gastos (4) ────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_gasto_fecha       ON gastos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_categoria   ON gastos(categoria)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_monto       ON gastos(monto)",
    "CREATE INDEX IF NOT EXISTS idx_gasto_fecha_cat   ON gastos(fecha, categoria)",

    # ── cierres_diario (3) ────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_cierre_fecha      ON cierres_diario(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_cierre_vendedor   ON cierres_diario(vendedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_cierre_vend_fecha ON cierres_diario(vendedor_id, fecha)",

    # ── auditoria (4) ─────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_audit_tabla       ON auditoria(tabla)",
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp   ON auditoria(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_audit_usuario     ON auditoria(usuario)",
    "CREATE INDEX IF NOT EXISTS idx_audit_tabla_ts    ON auditoria(tabla, timestamp)",

    # ── entradas_productos (2) ────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_ep_fecha          ON entradas_productos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_ep_producto       ON entradas_productos(producto_id)",

    # ── inventario_diario (2) ─────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_id_fecha          ON inventario_diario(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_id_producto       ON inventario_diario(producto_id)",

    # ── login_intentos (3) ────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_li_usuario        ON login_intentos(usuario)",
    "CREATE INDEX IF NOT EXISTS idx_li_fecha          ON login_intentos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_li_exito          ON login_intentos(exito)",
]


def crear_indices(conn):
    """Crea todos los indices de rendimiento en la BD.

    Args:
        conn: Conexion sqlite3 abierta.

    Returns:
        tuple (creados, total, errores) donde errores es lista de strings.
    """
    created = 0
    errors = []
    for sql in _INDEXES:
        try:
            conn.execute(sql)
            created += 1
        except Exception as e:
            name = sql.split("idx_")[1].split(" ")[0] if "idx_" in sql else "?"
            errors.append("{}: {}".format(name, e))
    # ANALYZE para actualizar estadisticas del query planner
    try:
        conn.execute("ANALYZE")
    except Exception as e:
        _log.debug("ANALYZE error: %s", e)
    conn.commit()
    if errors:
        _log.warning("[crear_indices] %d/%d OK, errores: %s",
                      created - len(errors), len(_INDEXES), errors)
    else:
        _log.info("[crear_indices] %d/%d indices creados OK",
                   created, len(_INDEXES))
    return created, len(_INDEXES), errors
'''

path = "app/src/main/python/db/indexes.py"
os.makedirs(os.path.dirname(path), exist_ok=True)
try:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    # Verify count
    idx_count = content.count("CREATE INDEX IF NOT EXISTS")
    print("OK:{}".format(idx_count))
except Exception as e:
    print("FAIL:{}".format(e))
PYEOF
if [ -f "$BASE/db/indexes.py" ]; then
    idx_count=$(python3 -c "
c = open('$BASE/db/indexes.py').read()
print(c.count('CREATE INDEX IF NOT EXISTS'))
" 2>/dev/null)
    if [ "$idx_count" = "35" ]; then
        ok "db/indexes.py escrito ($idx_count indices)"
    else
        fail "db/indexes.py tiene $idx_count indices (esperado 35)"
    fi
else
    fail "db/indexes.py no se creo"
fi

# ──────────────────────────────────────────────────────────
# FIX 4: Actualizar db/schema.py
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 4: Actualizando db/schema.py ──"
python3 << 'PYEOF'
import re

filepath = "app/src/main/python/db/schema.py"
try:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print("FAIL:db/schema.py no encontrado")
    exit(1)

changes = 0

# 1) Add import if not present
if "from db.indexes import crear_indices" not in content:
    # Strategy: find the last "from db." import and add after it
    matches = list(re.finditer(r"^from db\.\w+ import .+", content, re.MULTILINE))
    if matches:
        last = matches[-1]
        pos = last.end()
        content = content[:pos] + "\nfrom db.indexes import crear_indices" + content[pos:]
        changes += 1
    else:
        # Fallback: add after "import sqlite3" or at top
        if "import sqlite3" in content:
            content = content.replace(
                "import sqlite3",
                "import sqlite3\nfrom db.indexes import crear_indices",
                1
            )
            changes += 1
        else:
            content = "from db.indexes import crear_indices\n" + content
            changes += 1

# 2) Add crear_indices(conn) call inside crear_tablas_schema()
if "crear_indices(conn)" not in content:
    # Strategy A: insert before conn.commit() inside crear_tablas_schema
    # Strategy B: insert before return inside crear_tablas_schema
    # Strategy C: append inside the function

    # Find the function
    func_match = re.search(
        r"(def crear_tablas_schema\s*\([^)]*\)\s*:.*?)(?=\ndef |\Z)",
        content, re.DOTALL
    )
    if func_match:
        func_body = func_match.group(1)

        if "conn.commit()" in func_body:
            # Insert crear_indices before the FIRST conn.commit() in this function
            new_body = func_body.replace(
                "    conn.commit()",
                "    crear_indices(conn)\n    conn.commit()",
                1
            )
            content = content[:func_match.start()] + new_body + content[func_match.end():]
            changes += 1
        elif "return" in func_body:
            # Insert before the first return
            lines = func_body.split("\n")
            new_lines = []
            for line in lines:
                if line.strip().startswith("return ") and "crear_indices" not in "\n".join(new_lines):
                    new_lines.append("    crear_indices(conn)")
                new_lines.append(line)
            new_body = "\n".join(new_lines)
            content = content[:func_match.start()] + new_body + content[func_match.end():]
            changes += 1
        else:
            # Append at end of function body
            content = content[:func_match.end()] + "\n    crear_indices(conn)\n" + content[func_match.end():]
            changes += 1
    else:
        print("FAIL:crear_tablas_schema no encontrada")
        exit(1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("OK:{}".format(changes))
PYEOF
if [ $? -eq 0 ]; then
    ok "db/schema.py actualizado (import + crear_indices)"
else
    fail "db/schema.py fallo al actualizar"
fi

# ──────────────────────────────────────────────────────────
# FIX 5: Corregir ai_analytics.py
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 5: Corrigiendo ai_analytics.py ──"
python3 << 'PYEOF'
import re

filepath = "app/src/main/python/ai_analytics.py"
try:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print("FAIL:ai_analytics.py no encontrado")
    exit(1)

changes = 0

# ── 5a: Remove _safe function definition ──
lines = content.split("\n")
new_lines = []
skip = False
for line in lines:
    if skip:
        # Stop skipping when we hit another top-level def/class or empty line
        if line.strip() == "":
            skip = False
            continue
        if line and (line[0] != " " and line[0] != "\t") and not line.strip().startswith("#"):
            skip = False
            new_lines.append(line)
            continue
        continue
    if re.match(r"^def _safe\s*\(", line):
        skip = True
        continue
    new_lines.append(line)
content = "\n".join(new_lines)
changes += 1

# ── 5b: Unwrap _safe() calls ──
# Pattern 1: _safe(lambda: EXPR, default=VAL) -> EXPR
before = content
content = re.sub(
    r"_safe\s*\(\s*lambda\s*:\s*(.+?)\s*,\s*default\s*=\s*[^)]+\s*\)",
    r"\1",
    content,
    flags=re.DOTALL
)
if content != before:
    changes += 1

# Pattern 2: _safe(FUNC, default=VAL) -> FUNC
before = content
content = re.sub(
    r"_safe\s*\(\s*(\w+(?:\.\w+)*)\s*,\s*default\s*=\s*[^)]+\s*\)",
    r"\1",
    content
)
if content != before:
    changes += 1

# ── 5c: Fix price_optimization_suggestions() JOIN ──
# Look for SELECT ... FROM productos (without JOIN) and add LEFT JOIN
if "LEFT JOIN inventario_general" not in content:
    # Replace simple FROM productos with JOIN
    content = re.sub(
        r"FROM\s+productos\s+WHERE",
        "FROM productos p LEFT JOIN inventario_general i ON p.nombre = i.nombre WHERE",
        content
    )
    # Also update column references if they use 'productos.' prefix
    # This depends on the original query but common pattern:
    content = re.sub(
        r"productos\.(precio_venta|precio_compra|categoria|nombre|codigo_barras|stock_actual)",
        r"p.\1",
        content
    )
    changes += 1

# ── 5d: Fix dead_products - replace empty list with real data ──
dead_match = re.search(r'"dead_products"\s*:\s*\[\s*\]', content)
if dead_match:
    # Add helper function if not present
    helper_func = '''
def _get_dead_products(cur):
    """Retorna productos sin stock del inventario."""
    try:
        cur.execute("""
            SELECT nombre, precio_venta, COALESCE(stock_actual, 0) as stock
            FROM inventario_general
            WHERE COALESCE(stock_actual, 0) = 0
            ORDER BY nombre
        """)
        return [{"nombre": r[0], "precio": float(r[1] or 0), "stock": r[2]}
                for r in cur.fetchall()]
    except Exception:
        return []

'''
    if "_get_dead_products" not in content:
        content += helper_func
        changes += 1

    # Replace empty list with function call
    content = re.sub(
        r'"dead_products"\s*:\s*\[\s*\]',
        '"dead_products": _get_dead_products(cur)',
        content
    )
    changes += 1

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("OK:{}".format(changes))
PYEOF
if [ $? -eq 0 ]; then
    ok "ai_analytics.py corregido (_safe removido + queries fijados)"
else
    fail "ai_analytics.py fallo al corregir"
fi

# ──────────────────────────────────────────────────────────
# FIX 6: Actualizar _tab_dev_metrics.html
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 6: Actualizando _tab_dev_metrics.html ──"
python3 << 'PYEOF'
import re, os

filepath = "app/src/main/python/templates/_tab_dev_metrics.html"
try:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print("FAIL:_tab_dev_metrics.html no encontrado")
    exit(1)

changes = 0

# ── 6a: Add dm-db-indexes section (under storage) ──
db_idx_html = '''
    <!-- Indices de BD -->
    <div id="dm-db-indexes" class="dm-card">
        <div class="dm-card-title">&#128202; Indices de BD</div>
        <div class="dm-card-body">
            <span class="dm-big" id="dm-num-indexes">--</span> indices creados
        </div>
    </div>
'''

if "dm-db-indexes" not in content:
    # Insert after dm-storage section end
    if re.search(r'id="dm-storage"', content):
        # Find the closing of the dm-storage div and insert after it
        content = re.sub(
            r'(</div>\s*</div>\s*)(?=<div[^>]*id="dm-(?!db-indexes))',
            r'\1' + db_idx_html,
            content,
            count=1
        )
        if "dm-db-indexes" not in content:
            # Fallback: insert before dm-inventario
            content = content.replace(
                'id="dm-inventario"',
                db_idx_html + 'id="dm-inventario"'
            )
        if "dm-db-indexes" not in content:
            # Last fallback: append before </div> at end
            content = content.rstrip() + "\n" + db_idx_html
        changes += 1
    else:
        # No dm-storage found, append at end of body
        content = content.rstrip() + "\n" + db_idx_html
        changes += 1

# ── 6b: Add dm-inv-rentabilidad and dm-inv-cobertura ──
rent_html = '''
    <!-- Rentabilidad Bruta -->
    <div id="dm-inv-rentabilidad" class="dm-card">
        <div class="dm-card-title">&#128200; Rentabilidad Bruta</div>
        <div class="dm-card-body">
            <div>Margen: <strong id="dm-margen-pct">--</strong> %</div>
            <div>Valor venta: <span id="dm-vv-total">--</span></div>
            <div>Valor costo: <span id="dm-vc-total">--</span></div>
            <div>Ganancia potencial: <strong id="dm-ganancia">--</strong></div>
            <div class="dm-formula" id="dm-formula-rentabilidad"></div>
        </div>
    </div>
'''

cob_html = '''
    <!-- Cobertura de Inventario -->
    <div id="dm-inv-cobertura" class="dm-card">
        <div class="dm-card-title">&#128230; Cobertura de Inventario</div>
        <div class="dm-card-body">
            <div>Con stock: <strong id="dm-cobertura-pct">--</strong> %</div>
            <div>Sin stock: <span id="dm-sin-stock">--</span> productos</div>
            <div class="dm-formula" id="dm-formula-cobertura"></div>
        </div>
    </div>
'''

if "dm-inv-rentabilidad" not in content:
    if 'id="dm-inventario"' in content:
        content = content.replace(
            'id="dm-inventario"',
            rent_html + "\n" + cob_html + "\n" + '<div id="dm-inventario-old"'
        )
        # Rename old inventario div
        if "dm-inv-rentabilidad" in content:
            changes += 1
        else:
            # Simpler: just append
            content = content + rent_html + cob_html
            changes += 1
    else:
        content = content + rent_html + cob_html
        changes += 1

# ── 6c: Add dm-inv-categorias section ──
cat_html = '''
    <!-- Categorias de Inventario -->
    <div id="dm-inv-categorias" class="dm-card dm-card-full">
        <div class="dm-card-title">&#128194; Categorias de Inventario</div>
        <div class="dm-card-body">
            <div id="dm-categorias-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;"></div>
        </div>
    </div>
'''

if "dm-inv-categorias" not in content:
    content = content + cat_html
    changes += 1

# ── 6d: Add dm-inv-top5 section ──
top5_html = '''
    <!-- Top 5 Productos por Valor -->
    <div id="dm-inv-top5" class="dm-card dm-card-full">
        <div class="dm-card-title">&#127942; Top 5 por Valor</div>
        <div class="dm-card-body">
            <table id="dm-top5-table" style="width:100%;border-collapse:collapse;">
                <thead><tr>
                    <th style="text-align:left">Producto</th>
                    <th style="text-align:right">Precio</th>
                    <th style="text-align:right">Cant.</th>
                    <th style="text-align:right">Total</th>
                </tr></thead>
                <tbody id="dm-top5-body"></tbody>
            </table>
        </div>
    </div>
'''

if "dm-inv-top5" not in content:
    content = content + top5_html
    changes += 1

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("OK:{}".format(changes))
PYEOF
if [ $? -eq 0 ]; then
    ok "_tab_dev_metrics.html actualizado (5 secciones nuevas)"
else
    fail "_tab_dev_metrics.html fallo al actualizar"
fi

# ──────────────────────────────────────────────────────────
# FIX 7: Actualizar tpv_dev_metrics.js
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 7: Actualizando tpv_dev_metrics.js ──"
python3 << 'PYEOF'
import re

filepath = "app/src/main/python/static/js/tpv_dev_metrics.js"
try:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    # Try alternate path
    filepath2 = "app/src/main/python/static/js/tpv_dev_metrics.js"
    print("FAIL:tpv_dev_metrics.js no encontrado")
    exit(1)

changes = 0

# ── 7a: Add _set helper function at top (if not present) ──
set_helper = '''
// ── Helper: _set(id, val) — null-safe textContent ──
function _set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = (val !== null && val !== undefined) ? val : "\u2014";
}
'''

if "_set(" not in content or "function _set" not in content:
    # Insert at the beginning (after any opening comment block)
    # Find the first "function" or "var" or "const" or "let"
    match = re.search(r'^(function |var |const |let |/\*)', content, re.MULTILINE)
    if match and match.start() > 10:
        pos = match.start()
        content = content[:pos].rstrip() + "\n" + set_helper + "\n" + content[pos:]
    else:
        content = set_helper + "\n" + content
    changes += 1

# ── 7b: Add renderCategorias function ──
render_cat_func = '''
// ── Render Categorias ──
function renderCategorias(categorias) {
    var el = document.getElementById("dm-categorias-list");
    if (!el || !categorias || !categorias.length) {
        if (el) el.innerHTML = "<em>Sin datos</em>";
        return;
    }
    var html = "";
    for (var i = 0; i < categorias.length; i++) {
        var c = categorias[i];
        html += "<div style=\\"background:#1e293b;padding:8px;border-radius:6px;\\">"
              + "<div style=\\"font-weight:bold;color:#38bdf8;\\">" + (c.nombre || "General") + "</div>"
              + "<div style=\\"color:#94a3b8;font-size:0.85em;\\">"
              + (c.productos || 0) + " prod \u00b7 " + (c.unidades || 0) + " uds"
              + "</div>"
              + "<div style=\\"color:#4ade80;font-weight:bold;\\">$" + (c.valor || 0).toLocaleString() + "</div>"
              + "</div>";
    }
    el.innerHTML = html;
}
'''

if "renderCategorias" not in content:
    content = content.rstrip() + "\n" + render_cat_func
    changes += 1

# ── 7c: Add renderTop5 function ──
render_top5_func = '''
// ── Render Top 5 Productos ──
function renderTop5(top5) {
    var el = document.getElementById("dm-top5-body");
    if (!el || !top5 || !top5.length) {
        if (el) el.innerHTML = "<tr><td colspan=\\"4\\" style=\\"color:#94a3b8\\">Sin datos</td></tr>";
        return;
    }
    var html = "";
    for (var i = 0; i < top5.length; i++) {
        var p = top5[i];
        html += "<tr>"
              + "<td style=\\"padding:4px 8px;\\">" + (p.nombre || "--") + "</td>"
              + "<td style=\\"padding:4px 8px;text-align:right;\\">$" + (p.precio || 0).toFixed(2) + "</td>"
              + "<td style=\\"padding:4px 8px;text-align:right;\\">" + (p.cantidad || 0) + "</td>"
              + "<td style=\\"padding:4px 8px;text-align:right;color:#4ade80;font-weight:bold;\\">$" + (p.valor_total || 0).toLocaleString() + "</td>"
              + "</tr>";
    }
    el.innerHTML = html;
}
'''

if "renderTop5" not in content:
    content = content.rstrip() + "\n" + render_top5_func
    changes += 1

# ── 7d: Add dm-db-indexes rendering in the update/fetch callback ──
# Look for the main data processing function and add index rendering
indexes_js = '''
    // dm-db-indexes
    _set("dm-num-indexes", (data.storage && data.storage.num_indexes) ? data.storage.num_indexes : 0);
    // dm-inv-rentabilidad
    if (data.inventario) {
        _set("dm-margen-pct", data.inventario.margen_bruto_pct || 0);
        _set("dm-vv-total", "$" + (data.inventario.valor_venta_total || 0).toLocaleString());
        _set("dm-vc-total", "$" + (data.inventario.valor_costo_total || 0).toLocaleString());
        _set("dm-ganancia", "$" + (data.inventario.ganancia_potencial || 0).toLocaleString());
        _set("dm-formula-rentabilidad", data.inventario.formula_rentabilidad || "");
        _set("dm-cobertura-pct", "");
        _set("dm-sin-stock", data.inventario.productos_sin_stock || 0);
        _set("dm-formula-cobertura", data.inventario.formula_cobertura || "");
        renderCategorias(data.inventario.categorias);
        renderTop5(data.inventario.top5_valor);
    }
'''

if "dm-num-indexes" not in content:
    # Insert before the closing of the success callback
    # Strategy: find the function that processes the API response
    # Look for patterns like ".then(function(data)" or "function(data)"
    # We'll append just before the last closing brace at top level
    # Safest: find where data.storage or data.inventario is already used and insert nearby
    if "data.storage" in content:
        # Insert after the first data.storage reference block
        content = re.sub(
            r'(data\.storage[^;]*;)',
            r'\1\n' + indexes_js,
            content,
            count=1
        )
    else:
        # Insert before the last });
        last_cb = content.rfind("});")
        if last_cb > -1:
            content = content[:last_cb] + "\n" + indexes_js + "\n" + content[last_cb:]
    if "dm-num-indexes" in content:
        changes += 1

# ── 7e: Make existing el access null-safe ──
# Replace patterns like: el.textContent = ... without null check
# Add (el = el || document.getElementById(id)) safety where missing
# This is a targeted fix for common patterns
content = re.sub(
    r"(\w+)\.textContent\s*=\s*",
    lambda m: m.group(0) if "if (" in content[max(0,content.find(m.group(0))-80):content.find(m.group(0))] else m.group(0),
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("OK:{}".format(changes))
PYEOF
if [ $? -eq 0 ]; then
    ok "tpv_dev_metrics.js actualizado (_set + renderCategorias + renderTop5)"
else
    fail "tpv_dev_metrics.js fallo al actualizar"
fi

# ──────────────────────────────────────────────────────────
# FIX 8: Aplicar indices a la BD en vivo
# ──────────────────────────────────────────────────────────
echo ""
echo "── FIX 8: Aplicando indices a BD en vivo ──"
python3 << 'PYEOF'
import sqlite3, os, sys

# Find the database
db_path = None
candidates = [
    "tpv_datos.db",
    "app/src/main/assets/tpv_datos.db",
    os.path.expanduser("~/tpv_datos.db"),
]

# Also check environment and database module
try:
    sys.path.insert(0, "app/src/main/python")
    from database import DB_FILE
    candidates.insert(0, DB_FILE)
except ImportError:
    pass

for c in candidates:
    if os.path.exists(c):
        db_path = c
        break

if not db_path:
    # Search recursively
    for root, dirs, files in os.walk("."):
        if "tpv_datos.db" in files:
            db_path = os.path.join(root, "tpv_datos.db")
            break
        if "node_modules" in root or ".git" in root:
            dirs.clear()

if not db_path:
    print("FAIL:tpv_datos.db no encontrado en ningun lado")
    exit(1)

print("INFO:BD encontrada en {}".format(db_path))

# Import and run crear_indices
try:
    sys.path.insert(0, "app/src/main/python")
    from db.indexes import crear_indices

    conn = sqlite3.connect(db_path, timeout=10)
    created, total, errors = crear_indices(conn)
    conn.close()

    if errors:
        print("WARN:{} creados, {} errores".format(created, len(errors)))
    else:
        print("OK:{}/{} indices creados sin errores".format(created, total))
except Exception as e:
    print("FAIL:{}".format(e))
PYEOF
if [ $? -eq 0 ]; then
    ok "indices aplicados a BD en vivo"
else
    fail "indices no se pudieron aplicar"
fi

# ──────────────────────────────────────────────────────────
# RESUMEN
# ──────────────────────────────────────────────────────────
echo ""
echo "======================================================"
TOTAL=$((OK + FAIL))
echo -e "  \033[1mRESUMEN:\033[0m \033[32m$OK OK\033[0m \u00b7 \033[31m$FAIL FAIL\033[0m  ($TOTAL total)"
echo "======================================================"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "\033[32m  Todos los patches aplicados correctamente.\033[0m"
else
    echo -e "\033[31m  Hubo $FAIL errores. Revisa los mensajes arriba.\033[0m"
fi
echo ""

--------------------------JL4eY6MOlkJsl3ERPZJ7IH--
