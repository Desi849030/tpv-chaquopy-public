from metrics.helpers import (
    dev_metrics_bp, _get_db_path, _ram_info, _storage_info,
    _inventario_formulas, _dev_only, jsonify, time
)


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
