import hashlib, time, re, uuid, threading, json, base64
from functools import wraps
from datetime import datetime



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


_SQLI_PATTERNS = ["'; ", "--", "/*", "*/", "xp_", "UNION ", "SELECT ", "INSERT ", "DELETE ", "UPDATE ", "DROP "]

# Patrones regex para vectores que no se detectan por subcadena simple:
# - Tautologias:  ' OR '1'='1 ,  " OR 1=1 ,  ) OR (1=1
# - Comentarios de fin de linea:  admin'--  ,  admin'#
# - Apilado de sentencias:  ; DROP TABLE
# - Funciones peligrosas:  SLEEP( , BENCHMARK( , LOAD_FILE(
_SQLI_REGEX = re.compile(
    r"('|\"|\)|\s)\s*(OR|AND)\s+\(?\s*[\w'\"]+\s*=\s*[\w'\"]+"  # OR/AND tautologico (admite parentesis)
    r"|('|\")\s*(OR|AND)\s+\d"                            # ' OR 1...
    r"|;\s*(DROP|DELETE|UPDATE|INSERT|TRUNCATE|ALTER)\b"  # sentencias apiladas
    r"|\b(SLEEP|BENCHMARK|LOAD_FILE|WAITFOR\s+DELAY)\s*\(" # time-based / files
    r"|('|\")\s*(--|#)",                                   # comentario tras comilla
    re.IGNORECASE,
)


def check_sql_injection(data):
    if isinstance(data, dict):
        return any(check_sql_injection(v) for v in data.values())
    elif isinstance(data, list):
        return any(check_sql_injection(i) for i in data)
    elif isinstance(data, str):
        d = data.upper()
        if any(p.upper() in d for p in _SQLI_PATTERNS):
            return True
        return bool(_SQLI_REGEX.search(data))
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
    from db_connection import obtener_conexion
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
    from db_connection import obtener_conexion
    conn = obtener_conexion()
    try:
        where = "WHERE fecha=?" + (" AND vendedor_id=?" if vendedor_id else "")
        params = [fecha] + ([vendedor_id] if vendedor_id else [])
        # tabla is validated against TABLAS_PERMITIDAS whitelist
        row = conn.execute("""
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



def sanitize_input(value):
    """Sanitiza entrada de usuario contra SQLi y XSS"""
    if not value:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    
    value = str(value).strip()
    
    # Remove control characters (NULL, etc)
    value = ''.join(ch for ch in value if ord(ch) >= 32 or ch == '\n' or ch == '\t')
    
    # Escape HTML entities
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    value = value.replace('"', "&quot;")
    value = value.replace("'", "&#x27;")
    
    # Remove dangerous SQL patterns
    dangerous = ["DROP", "UNION", "SELECT", "INSERT", "DELETE", "UPDATE", "--", "/*", "*/", "OR 1=1"]
    for d in dangerous:
        if d.lower() in value.lower():
            value = value.replace(d, "")
    
    # Limit length
    if len(value) > 255:
        value = value[:255]
    
        # Remove event handlers (XSS)
    event_handlers = ["onerror", "onload", "onclick", "onmouseover", "onfocus", "onblur", "onsubmit"]
    for handler in event_handlers:
        if handler.lower() in value.lower():
            value = value.replace(handler, "")
    
    return value

def validate_email(email):
    import re
    if not email or not isinstance(email, str):
        return False
    pattern = "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
    return bool(re.match(pattern, email))
