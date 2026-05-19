# metrics/__init__.py - v5 - Rutas directas sin dependencias circulares
import os, sys, json, time, sqlite3, subprocess, traceback

from flask import Blueprint, jsonify, request as req

dev_metrics_bp = Blueprint("dev_metrics", __name__)

DB_PATH = os.environ.get("TPV_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "tpv_database.db"))

def _get_meminfo():
    info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().replace(" kB", "").strip()
                    try:
                        info[key] = int(val)
                    except ValueError:
                        pass
    except Exception:
        pass
    return info

def _get_db_size():
    try:
        sz = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        return round(sz / 1024, 1)
    except Exception:
        return 0

def _get_disk():
    try:
        st = os.statvfs(os.path.dirname(DB_PATH))
        total_mb = round(st.f_blocks * st.f_frsize / 1048576, 1)
        free_mb = round(st.f_bavail * st.f_frsize / 1048576, 1)
        used_mb = round(total_mb - free_mb, 1)
        pct = round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0
        return {"disco_total_mb": total_mb, "disco_usado_mb": used_mb,
                "disco_libre_mb": free_mb, "disco_pct": pct}
    except Exception:
        return {"disco_total_mb": 0, "disco_usado_mb": 0,
                "disco_libre_mb": 0, "disco_pct": 0}

def _get_db_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='index'")
        idx = len(c.fetchall())
        c.execute("SELECT COUNT(*) FROM productos")
        tp = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(cantidad),0) FROM productos")
        tu = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM productos WHERE cantidad <= 0")
        ss = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(precio_venta*cantidad),0) FROM productos")
        vvt = round(c.fetchone()[0], 2)
        c.execute("SELECT COALESCE(SUM(precio_costo*cantidad),0) FROM productos")
        vct = round(c.fetchone()[0], 2)
        gp = round(vvt - vct, 2)
        mb = round((gp / vvt) * 100, 1) if vvt > 0 else 0
        c.execute("SELECT DISTINCT categoria FROM productos ORDER BY categoria")
        cats = [r[0] for r in c.fetchall() if r[0]]
        c.execute("SELECT nombre, ROUND(precio_venta*cantidad,2) FROM productos ORDER BY precio_venta*cantidad DESC LIMIT 5")
        t5 = [{"nombre": r[0], "valor": r[1]} for r in c.fetchall()]
        conn.close()
        return {"total_productos": tp, "total_unidades": tu,
                "productos_sin_stock": ss, "valor_venta_total": vvt,
                "valor_costo_total": vct, "ganancia_potencial": gp,
                "margen_bruto_pct": mb, "categorias": cats, "top5_valor": t5}
    except Exception as e:
        return {"error": str(e)}

def _get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            secs = float(f.read().split()[0])
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        return "%dh %dm" % (h, m)
    except Exception:
        return "N/A"

def _get_process_ram():
    try:
        pid = os.getpid()
        with open("/proc/%d/status" % pid, "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    return round(int(parts[1]) / 1024, 1)
    except Exception:
        pass
    return 0

def _ventas_hoy():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = time.strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM ventas WHERE fecha=?", (today,))
        r = c.fetchone()
        conn.close()
        return {"ventas_hoy": r[0], "ingresos_hoy": round(r[1], 2)}
    except Exception:
        return {"ventas_hoy": 0, "ingresos_hoy": 0}

@dev_metrics_bp.route("/api/dev/metrics/ram")
def api_ram():
    mi = _get_meminfo()
    total = mi.get("MemTotal", 0) / 1024
    avail = mi.get("MemAvailable", mi.get("MemFree", 0)) / 1024
    used = round(total - avail, 1)
    free = round(avail, 1)
    pct = round((used / total) * 100, 1) if total > 0 else 0
    return jsonify({
        "proceso_mb": _get_process_ram(),
        "fuente": "proc/meminfo",
        "sistema_pct": pct,
        "sistema_total_mb": round(total, 1),
        "sistema_usado_mb": used,
        "sistema_libre_mb": free
    })

@dev_metrics_bp.route("/api/dev/metrics/storage")
def api_storage():
    d = _get_disk()
    d["db_size_kb"] = _get_db_size()
    d["db_path"] = DB_PATH
    d["num_indexes"] = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        d["num_indexes"] = c.fetchone()[0]
        conn.close()
    except Exception:
        pass
    return jsonify(d)

@dev_metrics_bp.route("/api/dev/metrics/inventario")
def api_inventario():
    return jsonify(_get_db_stats())

@dev_metrics_bp.route("/api/dev/metrics/resumen")
def api_resumen():
    inv = _get_db_stats()
    vt = _ventas_hoy()
    return jsonify({
        "total_productos": inv.get("total_productos", 0),
        "ventas_hoy": vt.get("ventas_hoy", 0),
        "ingresos_hoy": vt.get("ingresos_hoy", 0)
    })

@dev_metrics_bp.route("/api/dev/metrics/all")
def api_all():
    mi = _get_meminfo()
    total = mi.get("MemTotal", 0) / 1024
    avail = mi.get("MemAvailable", mi.get("MemFree", 0)) / 1024
    used = round(total - avail, 1)
    free = round(avail, 1)
    pct = round((used / total) * 100, 1) if total > 0 else 0
    d = _get_disk()
    inv = _get_db_stats()
    vt = _ventas_hoy()
    return jsonify({
        "ram": {
            "proceso_mb": _get_process_ram(), "fuente": "proc/meminfo",
            "sistema_pct": pct, "sistema_total_mb": round(total, 1),
            "sistema_usado_mb": used, "sistema_libre_mb": free
        },
        "storage": {**d, "db_size_kb": _get_db_size(),
                    "db_path": DB_PATH, "uptime": _get_uptime()},
        "inventario": inv,
        "resumen": {"total_productos": inv.get("total_productos", 0),
                    "ventas_hoy": vt.get("ventas_hoy", 0),
                    "ingresos_hoy": vt.get("ingresos_hoy", 0)}
    })

@dev_metrics_bp.route("/api/ping")
def api_ping():
    return jsonify({"status": "ok", "ts": int(time.time())})
