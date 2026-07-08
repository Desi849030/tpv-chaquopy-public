"""
tpv_rutas.py — TPV Ultra Smart
Deteccion automatica de rutas para Pydroid 3 y Android
"""
import os, sys

def _buscar():
    candidatas = []
    try:
        candidatas.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    candidatas += [
        os.getcwd(),
        '/storage/emulated/0/TPV_APK',
        '/storage/emulated/0/TPV',
        '/sdcard/TPV_APK',
        '/sdcard/TPV',
    ]
    # Busqueda en subcarpetas de backend
    for c in list(candidatas):
        parent = os.path.dirname(c)
        if parent and parent not in candidatas:
            candidatas.append(parent)
    for r in candidatas:
        if r and os.path.exists(os.path.join(r, 'buildozer.spec')):
            return r
        if r and os.path.exists(os.path.join(r, 'backend', 'database.py')):
            return r
        if r and os.path.exists(os.path.join(r, 'database.py')):
            return r
    # Busqueda en /storage/emulated/0
    try:
        for item in os.listdir('/storage/emulated/0'):
            ruta = '/storage/emulated/0/' + item
            if os.path.isdir(ruta) and os.path.exists(ruta + '/buildozer.spec'):
                return ruta
    except Exception:
        pass
    return os.getcwd()

BASE = _buscar()

def fix_path():
    global BASE
    # Añadir raiz del proyecto
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    # Añadir backend/
    backend = os.path.join(BASE, 'backend')
    if os.path.exists(backend) and backend not in sys.path:
        sys.path.insert(0, backend)
    try:
        os.chdir(BASE)
    except Exception:
        pass
    print("TPV cargado desde: " + BASE)
    return BASE

CARPETA = BASE
