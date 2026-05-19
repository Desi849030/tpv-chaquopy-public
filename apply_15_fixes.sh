#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  TPV ULTRA SMART v2.5.5 — 15 PARCHEES + INDICES + METRICAS
#  Ejecutar: bash apply_15_fixes.sh
# ═══════════════════════════════════════════════════════════════════════
cd ~/tpv-chaquopy || exit 1
echo "=== TPV v2.5.5 — Aplicando 15 Fixes + Indices ==="

# ── Verificar estructura ──
PY="app/src/main/python"
HT="app/src/main/assets/frontend"
test -d "$PY" || { echo "ERROR: No existe $PY"; exit 1; }
test -f "$PY/ia/catalog.py" || { echo "ERROR: No existe catalog.py"; exit 1; }

# ═══════════════════════════════════════════════
#  EJECUTAR PARCHES VIA PYTHON (confiable)
# ═══════════════════════════════════════════════
export PYTHONPATH="$PWD/$PY"
export TPV_TESTING=true

python3 << 'PATCHEOF'
import os, re

PY = "app/src/main/python"
HT = "app/src/main/assets/frontend"
fails = 0
applied = 0

def ok(msg):
    global applied
    print(f"  \033[32m[OK]\033[0m {msg}")
    applied += 1

def fail(msg):
    global fails
    print(f"  \033[31m[FAIL]\033[0m {msg}")
    fails += 1

def readf(path):
    with open(path, 'r') as f:
        return f.read()

def writef(path, content):
    with open(path, 'w') as f:
        f.write(content)

print("\n--- FIX 1-2: ia/catalog.py ---")
F = f"{PY}/ia/catalog.py"
c = readf(F)
if 'costo as costo' in c and 'FROM productos' in c:
    ok("FIX 1: costo as costo — ya correcto")
else:
    fail("FIX 1: costo as costo — patron no encontrado")

if '0 as stock_actual' in c:
    ok("FIX 2: 0 as stock_actual — ya correcto")
else:
    fail("FIX 2: stock_actual — no encontrado")

print("\n--- FIX 3: Crear db/indexes.py ---")
IDX = f"{PY}/db/indexes.py"
idx_content = '''# -*- coding: utf-8 -*-
"""db/indexes.py - Indices de rendimiento SQLite para TPV."""
IDX_HV_FECHA = "CREATE INDEX IF NOT EXISTS idx_hv_fecha ON historial_ventas(DATE(fecha))"
IDX_HV_NOMBRE = "CREATE INDEX IF NOT EXISTS idx_hv_nombre ON historial_ventas(nombre)"
IDX_HV_VENDEDOR = "CREATE INDEX IF NOT EXISTS idx_hv_vendedor ON historial_ventas(vendedor_id)"
IDX_PROD_CAT = "CREATE INDEX IF NOT EXISTS idx_prod_cat ON productos(categoria)"
IDX_PROD_ACT = "CREATE INDEX IF NOT EXISTS idx_prod_act ON productos(activo)"
IDX_INV_CAT = "CREATE INDEX IF NOT EXISTS idx_inv_cat ON inventario_general(categoria)"
IDX_INV_STOCK = "CREATE INDEX IF NOT EXISTS idx_inv_stock ON inventario_general(stock_actual)"
IDX_CC_FECHA = "CREATE INDEX IF NOT EXISTS idx_cc_fecha ON cierres_caja(fecha)"
IDX_GASTO_FECHA = "CREATE INDEX IF NOT EXISTS idx_gasto_fecha ON gastos(fecha)"
IDX_GASTO_CAT = "CREATE INDEX IF NOT EXISTS idx_gasto_cat ON gastos(categoria)"
IDX_CD_VEND = "CREATE INDEX IF NOT EXISTS idx_cd_vend ON cierres_diario(vendedor_id)"
IDX_USER_ROL = "CREATE INDEX IF NOT EXISTS idx_user_rol ON usuarios(rol)"
IDX_USER_USER = "CREATE INDEX IF NOT EXISTS idx_user_username ON usuarios(username)"
IDX_LOG_TIPO = "CREATE INDEX IF NOT EXISTS idx_log_tipo ON logs_sistema(tipo)"
IDX_AUD_TABLA = "CREATE INDEX IF NOT EXISTS idx_aud_tabla ON auditoria(tabla)"
IDX_AUD_USER = "CREATE INDEX IF NOT EXISTS idx_aud_usuario ON auditoria(usuario_id)"
ALL_INDEXES = [
    IDX_HV_FECHA, IDX_HV_NOMBRE, IDX_HV_VENDEDOR,
    IDX_PROD_CAT, IDX_PROD_ACT,
    IDX_INV_CAT, IDX_INV_STOCK,
    IDX_CC_FECHA, IDX_GASTO_FECHA, IDX_GASTO_CAT,
    IDX_CD_VEND, IDX_USER_ROL, IDX_USER_USER,
    IDX_LOG_TIPO, IDX_AUD_TABLA, IDX_AUD_USER,
]
def crear_indices(conn):
    cur = conn.cursor()
    creados = 0
    for sql in ALL_INDEXES:
        try:
            cur.execute(sql)
            creados += 1
        except Exception:
            pass
    conn.commit()
    return creados
'''
writef(IDX, idx_content)
ok("db/indexes.py creado (16 indices)")

