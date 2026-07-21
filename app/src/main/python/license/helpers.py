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
            data_dir = os.environ.get("TPV_FILES_DIR", os.getcwd())
            key_path = os.path.join(data_dir, ".tpv_secret_key")
            # The module path is read only in APK; it is read only as a legacy
            # migration fallback and is never used as a write destination.
            legacy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tpv_secret_key")
            for path in (key_path, legacy_path):
                try:
                    with open(path, "r", encoding="utf-8") as key_file:
                        _SECRET = key_file.read().strip()
                        break
                except OSError:
                    pass
            if not _SECRET:
                _SECRET = os.urandom(32).hex()
                try:
                    os.makedirs(data_dir, exist_ok=True)
                    with open(key_path, "w", encoding="utf-8") as key_file:
                        key_file.write(_SECRET)
                    os.chmod(key_path, 0o600)
                except OSError:
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

