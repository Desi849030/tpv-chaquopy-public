# -*- coding: utf-8 -*-
"""
license_manager.py v2.0 - TPV Ultra Smart
Sistema de licencias robusto del lado del servidor.
Validación HMAC, vinculación por device ID, gracia post-expiración.
"""
import hmac, hashlib, os, json, time, sqlite3, threading
from datetime import datetime, timedelta

# ═════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═════════════════════════════════════════════════════
_SECRET = None
_LK = threading.Lock()

def _get_secret():
    """Carga o genera la clave secreta para firmar licencias."""
    global _SECRET
    if _SECRET:
        return _SECRET
    with _LK:
        if not _SECRET:
            # Buscar en .tpv_secret_key o generar una
            for p in ['.tpv_secret_key', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tpv_secret_key')]:
                try:
                    with open(p, 'r') as f:
                        _SECRET = f.read().strip()
                        break
                except:
                    pass
            if not _SECRET:
                _SECRET = os.urandom(32).hex()
                try:
                    with open('.tpv_secret_key', 'w') as f:
                        f.write(_SECRET)
                except:
                    pass
    return _SECRET


# ═════════════════════════════════════════════════════
#  BD
# ═════════════════════════════════════════════════════
def _db():
    for p in ['tpv_datos.db', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')]:
        if os.path.exists(p):
            c = sqlite3.connect(p, timeout=3, check_same_thread=False)
            c.row_factory = sqlite3.Row
            return c
    return None

def _init_table():
    c = _db()
    if not c:
        return
    c.execute('''CREATE TABLE IF NOT EXISTS licencias_servidor (
        licencia_id TEXT PRIMARY KEY,
        device_id TEXT NOT NULL,
        tipo TEXT DEFAULT 'trial',
        valor TEXT DEFAULT 7,
        unidad TEXT DEFAULT 'dias',
        fecha_activacion TEXT,
        fecha_expiracion TEXT,
        firma_hmac TEXT NOT NULL,
        activa INTEGER DEFAULT 1,
        nota TEXT DEFAULT ''
    )''')
    c.commit()
    c.close()


# ═════════════════════════════════════════════════════
#  GENERACIÓN DE LICENCIAS
# ═════════════════════════════════════════════════════
def generar_licencia(device_id, tipo='trial', valor=7, unidad='dias', nota=''):
    """
    Genera una licencia firmada con HMAC.
    Devuelve dict con licencia_id, firma, fecha_expiracion.
    """
    _init_table()
    
    secret = _get_secret()
    licencia_id = f"LIC-{hmac.new(secret.encode(), f'{device_id}{time.time()}'.encode(), hashlib.sha256).hexdigest()[:16].upper()}"
    
    # Calcular expiración
    now = datetime.now()
    if unidad == 'dias':
        exp = now + timedelta(days=valor)
    elif unidad == 'horas':
        exp = now + timedelta(hours=valor)
    elif unidad == 'minutos':
        exp = now + timedelta(minutes=valor)
    elif unidad == 'meses':
        exp = now + timedelta(days=valor * 30)
    else:
        exp = now + timedelta(days=valor)
    
    # Firma HMAC (no se puede falsificar sin la clave secreta)
    payload = f"{licencia_id}:{device_id}:{tipo}:{valor}:{unidad}:{exp.isoformat()}"
    firma = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    
    # Guardar en BD
    c = _db()
    if c:
        c.execute('''INSERT OR REPLACE INTO licencias_servidor 
            (licencia_id, device_id, tipo, valor, unidad, fecha_activacion, fecha_expiracion, firma_hmac, activa, nota)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (licencia_id, device_id, tipo, valor, unidad, now.isoformat(), exp.isoformat(), firma, 1, nota))
        c.commit()
        c.close()
    
    return {
        'licencia_id': licencia_id,
        'device_id': device_id,
        'tipo': tipo,
        'valor': valor,
        'unidad': unidad,
        'fecha_activacion': now.isoformat(),
        'fecha_expiracion': exp.isoformat(),
        'firma': firma
    }


# ═════════════════════════════════════════════════════
#  VALIDACIÓN DE LICENCIAS
# ═════════════════════════════════════════════════════
def validar_licencia(device_id):
    """
    Valida si hay una licencia activa para el device_id.
    Retorna dict con: {valida, estado, dias_restantes, licencia, mensaje}
    
    Estados:
    - 'activa': licencia vigente
    - 'gracia': expirada pero dentro del periodo de gracia (3 dias)
    - 'expirada': licencia expirada fuera de gracia
    - 'sin_licencia': no hay licencia registrada
    """
    _init_table()
    c = _db()
    if not c:
        # Sin BD = modo desarrollo = sin restricción
        return {'valida': True, 'estado': 'sin_bd', 'dias_restantes': 999, 'licencia': None, 'mensaje': 'Modo desarrollo'}
    
    try:
        row = c.execute(
            '''SELECT * FROM licencias_servidor 
               WHERE device_id = ? AND activa = 1 
               ORDER BY fecha_expiracion DESC LIMIT 1''',
            (device_id,)
        ).fetchone()
        
        if not row:
            return {'valida': False, 'estado': 'sin_licencia', 'dias_restantes': 0, 'licencia': None, 'mensaje': 'Sin licencia registrada'}
        
        # Verificar firma HMAC (anti-tampering)
        secret = _get_secret()
        payload = f"{row['licencia_id']}:{row['device_id']}:{row['tipo']}:{row['valor']}:{row['unidad']}:{row['fecha_expiracion']}"
        firma_esperada = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(firma_esperada, row['firma_hmac']):
            # Firma invalida = licencia manipulada
            c.execute('UPDATE licencias_servidor SET activa = 0 WHERE licencia_id = ?', (row['licencia_id'],))
            c.commit()
            return {'valida': False, 'estado': 'falsificada', 'dias_restantes': 0, 'licencia': None, 'mensaje': 'Licencia invalida (firma no coincide)'}
        
        # Verificar expiración
        exp = datetime.fromisoformat(row['fecha_expiracion'])
        ahora = datetime.now()
        diff = (exp - ahora).total_seconds()
        dias = diff / 86400
        
        if diff > 0:
            # Vigente
            lic_info = {
                'licencia_id': row['licencia_id'],
                'tipo': row['tipo'],
                'fecha_expiracion': row['fecha_expiracion'],
                'dias_restantes': round(dias, 1)
            }
            return {'valida': True, 'estado': 'activa', 'dias_restantes': round(dias, 1), 'licencia': lic_info, 'mensaje': 'Licencia activa'}
        
        # Expirada - verificar periodo de gracia (3 dias)
        if diff > -259200:  # 3 * 24 * 3600
            lic_info = {
                'licencia_id': row['licencia_id'],
                'tipo': row['tipo'],
                'fecha_expiracion': row['fecha_expiracion'],
                'dias_restantes': 0
            }
            return {'valida': True, 'estado': 'gracia', 'dias_restantes': 0, 'licencia': lic_info, 'mensaje': f'Periodo de gracia ({abs(round(dias, 1))} dias)'}
        
        # Expirada fuera de gracia
        return {'valida': False, 'estado': 'expirada', 'dias_restantes': 0, 'licencia': None, 'mensaje': f'Expirada el {row["fecha_expiracion"][:10]}'}
    
    except Exception as e:
        return {'valida': False, 'estado': 'error', 'dias_restantes': 0, 'licencia': None, 'mensaje': str(e)}
    finally:
        c.close()


def activar_licencia(licencia_id, device_id):
    """
    Activa una licencia existente para un device_id diferente.
    Útil cuando el desarrollador genera una licencia y se la da al cliente.
    """
    _init_table()
    c = _db()
    if not c:
        return {'ok': False, 'error': 'Sin base de datos'}
    
    try:
        row = c.execute('SELECT * FROM licencias_servidor WHERE licencia_id = ?', (licencia_id,)).fetchone()
        if not row:
            return {'ok': False, 'error': 'Licencia no encontrada'}
        
        # Verificar firma
        secret = _get_secret()
        payload = f"{row['licencia_id']}:{row['device_id']}:{row['tipo']}:{row['valor']}:{row['unidad']}:{row['fecha_expiracion']}"
        firma_esperada = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(firma_esperada, row['firma_hmac']):
            return {'ok': False, 'error': 'Licencia invalida'}
        
        # Verificar que no esté expirada
        exp = datetime.fromisoformat(row['fecha_expiracion'])
        if datetime.now() > exp:
            return {'ok': False, 'error': 'Licencia expirada'}
        
        # Cambiar device_id y activar
        new_payload = f"{licencia_id}:{device_id}:{row['tipo']}:{row['valor']}:{row['unidad']}:{row['fecha_expiracion']}"
        new_firma = hmac.new(secret.encode(), new_payload.encode(), hashlib.sha256).hexdigest()
        
        c.execute('''UPDATE licencias_servidor 
            SET device_id = ?, firma_hmac = ?, activa = 1, fecha_activacion = ?
            WHERE licencia_id = ?''',
            (device_id, new_firma, datetime.now().isoformat(), licencia_id))
        c.commit()
        
        return {'ok': True, 'mensaje': 'Licencia activada correctamente'}
    
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        c.close()


def desactivar_licencia(licencia_id):
    """Desactiva una licencia."""
    c = _db()
    if not c:
        return {'ok': False, 'error': 'Sin base de datos'}
    c.execute('UPDATE licencias_servidor SET activa = 0 WHERE licencia_id = ?', (licencia_id,))
    c.commit()
    c.close()
    return {'ok': True, 'mensaje': 'Licencia desactivada'}


def listar_licencias():
    """Lista todas las licencias."""
    _init_table()
    c = _db()
    if not c:
        return []
    rows = c.execute('SELECT * FROM licencias_servidor ORDER BY fecha_expiracion DESC').fetchall()
    c.close()
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════
#  MIDDLEWARE: Verificar licencia en cada request
# ═════════════════════════════════════════════════════
# Rutas que NO requieren verificación de licencia
_RUTAS_LIBRES = {
    "/api/auth/login", "/api/auth/logout", "/api/health",
    "/api/ping", "/api/license/validate", "/api/license/activate",
    "/api/license/generate", "/api/license/device-id",
    "/api/config/publica", "/api/catalogo",
    "/api/clientes/registrar", "/api/clientes/login", "/api/tienda"
}

def requiere_licencia(f):
    """Decorador: verifica licencia antes de ejecutar la ruta."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, session, jsonify
        # Rutas libres
        if request.path in _RUTAS_LIBRES or request.path.startswith("/api/clientes") or request.path.startswith("/api/tienda"):
            return f(*args, **kwargs)
        # DESARROLLADOR es inmune
        u = session.get("usuario", {})
        if u.get("rol") == "desarrollador":
            return f(*args, **kwargs)
        # Obtener device_id
        device_id = request.headers.get("X-Device-ID", "") or request.args.get("device_id", "")
        if not device_id:
            return f(*args, **kwargs)
        # Validar licencia
        resultado = validar_licencia(device_id)
        if not resultado["valida"]:
            return jsonify({"error": "licencia_expirada", "mensaje": resultado["mensaje"], "estado": resultado["estado"]}), 403
        request.licencia = resultado
        return f(*args, **kwargs)
    return decorated

def generar_device_id():
    """Genera un ID único para el dispositivo basado en hardware."""
    import platform
    info = f"{platform.node()}-{platform.machine()}-{os.getlogin() if hasattr(os,'getlogin') else 'unknown'}"
    hash_id = hashlib.sha256(info.encode()).hexdigest()[:12].upper()
    return f"TPV-{hash_id}"

# Inicializar tabla al importar
_init_table()

print("✅ license_manager.py v2.0 listo - Licencias server-side activas")
