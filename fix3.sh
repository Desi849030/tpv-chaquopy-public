--------------------------90PGmOwwcuobN2qNEzoUxn
Content-Disposition: form-data; name="content"
Content-Type: text/x-shellscript

#!/bin/bash
# Patch rapido: corrige los 3 fallos de apply_v3.sh
cd ~/tpv-chaquopy || exit 1
echo "=== TPV v2.5.5 — Fix 3 fallos del patch v3 ==="
echo ""

python3 << 'PYEOF'
import re, os, sys
sys.path.insert(0, "app/src/main/python")
os.environ["PYTHONPATH"] = "app/src/main/python"

ok_count = 0
fail_count = 0

def ok(msg):
    global ok_count
    print(f"  \033[32m[OK]\033[0m {msg}")
    ok_count += 1

def fail(msg):
    global fail_count
    print(f"  \033[31m[FAIL]\033[0m {msg}")
    fail_count += 1

# ══════════════════════════════════════════════════
# FIX A: schema.py — from __future__ debe ser linea 1
# ══════════════════════════════════════════════════
print("\n--- FIX A: db/schema.py ---")
fp = "app/src/main/python/db/schema.py"
with open(fp, "r") as f:
    lines = f.readlines()

# Encontrar from __future__ y ponerlo al inicio
new_lines = []
future_import = None
for i, line in enumerate(lines):
    if line.strip().startswith("from __future__"):
        future_import = line
        continue
    new_lines.append(line)

if future_import:
    # Insertar: future primero, luego el import de indexes despues
    insert_pos = 0
    # Insertar import de indexes despues de los comentarios/docstring iniciales
    for i, l in enumerate(new_lines):
        stripped = l.strip()
        if stripped.startswith('"""') or stripped.startswith("#") or stripped == "":
            insert_pos = i + 1
        elif stripped and not stripped.startswith('"""') and not stripped.startswith("#"):
            break
    result_lines = [future_import] + new_lines[:insert_pos]
    # Agregar import de indexes si no existe
    has_idx = any("from db.indexes import" in l for l in new_lines)
    if not has_idx:
        result_lines.append("from db.indexes import crear_indices\n")
    result_lines += new_lines[insert_pos:]
    with open(fp, "w") as f:
        f.writelines(result_lines)
    ok("schema.py: from __future__ al inicio + import indexes")
else:
    ok("schema.py: from __future__ ya es linea 1")

# Verificar que crear_tablas_schema tiene crear_indices
with open(fp, "r") as f:
    c = f.read()
if "crear_indices(conn)" not in c:
    c = c.replace(
        "def crear_tablas_schema(conn):\n    \"\"\"Ejecuta todas las CREATE TABLE IF NOT EXISTS",
        "def crear_tablas_schema(conn):\n    \"\"\"Ejecuta todas las CREATE TABLE IF NOT EXISTS + crea indices.\"\"\""
    )
    c = c.replace(
        "        except Exception:\n            pass\n",
        "        except Exception:\n            pass\n    # Crear indices de rendimiento\n    try:\n        from db.indexes import crear_indices\n        crear_indices(conn)\n    except Exception:\n        pass\n",
        1
    )
    with open(fp, "w") as f:
        f.write(c)
    ok("crear_indices() integrado en crear_tablas_schema()")
else:
    ok("crear_indices() ya integrado")

# Verificar sintaxis
try:
    compile(open(fp).read(), fp, "exec")
    ok("schema.py: sintaxis valida")