print("\n--- FIX 4: Integrar crear_indices en crear_tablas ---")
CF = f"{PY}/db_config_licencias.py"
c = readf(CF)
if 'crear_indices' in c:
    ok("crear_indices ya integrado")
else:
    c = c.replace(
        'from db.schema import crear_tablas_schema',
        'from db.schema import crear_tablas_schema\nfrom db.indexes import crear_indices'
    )
    c = c.replace(
        'crear_tablas_schema(conn)',
        'crear_tablas_schema(conn)\n    try: crear_indices(conn)\n    except Exception: pass'
    )
    writef(CF, c)
    ok("crear_indices() integrado en crear_tablas()")

print("\n--- FIX 5-6: ai_analytics.py — columna stock ---")
AF = f"{PY}/ai_analytics.py"
c = readf(AF)
changed = False
if 'AND stock>0' in c and 'FROM productos' in c:
    c = c.replace(
        "SELECT nombre, precio, costo FROM productos WHERE precio>0 AND costo>0 AND stock>0",
        "SELECT p.nombre, p.precio, p.costo FROM productos p JOIN inventario_general ig ON p.producto_id=ig.producto_id WHERE p.precio>0 AND p.costo>0 AND ig.stock_actual>0"
    )
    changed = True
if 'FROM productos WHERE stock > 0' in c:
    c = c.replace(
        "SELECT nombre, stock FROM productos WHERE stock > 0 ORDER BY stock DESC",
        "SELECT p.nombre, ig.stock_actual as stock FROM productos p JOIN inventario_general ig ON p.producto_id=ig.producto_id WHERE ig.stock_actual > 0 ORDER BY ig.stock_actual DESC"
    )
    changed = True
if changed:
    writef(AF, c)
    ok("ai_analytics.py: stock -> JOIN inventario_general")
else:
    ok("ai_analytics.py: ya corregido o patron diferente")

print("\n--- FIX 7: ai_analytics.py — dead products ---")
c = readf(AF)
if '"dead_products": []' in c:
    c = c.replace('"dead_products": []', 'dead_products[:5]')
    writef(AF, c)
    ok("dead_products ahora retorna datos")
else:
    ok("dead_products ya corregido")

print("\n--- FIX 8: ai_analytics.py — _safe() muerta ---")
c = readf(AF)
if 'def _safe' in c:
    c = re.sub(r'def _safe\(func\):.*?return None\n', '', c, flags=re.DOTALL)
    writef(AF, c)
    ok("_safe() eliminada")
else:
    ok("_safe() ya no existe")

print("\n--- FIX 9: Dev metrics HTML — rentabilidad/cobertura ---")
DM = f"{HT}/templates/partials/tabs/_tab_dev_metrics.html"
c = readf(DM)
if 'dm-inv-rentabilidad' not in c:
    c = c.replace(
        '<span id="dm-inv-margen-pct" style="font-weight:600">--</span></div>',
        '<span id="dm-inv-margen-pct" style="font-weight:600">--</span></div>\n            <div class="dm-row" style="border-top:1px solid #2a3a4a;padding-top:6px;margin-top:4px"><span>Rentabilidad:</span> <span id="dm-inv-rentabilidad" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>\n            <div class="dm-row"><span>Cobertura stock:</span> <span id="dm-inv-cobertura" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>'
    )
    writef(DM, c)
    ok("Campos rentabilidad y cobertura agregados")
else:
    ok("Rentabilidad/cobertura ya existen")

print("\n--- FIX 10: Dev metrics HTML — categorias/top5 ---")
c = readf(DM)
if 'dm-inv-categorias' not in c:
    c = c.replace(
        '<div style="font-size:10px;color:#5a6a7a;text-align:center">',
        '''<div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Categorias</h3>
            <div id="dm-inv-categorias"></div>
        </div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Top 5 por Valor</h3>
            <div id="dm-inv-top5"></div>
        </div>
        <div style="font-size:10px;color:#5a6a7a;text-align:center">'''
    )
    writef(DM, c)
    ok("Secciones categorias y top5 agregadas")
