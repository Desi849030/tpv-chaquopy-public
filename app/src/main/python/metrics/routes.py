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

