"""
═══════════════════════════════════════════════════════════════
  pwa_routes.py  —  TPV Ultra Smart
  Añade las 3 rutas necesarias para convertir el TPV en PWA

  INSTRUCCIONES DE USO:
  1. Copia este archivo a la misma carpeta que app.py
  2. En app.py añade estas 2 líneas justo después de crear 'app':

       from pwa_routes import registrar_pwa
       registrar_pwa(app)

  3. Copia también a la misma carpeta:
       - manifest.json
       - service-worker.js
       - pwa-icon-192.png
       - pwa-icon-512.png  (generados por generar_icono_pwa.py)

  4. En index.html añade dentro del <head>:
       <link rel="manifest" href="/manifest.json">
       <meta name="theme-color" content="#1E4D8C">
       <meta name="mobile-web-app-capable" content="yes">
       <meta name="apple-mobile-web-app-capable" content="yes">
       <meta name="apple-mobile-web-app-status-bar-style" content="default">
       <meta name="apple-mobile-web-app-title" content="TPV Smart">
       <script>
         if ('serviceWorker' in navigator) {
           navigator.serviceWorker.register('/service-worker.js')
             .then(() => console.log('PWA lista'))
             .catch(e => console.error('SW error:', e));
         }
       </script>
═══════════════════════════════════════════════════════════════
"""

import os
import json
from flask import Response, request


def registrar_pwa(app):
    """
    Registra las rutas PWA en la app Flask.
    Llama a esta función después de crear la instancia Flask.
    """

    _DIR = os.path.dirname(os.path.abspath(__file__))

    def _leer_archivo(nombre, modo='rb'):
        """Busca el archivo en la carpeta del proyecto."""
        candidatos = [
            os.path.join(os.getcwd(), nombre),
            os.path.join(_DIR, nombre),
            os.path.join('/storage/emulated/0/TPV_APK', nombre),
        ]
        for ruta in candidatos:
            if os.path.exists(ruta):
                with open(ruta, modo) as f:
                    return f.read()
        return None

    # ── Ruta 1: manifest.json ─────────────────────────────────
    @app.route('/manifest.json')
    def pwa_manifest():
        contenido = _leer_archivo('manifest.json', 'r')
        if contenido:
            return Response(contenido, mimetype='application/manifest+json')
        # Manifest por defecto si no existe el archivo
        manifest = {
            "name": "TPV Ultra Smart",
            "short_name": "TPV Smart",
            "description": "Sistema de Punto de Venta Profesional",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#1E4D8C",
            "orientation": "portrait-primary",
            "scope": "/",
            "lang": "es",
            "icons": [
                {"src": "/pwa-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                {"src": "/pwa-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            ]
        }
        return Response(json.dumps(manifest, ensure_ascii=False), mimetype='application/manifest+json')

    # ── Ruta 2: service-worker.js ─────────────────────────────
    @app.route('/service-worker.js')
    def pwa_service_worker():
        contenido = _leer_archivo('service-worker.js', 'r')
        if contenido:
            return Response(
                contenido,
                mimetype='application/javascript',
                headers={'Service-Worker-Allowed': '/'}
            )
        # Service worker mínimo si no existe el archivo
        sw_minimo = """
const CACHE='tpv-v1';
self.addEventListener('install',e=>{self.skipWaiting();});
self.addEventListener('activate',e=>{self.clients.claim();});
self.addEventListener('fetch',e=>{
  if(e.request.url.includes('/api/'))return;
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
"""
        return Response(sw_minimo, mimetype='application/javascript',
                        headers={'Service-Worker-Allowed': '/'})

    # ── Ruta 3: iconos PNG ────────────────────────────────────
    @app.route('/pwa-icon-<int:size>.png')
    def pwa_icono(size):
        nombre = f'pwa-icon-{size}.png'
        contenido = _leer_archivo(nombre, 'rb')
        if contenido:
            return Response(contenido, mimetype='image/png')

        # Generar icono básico en memoria si no existe el archivo
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            img = Image.new('RGB', (size, size), color='#1E4D8C')
            draw = ImageDraw.Draw(img)
            margen = int(size * 0.1)
            draw.ellipse([margen, margen, size - margen, size - margen], fill='#2E75B6')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            return Response(buf.read(), mimetype='image/png')
        except ImportError:
            # Sin Pillow: devuelve 1x1 pixel transparente
            import base64
            pixel = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
            )
            return Response(pixel, mimetype='image/png')

    print('✅ Rutas PWA registradas: /manifest.json, /service-worker.js, /pwa-icon-*.png')
