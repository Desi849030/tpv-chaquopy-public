# -*- coding: utf-8 -*-
"""config.py - TPV Ultra Smart - Configuración centralizada"""
import os
from pathlib import Path

# ═══ Ruta del proyecto ═══
def _detectar_ruta():
    try:
        import tpv_rutas
        return tpv_rutas.obtener_ruta_base()
    except:
        pass
    p = Path(__file__).resolve().parent
    for intento in [p, p / '..' / 'assets' / 'frontend', p.parent]:
        if (intento / 'index.html').exists():
            return str(intento)
    return str(p)

CARPETA = os.environ.get("TPV_FRONTEND_DIR") or _detectar_ruta()

# ═══ Secretos ═══
def _cargar_secreto():
    for p in ['.tpv_secret_key', os.path.join(CARPETA, '.tpv_secret_key')]:
        try:
            with open(p, 'r') as f: return f.read().strip()
        except: pass
    import secrets
    s = secrets.token_hex(32)
    try:
        with open('.tpv_secret_key', 'w') as f: f.write(s)
    except: pass
    return s

SECRET_KEY = _cargar_secreto()

# ═══ Flask defaults ═══
SESSION_COOKIE_DOMAIN = None
PERMANENT_SESSION_LIFETIME = 86400 * 7

# ═══ Módulos disponibles (para privilegios) ═══
MODULOS_DISPONIBLES = {
    "catalogo": "Gestion de catalogo", "ventas": "Registro de ventas",
    "caja": "Caja y cobros", "dashboard": "Panel estadisticas",
    "inventario": "Control inventario", "productos": "CRUD productos",
    "categorias": "Gestion categorias", "orden": "Gestion de ordenes",
    "tienda": "Tienda online", "registros": "Historial",
    "herramientas": "Herramientas", "configuracion": "Configuracion",
    "usuarios": "Gestion usuarios", "licencias": "Gestion licencias",
    "debug": "Panel depuracion", "privilegios": "Gestion privilegios",
    "blindajes": "Panel blindajes", "ia_edge": "IA Edge Analytics",
    "lealtad": "Programa Lealtad", "asistente_ia": "Asistente IA",
    "descuentos": "Descuentos", "supabase": "Configuracion Supabase",
    "seguridad": "Seguridad", "exportar": "Exportar datos",
    "copias": "Copias de seguridad"
}

# ═══ Privilegios default por rol ═══
PRIVILEGIOS_DEFAULT = {
    "desarrollador": MODULOS_DISPONIBLES,
    "administrador": {k: v for k, v in MODULOS_DISPONIBLES.items() if k not in ("debug", "privilegios", "licencias")},
    "supervisor": {k: v for k, v in MODULOS_DISPONIBLES.items() if k in ("catalogo", "ventas", "inventario", "dashboard", "productos", "registros", "tienda", "lealtad", "descuentos")},
    "vendedor": {k: v for k, v in MODULOS_DISPONIBLES.items() if k in ("catalogo", "ventas", "inventario", "productos", "tienda")},
    "cliente": {k: v for k, v in MODULOS_DISPONIBLES.items() if k in ("catalogo", "tienda", "lealtad")}
}

print("[config.py] Configuración centralizada cargada")
