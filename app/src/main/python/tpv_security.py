"""security.py — Seguridad server-side (no afecta offline)
Todas las validaciones son opcionales. El JS sigue funcionando
localmente para offline; el servidor valida cuando hay conexion."""
import hashlib, time, re, uuid, threading, json, base64
from functools import wraps
from datetime import datetime

# ══════════════════════════════════════════════════════════════
#  RATE LIMITING — memoria, sin dependencias
# ══════════════════════════════════════════════════════════════
_rl_store = {}
_rl_lock = threading.Lock()

def rate_limit(max_attempts=5, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            key = request.remote_addr or "unknown"
            now = time.time()
            with _rl_lock:
                if key not in _rl_store:
                    _rl_store[key] = []
                _rl_store[key] = [t for t in _rl_store[key] if now - t < window]
                if len(_rl_store[key]) >= max_attempts:
                    wait = int(window - (now - _rl_store[key][0]))
                    return jsonify({"error": f"Demasiados intentos. Espera {wait}s"}), 429
                _rl_store[key].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ══════════════════════════════════════════════════════════════
#  HASH DE CONTRASEÑAS (SHA-256+salt, sin bcrypt)
# ══════════════════════════════════════════════════════════════
def hash_password(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex[:16]
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${h}"

def verify_password(password, stored_hash):
    if not stored_hash or '$' not in stored_hash:
        return password == stored_hash
    salt, h = stored_hash.split('$', 1)
    return hash_password(password, salt) == stored_hash

def needs_hash_migration(stored_hash):
    return stored_hash is not None and '$' not in stored_hash and len(stored_hash) < 50

# ══════════════════════════════════════════════════════════════
#  SANITIZACION DE INPUT
# ══════════════════════════════════════════════════════════════
_XSS = re.compile(r'<script|javascript:|on\w+=|<iframe|<object|data:', re.IGNORECASE)
_SQLI_PATTERNS = ["';", "--", "/*", "*/", "xp_", "UNION ", "SELECT ", "INSERT ", "DELETE ", "UPDATE ", "DROP "]

def sanitize_string(val):
    if not isinstance(val, str): return val
    val = re.sub(r'<[^>]+>', '', val)
    val = _XSS.sub('', val)
    return val.strip()

def sanitize_data(data):
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(i) for i in data]
    elif isinstance(data, str):
        return sanitize_string(data)
    return data

def check_sql_injection(data):
    if isinstance(data, dict):
        return any(check_sql_injection(v) for v in data.values())
    elif isinstance(data, list):
        return any(check_sql_injection(i) for i in data)
    elif isinstance(data, str):
        d = data.upper()
        return any(p.upper() in d for p in _SQLI_PATTERNS)
    return False

# ══════════════════════════════════════════════════════════════
#  GENERACION DE IDS
# ══════════════════════════════════════════════════════════════
def generar_id(prefix="id"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

# ══════════════════════════════════════════════════════════════
#  CALCULO DE PRECIOS SERVER-SIDE
# ══════════════════════════════════════════════════════════════
def calcular_venta(items, descuento_pct=0, impuesto_pct=0):
    subtotal = sum(
        float(i.get("precio", 0)) * float(i.get("cantidad", 1))
        for i in items if isinstance(i, dict)
    )
    monto_desc = subtotal * (float(descuento_pct) / 100)
    sub_desc = subtotal - monto_desc
    monto_imp = sub_desc * (float(impuesto_pct) / 100)
    total = sub_desc + monto_imp
    return {
        "subtotal": round(subtotal, 2),
        "monto_descuento": round(monto_desc, 2),
        "subtotal_con_descuento": round(sub_desc, 2),
        "monto_impuesto": round(monto_imp, 2),
        "total": round(total, 2),
        "items_count": len(items)
    }

def validar_totales(data):
    items = data.get("items", [])
    desc = float(data.get("descuento_pct", 0))
    calc = calcular_venta(items, desc)
    total_cli = float(data.get("total", 0))
    if abs(total_cli - calc["total"]) > 0.01:
        return {"valido": False, "error": "Discrepancia en totales",
                "total_cliente": total_cli, "total_servidor": calc["total"],
                "diferencia": round(total_cli - calc["total"], 2)}
    return {"valido": True, "calculo": calc}

# ══════════════════════════════════════════════════════════════
#  VALIDACION DE STOCK
# ══════════════════════════════════════════════════════════════
def validar_stock(items, user_id=None):
    from database import obtener_conexion
    conn = obtener_conexion()
    sin_stock = []
    try:
        for item in items:
            pid = item.get("producto_id", "")
            cant = float(item.get("cantidad", 0))
            if not pid or cant <= 0: continue
            row = conn.execute(
                "SELECT stock_actual, nombre FROM inventario_general WHERE producto_id=?", (pid,)
            ).fetchone()
            if row:
                disp = float(row[0]) if row[0] else 0
                if disp < cant:
                    sin_stock.append({"producto_id": pid, "nombre": row[1] or pid,
                                      "solicitado": cant, "disponible": disp,
                                      "faltante": round(cant - disp, 2)})
    except Exception as e:
        return {"valido": False, "error": str(e)}
    finally:
        conn.close()
    return {"valido": True} if not sin_stock else {"valido": False, "sin_stock": sin_stock}

# ══════════════════════════════════════════════════════════════
#  CIERRE DE CAJA SERVER-SIDE
# ══════════════════════════════════════════════════════════════
def calcular_cierre_server(fecha, vendedor_id=None):
    from database import obtener_conexion
    conn = obtener_conexion()
    try:
        where = "WHERE fecha=?" + (" AND vendedor_id=?" if vendedor_id else "")
        params = [fecha] + ([vendedor_id] if vendedor_id else [])
        row = conn.execute(f"""
            SELECT COUNT(*), COALESCE(SUM(total),0)
            FROM historial_ventas {where}
        """, params).fetchone()
        total_ventas = round(row[1] or 0, 2)
        return {
            "num_ventas": row[0] or 0,
            "total_ventas": total_ventas
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
#  AUDITORIA — Middleware
# ══════════════════════════════════════════════════════════════
_RUTAS_AUDIT = [
    '/api/auth/login', '/api/auth/logout',
    '/api/usuarios/crear', '/api/licencias/crear',
    '/api/gastos', '/api/inventario/entrada',
    '/api/inventario/general/eliminar',
    '/api/limpiar-tablas', '/api/reconstruir',
]

def registrar_auditoria(app_instance):
    @app_instance.before_request
    def audit_log():
        from flask import request, session
        try:
            path = request.path
            if any(path.startswith(r) for r in _RUTAS_AUDIT):
                u = session.get('usuario', {})
                entry = {
                    "ts": datetime.now().isoformat(),
                    "user": u.get('usuario_id', 'anon'),
                    "rol": u.get('rol', '-'),
                    "method": request.method,
                    "path": path,
                    "ip": request.remote_addr,
                }
                try:
                    from database import agregar_log
                    agregar_log(f"AUDIT:{json.dumps(entry, ensure_ascii=False)}", "info")
                except Exception:
                    pass
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════
#  CIFRADO LIVIANO PARA DATOS SENSIBLES (offline-safe)
# ══════════════════════════════════════════════════════════════
_OBFUSC_KEY = None

def _get_key():
    global _OBFUSC_KEY
    if _OBFUSC_KEY is None:
        try:
            _OBFUSC_KEY = uuid.uuid4().hex[:32]
        except Exception:
            _OBFUSC_KEY = "tpv_ultra_smart_default_key_32"
    return _OBFUSC_KEY

def cifrar_valor(valor):
    if not valor: return valor
    key = _get_key().encode()
    data = str(valor).encode()
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(xored).decode()

def descifrar_valor(cifrado):
    if not cifrado: return cifrado
    try:
        key = _get_key().encode()
        data = base64.b64decode(cifrado)
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return xored.decode()
    except Exception:
        return None
