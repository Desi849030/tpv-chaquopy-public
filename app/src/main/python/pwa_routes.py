"""
pwa_routes.py — TPV Ultra Smart (PWA Support)
Rutas mínimas para manifest.json y service-worker
"""
import os, json
from flask import Response

def registrar_pwa(app):
    _DIR = os.path.dirname(os.path.abspath(__file__))
    
    def _leer_archivo(nombre, modo='r'):
        candidatos = [
            os.path.join(os.getcwd(), nombre),
            os.path.join(_DIR, nombre),
            os.path.join('/storage/emulated/0/TPV_APK', nombre),
        ]
        for ruta in candidatos:
            if os.path.exists(ruta):
                with open(ruta, modo) as f: return f.read()
        return None
    
    @app.route('/manifest.json')
    def pwa_manifest():
        contenido = _leer_archivo('manifest.json', 'r')
        if contenido: return Response(contenido, mimetype='application/manifest+json')
        return Response(json.dumps({
            "name": "TPV Ultra Smart", "short_name": "TPV", "start_url": "/",
            "display": "standalone", "background_color": "#ffffff", "theme_color": "#1E4D8C",
            "icons": [{"src": "/pwa-icon-192.png", "sizes": "192x192", "type": "image/png"}]
        }), mimetype='application/manifest+json')
    
    @app.route('/service-worker.js')
    def pwa_sw():
        contenido = _leer_archivo('service-worker.js', 'r')
        if contenido: return Response(contenido, mimetype='application/javascript', headers={'Service-Worker-Allowed': '/'})
        return Response("self.addEventListener('fetch',e=>{});", mimetype='application/javascript')
    
    @app.route('/pwa-icon-<int:size>.png')
    def pwa_icon(size):
        return Response(b'', mimetype='image/png', status=404)  # Placeholder
    
    print("✅ Rutas PWA registradas")