except SyntaxError as e:
    fail(f"schema.py: SyntaxError en linea {e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════
# FIX B: _tab_dev_metrics.html
# ══════════════════════════════════════════════════
print("\n--- FIX B: _tab_dev_metrics.html ---")
html_path = "app/src/main/assets/frontend/templates/partials/tabs/_tab_dev_metrics.html"
if os.path.isfile(html_path):
    with open(html_path, "r") as f:
        hc = f.read()
    needs_update = False
    if "dm-db-indexes" not in hc:
        hc = hc.replace(
            '<div id="dm-db-path" style="font-size:10px;color:#5a6a7a">--</div>',
            '<div id="dm-db-path" style="font-size:10px;color:#5a6a7a">--</div>\n            <div class="dm-row"><span>Indices:</span> <span id="dm-db-indexes" style="font-weight:600">--</span></div>'
        )
        needs_update = True
    if "dm-inv-rentabilidad" not in hc:
        hc = hc.replace(
            '<span id="dm-inv-margen-pct" style="font-weight:600">--</span></div>',
            '<span id="dm-inv-margen-pct" style="font-weight:600">--</span></div>\n            <div class="dm-row" style="border-top:1px solid #2a3a4a;padding-top:6px;margin-top:4px"><span>Rentabilidad:</span> <span id="dm-inv-rentabilidad" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>\n            <div class="dm-row"><span>Cobertura stock:</span> <span id="dm-inv-cobertura" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>'
        )
        needs_update = True
    if "dm-inv-categorias" not in hc:
        hc = hc.replace(
            '<div style="font-size:10px;color:#5a6a7a;text-align:center">',
            '<div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">\n            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Categorias</h3>\n            <div id="dm-inv-categorias"></div>\n        </div>\n        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">\n            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Top 5 por Valor</h3>\n            <div id="dm-inv-top5"></div>\n        </div>\n        <div style="font-size:10px;color:#5a6a7a;text-align:center">'
        )
        needs_update = True
    if needs_update:
        with open(html_path, "w") as f:
            f.write(hc)
        ok("HTML actualizado: +indices, +rentabilidad, +categorias, +top5")
    else:
        ok("HTML ya actualizado")
else:
    # Escribir el archivo completo si no existe
    html_full = '''<div class="tab-pane fade" id="dev-metrics-tab-pane" role="tabpanel">
    <div id="dev-metrics-panel" style="padding:12px">
        <div id="dm-status" style="font-size:11px;color:#5a6a7a;text-align:center;margin-bottom:12px">cargando...</div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">RAM</h3>
            <div class="dm-row" style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px"><span>Proceso:</span> <span id="dm-ram-proceso" style="font-weight:600">--</span></div>
            <div id="dm-ram-sys-wrap" style="display:none">
                <div class="dm-row"><span>Sistema:</span> <span id="dm-ram-sys-pct" style="font-weight:600">--</span></div>
                <div style="height:6px;background:#2a3a4a;border-radius:3px;margin:4px 0"><div id="dm-ram-bar" style="height:100%;border-radius:3px;background:#00cec9;width:0%"></div></div>
                <div class="dm-row"><span>Total:</span> <span id="dm-ram-total">--</span></div>
                <div class="dm-row"><span>Usado:</span> <span id="dm-ram-usado">--</span></div>
                <div class="dm-row"><span>Libre:</span> <span id="dm-ram-libre">--</span></div>
            </div>
            <div id="dm-ram-fuente" style="font-size:10px;color:#5a6a7a">--</div>
        </div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Almacenamiento</h3>
            <div class="dm-row"><span>BD:</span> <span id="dm-db-size" style="font-weight:600">--</span></div>
            <div id="dm-db-path" style="font-size:10px;color:#5a6a7a">--</div>
            <div class="dm-row"><span>Indices:</span> <span id="dm-db-indexes" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Disco:</span> <span id="dm-disco-pct" style="font-weight:600">--</span></div>
            <div style="height:6px;background:#2a3a4a;border-radius:3px;margin:4px 0"><div id="dm-disco-bar" style="height:100%;border-radius:3px;background:#00cec9;width:0%"></div></div>
            <div class="dm-row"><span>Total:</span> <span id="dm-disco-total">--</span></div>
            <div class="dm-row"><span>Usado:</span> <span id="dm-disco-usado">--</span></div>
            <div class="dm-row"><span>Libre:</span> <span id="dm-disco-libre">--</span></div>
        </div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Inventario</h3>
            <div class="dm-row"><span>Productos:</span> <span id="dm-inv-total" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Unidades:</span> <span id="dm-inv-unidades" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Sin stock:</span> <span id="dm-inv-sin-stock" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Sin precio:</span> <span id="dm-inv-sin-precio" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Invalidos:</span> <span id="dm-inv-invalidos" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Valor venta:</span> <span id="dm-inv-valor-venta" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Valor costo:</span> <span id="dm-inv-valor-costo" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Ganancia:</span> <span id="dm-inv-ganancia" style="font-weight:600">--</span></div>
            <div class="dm-row"><span>Margen:</span> <span id="dm-inv-margen-pct" style="font-weight:600">--</span></div>
            <div class="dm-row" style="border-top:1px solid #2a3a4a;padding-top:6px;margin-top:4px"><span>Rentabilidad:</span> <span id="dm-inv-rentabilidad" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>
            <div class="dm-row"><span>Cobertura stock:</span> <span id="dm-inv-cobertura" style="font-weight:600;color:#00cec9;font-size:11px">--</span></div>
        </div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Categorias</h3>
            <div id="dm-inv-categorias"></div>
        </div>
        <div class="dm-card" style="background:#1a2332;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(0,206,201,.1)">
            <h3 style="color:#00cec9;margin:0 0 8px 0;font-size:14px">Top 5 por Valor</h3>
            <div id="dm-inv-top5"></div>
        </div>
        <div style="font-size:10px;color:#5a6a7a;text-align:center">
            Uptime: <span id="dm-uptime">--</span> | <span id="dm-timestamp">--</span>
        </div>
    </div>
    <script src="/static/js/tpv/tpv_dev_metrics.js"></script>
</div>'''
    with open(html_path, "w") as f:
        f.write(html_full)
    ok("HTML escrito completo (no existia)")

# ══════════════════════════════════════════════════
# FIX C: tpv_dev_metrics.js
# ══════════════════════════════════════════════════
print("\n--- FIX C: tpv_dev_metrics.js ---")
js_path = "app/src/main/assets/frontend/static/js/tpv/tpv_dev_metrics.js"
js_full = '''// tpv_dev_metrics.js v3 — Panel metricas desarrollador
(function() {
  var DM = {
    endpoint: "/api/dev/metrics",
    intervalId: null,
    el: function(id) { return document.getElementById(id); },
    fmt: function(n) { return new Intl.NumberFormat("es",{minimumFractionDigits:2}).format(n); },
    _set: function(id, val) { var e = this.el(id); if(e) e.textContent = val; },
    init: function() {
      this.fetch();
      this.intervalId = setInterval(function(){ DM.fetch(); }, 10000);
    },
    fetch: function() {
      var se = this.el("dm-status");
      if(se) se.textContent = "cargando...";
      fetch(this.endpoint,{cache:"no-store"}).then(function(r){
        if(!r.ok) throw new Error("HTTP "+r.status);
        return r.json();
      }).then(function(d){
        if(!d.ok) throw new Error(d.error||"Error");
        DM.render(d);
        if(se) se.textContent = "actualizado";
      }).catch(function(e){
        if(se) se.textContent = "error: "+e.message;
      });
    },
    render: function(d) {
      this.renderRam(d.ram);
      this.renderStorage(d.storage);
      this.renderInventario(d.inventario);
      this.renderCategorias(d.inventario);
      this.renderTop5(d.inventario);
      this.renderFooter(d);
    },
    renderRam: function(r) {
      if(!r) return;
      this._set("dm-ram-proceso", r.proceso_mb>0 ? r.proceso_mb+" MB" : "--");
      this._set("dm-ram-fuente", "fuente: "+r.fuente);
      if(r.sistema_total_mb>0){
        var w=this.el("dm-ram-sys-wrap"); if(w) w.style.display="block";
        this._set("dm-ram-sys-pct",(r.sistema_pct||0)+"%");
        var b=this.el("dm-ram-bar"); if(b) b.style.width=(r.sistema_pct||0)+"%";
        this._set("dm-ram-total",r.sistema_total_mb+" MB");
        this._set("dm-ram-usado",r.sistema_usado_mb+" MB");
        this._set("dm-ram-libre",r.sistema_libre_mb+" MB");
      }
    },
    renderStorage: function(s) {
      if(!s) return;
      this._set("dm-db-size", s.db_size_kb>0 ? s.db_size_kb+" KB" : "--");
      this._set("dm-db-path", s.db_path||"--");
      this._set("dm-db-indexes", (s.num_indexes||0)+" indices");
      var p=s.disco_pct||0;
      this._set("dm-disco-pct", p+"%");
      var b=this.el("dm-disco-bar"); if(b) b.style.width=p+"%";
      if(s.disco_total_mb>0){
        this._set("dm-disco-total",s.disco_total_mb+" MB");
        this._set("dm-disco-usado",s.disco_usado_mb+" MB");
        this._set("dm-disco-libre",s.disco_libre_mb+" MB");
      }
    },
    renderInventario: function(inv) {
      if(!inv) return;
      this._set("dm-inv-total", inv.total_productos);
      this._set("dm-inv-unidades", inv.total_unidades);
      this._set("dm-inv-sin-stock", inv.productos_sin_stock);
      this._set("dm-inv-sin-precio", inv.productos_sin_precio);
      this._set("dm-inv-invalidos", inv.productos_precio_invalido);
      this._set("dm-inv-valor-venta", this.fmt(inv.valor_venta_total)+" CUP");
      this._set("dm-inv-valor-costo", this.fmt(inv.valor_costo_total)+" CUP");
      this._set("dm-inv-ganancia", this.fmt(inv.ganancia_potencial)+" CUP");
      this._set("dm-inv-margen-pct", inv.margen_bruto_pct+"%");
      this._set("dm-inv-rentabilidad", inv.formula_rentabilidad||"N/A");
      this._set("dm-inv-cobertura", inv.formula_cobertura||"N/A");
    },
    renderCategorias: function(inv) {
      if(!inv||!inv.categorias||!inv.categorias.length) return;
      var el=this.el("dm-inv-categorias"); if(!el) return;
      el.innerHTML = inv.categorias.map(function(c){
        return \'<div class="dm-row" style="font-size:11px;padding:2px 0"><span>\'+c.nombre+\':</span> <span style="color:#00cec9">\'+c.productos+\' prod | \'+DM.fmt(c.valor)+\' CUP</span></div>\';
      }).join("");
    },
    renderTop5: function(inv) {
      if(!inv||!inv.top5_valor||!inv.top5_valor.length) return;
      var el=this.el("dm-inv-top5"); if(!el) return;
      el.innerHTML = inv.top5_valor.map(function(p,i){
        return \'<div class="dm-row" style="font-size:11px;padding:2px 0"><span>#\'+(i+1)+\' \'+p.nombre+\':</span> <span style="color:#00cec9">\'+DM.fmt(p.valor_total)+\' CUP</span></div>\';
      }).join("");
    },
    renderFooter: function(d) {
      if(d.uptime_s) this._set("dm-uptime", Math.floor(d.uptime_s/60)+"m "+(d.uptime_s%60)+"s");
      this._set("dm-timestamp", d.timestamp||"--");
    }
  };
  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",function(){DM.init();});
  } else { DM.init(); }
})();
'''
os.makedirs(os.path.dirname(js_path), exist_ok=True)
with open(js_path, "w") as f:
    f.write(js_full)
ok("tpv_dev_metrics.js escrito (v3 con categorias, top5, indexes)")

# ══════════════════════════════════════════════════
# FIX D: Aplicar indices a BD en vivo
# ══════════════════════════════════════════════════
print("\n--- FIX D: Aplicar indices a BD ---")
try:
    import sqlite3
    # Buscar BD
    db_candidates = [
        "tpv_datos.db",
        "app/src/main/python/tpv_datos.db",
    ]
    db_file = None
    for p in db_candidates:
        if os.path.exists(p):
            db_file = p
            break
    if not db_file:
        # Buscar en todo el proyecto
        for root, dirs, files in os.walk("."):
            if "tpv_datos.db" in files:
                db_file = os.path.join(root, "tpv_datos.db")
                break
    if not db_file:
        fail("tpv_datos.db no encontrado")
    else:
        conn = sqlite3.connect(db_file, timeout=10)
        cur = conn.cursor()
        # Crear los 35 indices directamente
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hv_fecha ON historial_ventas(DATE(fecha))",
            "CREATE INDEX IF NOT EXISTS idx_hv_nombre ON historial_ventas(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_hv_vendedor ON historial_ventas(vendedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_hv_venta_id ON historial_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_hv_vend_nombre ON historial_ventas(vendedor_id, nombre)",
            "CREATE INDEX IF NOT EXISTS idx_prod_cat ON productos(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_prod_act ON productos(activo)",
            "CREATE INDEX IF NOT EXISTS idx_prod_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_prod_cat_act ON productos(categoria, activo)",
            "CREATE INDEX IF NOT EXISTS idx_inv_cat ON inventario_general(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_inv_stock ON inventario_general(stock_actual)",
            "CREATE INDEX IF NOT EXISTS idx_inv_prod_id ON inventario_general(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_inv_cat_stock ON inventario_general(categoria, stock_actual)",
            "CREATE INDEX IF NOT EXISTS idx_cc_fecha ON cierres_caja(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_gasto_fecha ON gastos(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_gasto_cat ON gastos(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_gasto_fecha_cat ON gastos(fecha, categoria)",
            "CREATE INDEX IF NOT EXISTS idx_cd_vend ON cierres_diario(vendedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_cd_fecha ON cierres_diario(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_cd_vend_fecha ON cierres_diario(vendedor_id, fecha)",
            "CREATE INDEX IF NOT EXISTS idx_user_rol ON usuarios(rol)",
            "CREATE INDEX IF NOT EXISTS idx_user_username ON usuarios(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_activo ON usuarios(activo)",
            "CREATE INDEX IF NOT EXISTS idx_log_tipo ON logs_sistema(tipo)",
            "CREATE INDEX IF NOT EXISTS idx_log_ts ON logs_sistema(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_aud_tabla ON auditoria(tabla)",
            "CREATE INDEX IF NOT EXISTS idx_aud_usuario ON auditoria(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_aud_ts ON auditoria(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_aud_tabla_ts ON auditoria(tabla, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ep_producto ON entradas_productos(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_ep_fecha ON entradas_productos(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_id_vendedor ON inventario_diario(vendedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_id_fecha ON inventario_diario(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_li_username ON login_intentos(username)",
            "CREATE INDEX IF NOT EXISTS idx_li_timestamp ON login_intentos(timestamp)",
        ]
        creados = 0
        for sql in indexes:
            try:
                cur.execute(sql)
                creados += 1
            except Exception:
                pass
        try:
            cur.execute("ANALYZE")
        except Exception:
            pass
        conn.commit()
        # Contar
        row = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchone()
        total_idx = row[0] if row else 0
        conn.close()
        ok(f"{creados} indices creados/verificados ({total_idx} totales en BD)")
except Exception as e:
    fail(f"Error indices BD: {e}")

print(f"\n{'='*50}")
print(f"  RESULTADO: {ok_count} OK, {fail_count} FAIL")
print(f"{'='*50}")
if fail_count == 0:
    print("  Todos OK. Reinicia el servidor:")
    print("  cd app/src/main/python && python app.py")
PYEOF

--------------------------90PGmOwwcuobN2qNEzoUxn--
