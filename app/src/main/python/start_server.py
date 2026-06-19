# -*- coding: utf-8 -*-
"""
Iniciar servidor Flask para TPV Ultra Smart (Chaquopy / Android).

IMPORTANTE: MainActivity hace `py.getModule("start_server")`, que IMPORTA este
módulo pero NO ejecuta `if __name__ == '__main__'`. Por eso el servidor se
arranca automáticamente al importar (en un hilo daemon).

CAPTURA DE CRASH: si el servidor principal falla al arrancar, se guarda el
traceback completo en TPV_FILES_DIR/crash.log y se levanta un servidor MÍNIMO
de emergencia que MUESTRA el error en el WebView (en vez de cerrar la app).
"""
import os
import sys
import threading
import traceback
from datetime import datetime

_SERVER_THREAD = None


def configurar(files_dir, frontend_dir):
    """Recibe las rutas DESDE Java y las pone en os.environ.

    CLAVE: Java usa System.setProperty(), que NO aparece en os.environ de
    Python. Por eso MainActivity debe llamar a esta función pasando las rutas;
    así Python sí las ve. Llamar ANTES de que se importe 'app'.
    """
    try:
        if files_dir:
            os.environ['TPV_FILES_DIR'] = str(files_dir)
        if frontend_dir:
            os.environ['TPV_FRONTEND_DIR'] = str(frontend_dir)
        print("⚙️ Config recibida de Java: files=%s frontend=%s" % (files_dir, frontend_dir))
    except Exception:
        traceback.print_exc()
    return True


def _files_dir():
    return os.environ.get('TPV_FILES_DIR', os.path.dirname(os.path.abspath(__file__)))


def _guardar_crash(texto):
    """Guarda el error en crash.log (para poder verlo/enviarlo después)."""
    try:
        ruta = os.path.join(_files_dir(), 'crash.log')
        with open(ruta, 'a', encoding='utf-8') as f:
            f.write("\n===== %s =====\n%s\n" % (datetime.now().isoformat(), texto))
        return ruta
    except Exception:
        return ''


def _servidor_emergencia(port, error_texto):
    """Servidor mínimo que muestra el error en el navegador/WebView."""
    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer

        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>TPV - Error</title></head>"
            "<body style='background:#0a0e1a;color:#e2e8f0;font-family:sans-serif;padding:18px'>"
            "<h2 style='color:#f87171'>⚠️ El servidor TPV no pudo iniciar</h2>"
            "<p>Comparte esta información para diagnosticar el problema:</p>"
            "<pre style='white-space:pre-wrap;background:#111827;padding:12px;"
            "border-radius:8px;font-size:11px;color:#cbd5e1;overflow:auto'>"
            + (error_texto.replace('<', '&lt;').replace('>', '&gt;')) +
            "</pre></body></html>"
        )
        html_bytes = html.encode('utf-8')

        class H(BaseHTTPRequestHandler):
            def _send(self, body, ctype='text/html; charset=utf-8'):
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == '/api/health':
                    self._send(b'{"status":"error","db":false}', 'application/json')
                else:
                    self._send(html_bytes)

            def log_message(self, *a):
                pass

        HTTPServer(('127.0.0.1', port), H).serve_forever()
    except Exception:
        traceback.print_exc()


def _run():
    """Arranca Flask. En error, guarda crash.log y levanta el de emergencia."""
    port = int(os.environ.get('TPV_PORT', 5050))
    try:
        files_dir = _files_dir()
        frontend_dir = os.environ.get('TPV_FRONTEND_DIR', files_dir + '/frontend')
        if files_dir not in sys.path:
            sys.path.insert(0, files_dir)

        from app import app

        app.config['FRONTEND_DIR'] = frontend_dir
        print("🚀 Servidor TPV iniciado en puerto %s" % port)
        print("📁 Frontend: %s" % frontend_dir)
        app.run(host='0.0.0.0', port=port, debug=False,
                use_reloader=False, threaded=True)
    except Exception:
        err = traceback.format_exc()
        ruta = _guardar_crash(err)
        print("❌ CRASH al iniciar el servidor. Guardado en: %s\n%s" % (ruta, err))
        # Levantar servidor de emergencia para mostrar el error en el WebView.
        _servidor_emergencia(port, err)


def start_server():
    """Arranca el servidor en un hilo daemon (idempotente)."""
    global _SERVER_THREAD
    if _SERVER_THREAD and _SERVER_THREAD.is_alive():
        return _SERVER_THREAD
    _SERVER_THREAD = threading.Thread(target=_run, name="tpv-flask", daemon=True)
    _SERVER_THREAD.start()
    return _SERVER_THREAD


def iniciar(files_dir=None, frontend_dir=None):
    """Punto de entrada que llama MainActivity: configura rutas y arranca.
    Se invoca con callAttr('iniciar', filesDir, frontendDir). Configura las
    rutas en os.environ ANTES de importar 'app' (dentro de start_server)."""
    configurar(files_dir, frontend_dir)
    return start_server()


# Auto-arranque SOLO si una variable de entorno ya está disponible (Termux/CI)
# o si nadie va a llamar iniciar(). En la APK, MainActivity llama iniciar(...)
# con las rutas correctas, así que NO autoarrancamos aquí para no hacerlo antes
# de recibir las rutas (evita el 'TPV no encontrado').
_EN_ANDROID = False
try:
    import java  # noqa: F401  (solo existe dentro de Chaquopy/Android)
    _EN_ANDROID = True
except Exception:
    _EN_ANDROID = False

if not _EN_ANDROID:
    # Termux / navegador / CI: arrancar al importar (no hay Java que llame iniciar)
    start_server()


if __name__ == '__main__':
    import time
    while True:
        time.sleep(3600)