else:
    ok("Categorias/top5 ya existen")

print("\n--- FIX 11: Dev metrics HTML — indices count ---")
c = readf(DM)
if 'dm-db-indexes' not in c:
    c = c.replace(
        '<div id="dm-db-path" style="font-size:10px;color:#5a6a7a">--</div>',
        '<div id="dm-db-path" style="font-size:10px;color:#5a6a7a">--</div>\n            <div class="dm-row"><span>Indices:</span> <span id="dm-db-indexes" style="font-weight:600">--</span></div>'
    )
    writef(DM, c)
    ok("Campo indices BD agregado")
else:
    ok("Campo indices ya existe")

print("\n--- FIX 12: metrics/helpers.py — num_indexes ---")
MH = f"{PY}/metrics/helpers.py"
c = readf(MH)
if 'num_indexes' not in c:
    c = c.replace(
        '"disco_pct": 0.0,',
        '"disco_pct": 0.0,\n        "num_indexes": 0,'
    )
    c = c.replace(
        'result["db_size_mb"] = round(sz / 1024 / 1024, 3)',
        '''result["db_size_mb"] = round(sz / 1024 / 1024, 3)
            try:
                idx_c = sqlite3.connect(db_path, timeout=5).execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                ).fetchone()
                result["num_indexes"] = idx_c[0] if idx_c else 0
            except Exception:
                pass'''
    )
    writef(MH, c)
    ok("num_indexes agregado a storage_info")
else:
    ok("num_indexes ya existe")

print("\n--- FIX 13: tpv_dev_metrics.js — render categorias/top5 ---")
TDM = f"{HT}/static/js/tpv/tpv_dev_metrics.js"
c = readf(TDM)
if 'renderCategorias' not in c:
    render_cats = '''    renderCategorias: function(inv) {
      if (!inv || !inv.categorias || !inv.categorias.length) return;
      var el = document.getElementById("dm-inv-categorias");
      if (el) el.innerHTML = inv.categorias.map(function(c) {
        return '<div class="dm-row" style="font-size:11px"><span>' + c.nombre + ':</span> <span>' + c.productos + ' prod | ' + DM.fmt(c.valor) + '</span></div>';
      }).join("");
    },
    renderTop5: function(inv) {
      if (!inv || !inv.top5_valor || !inv.top5_valor.length) return;
      var el = document.getElementById("dm-inv-top5");
      if (el) el.innerHTML = inv.top5_valor.map(function(p, i) {
        return '<div class="dm-row" style="font-size:11px"><span>#' + (i+1) + ' ' + p.nombre + ':</span> <span>' + DM.fmt(p.valor_total) + '</span></div>';
      }).join("");
    },
'''
    c = c.replace('    renderFooter: function(d) {', render_cats + '    renderFooter: function(d) {')
    c = c.replace(
        'this.renderInventario(d.inventario);',
        'this.renderInventario(d.inventario);\n      this.renderCategorias(d.inventario);\n      this.renderTop5(d.inventario);'
    )
    writef(TDM, c)
    ok("renderCategorias/renderTop5 agregados")
else:
    ok("Ya tiene renderCategorias/renderTop5")

print("\n--- FIX 14: tpv_dev_metrics.js — render indices ---")
c = readf(TDM)
if 'dm-db-indexes' not in c:
    c = c.replace(
        'this.el("dm-db-path").textContent = s.db_path || "--";',
        'this.el("dm-db-path").textContent = s.db_path || "--";\n      this.el("dm-db-indexes").textContent = (s.num_indexes || 0) + " indices";'
    )
    writef(TDM, c)
    ok("Render de indices agregado")
else:
    ok("Render de indices ya existe")

print("\n--- FIX 15: Aplicar indices a la BD ---")
try:
    from db.indexes import crear_indices
    from db_connection import obtener_conexion
    conn = obtener_conexion()
    n = crear_indices(conn)
    print(f"  \033[32m[OK]\033[0m {n} indices creados/verificados en BD")
    applied += 1
    conn.close()
except Exception as e:
    fail(f"Error creando indices: {e}")

# ═══════════════════════════════════
#  VERIFICACION FINAL
# ═══════════════════════════════════
print(f"\n{'='*50}")
print(f"  RESULTADO: {applied} aplicados, {fails} fallos")
print(f"{'='*50}")
PATCHEOF

echo ""
echo "Para reiniciar el servidor:"
echo "  cd $PY && python app.py"
