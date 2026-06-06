# -*- coding: utf-8 -*-
"""
Iniciar servidor Flask para TPV Ultra Smart (Chaquopy / Android).

IMPORTANTE: MainActivity hace `py.getModule("start_server")`, que IMPORTA este
módulo pero NO ejecuta el bloque `if __name__ == '__main__'`. Por eso el
servidor se arranca automáticamente al importar (en un hilo daemon).
"""
import os
import sys
import threading

_SERVER_THREAD = None


def _run():
    """Arranca Flask. Se ejecuta en un hilo para no bloquear la importación."""
    try:
        files_dir = os.environ.get(
            'TPV_FILES_DIR',
            os.path.dirname(os.path.abspath(__file__)))
        frontend_dir = os.environ.get('TPV_FRONTEND_DIR', files_dir + '/frontend')

        if files_dir not in sys.path:
            sys.path.insert(0, files_dir)

        from app import app

        app.config['FRONTEND_DIR'] = frontend_dir
        port = int(os.environ.get('TPV_PORT', 5050))

        print("🚀 Servidor TPV iniciado en puerto %s" % port)
        print("📁 Frontend: %s" % frontend_dir)

        # threaded=True para atender peticiones concurrentes del WebView.
        app.run(host='127.0.0.1', port=port, debug=False,
                use_reloader=False, threaded=True)
    except Exception as e:  # noqa: BLE001
        print("❌ Error al iniciar el servidor: %s" % e)
        import traceback
        traceback.print_exc()


def start_server():
    """Arranca el servidor en un hilo daemon (idempotente)."""
    global _SERVER_THREAD
    if _SERVER_THREAD and _SERVER_THREAD.is_alive():
        return _SERVER_THREAD
    _SERVER_THREAD = threading.Thread(target=_run, name="tpv-flask", daemon=True)
    _SERVER_THREAD.start()
    return _SERVER_THREAD


# --- Arranque automático al IMPORTAR el módulo (clave para Chaquopy) ---
# MainActivity hace getModule("start_server"); esto dispara el servidor.
start_server()


if __name__ == '__main__':
    # Si se ejecuta directamente, mantener vivo el proceso.
    import time
    while True:
        time.sleep(3600)
