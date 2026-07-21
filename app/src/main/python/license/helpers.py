import hmac, hashlib, os, json, time, sqlite3, threading
from datetime import datetime, timedelta


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
                except Exception:  # noqa: broad-except
                    pass
            if not _SECRET:
                _SECRET = os.urandom(32).hex()
                try:
                    with open('.tpv_secret_key', 'w') as f:
                        f.write(_SECRET)
                except Exception:  # noqa: broad-except
                    pass
    return _SECRET


# ═════════════════════════════════════════════════════
#  BD
# ═════════════════════════════════════════════════════

def _db():
    """Open the application database, including Android/isolated data dirs."""
    data_dir = os.environ.get("TPV_FILES_DIR")
    paths = []
    if data_dir:
        paths.append(os.path.join(data_dir, "tpv_datos.db"))
    paths.extend([
        "tpv_datos.db",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "tpv_datos.db"),
    ])
    for p in paths:
        if os.path.exists(p) or (data_dir and p == paths[0]):
            try:
                os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
                c = sqlite3.connect(p, timeout=3, check_same_thread=False)
                c.row_factory = sqlite3.Row
                return c
            except sqlite3.Error:
                continue
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

