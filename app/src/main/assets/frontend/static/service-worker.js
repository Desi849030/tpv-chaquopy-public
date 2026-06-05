/* TPV UltraSmart — Service Worker v2 (offline-first)
   Estrategia:
   - Assets estáticos (/static/...): cache-first (rápido y offline).
   - Navegación / API: network-first con fallback offline.
   La app corre contra Flask local en la APK, así que esto refuerza
   la carga incluso si el servidor tarda en levantar. */

const CACHE = 'tpv-static-v2';

// Precache de los recursos críticos de la UI (todos locales).
const PRECACHE = [
  '/',
  '/static/lib/bootstrap.min.css',
  '/static/lib/bootstrap-icons.css',
  '/static/lib/poppins.css',
  '/static/lib/bootstrap.bundle.min.js',
  '/static/lib/chart.umd.min.js',
  '/static/css/modulo_0.css',
  '/static/css/modulo_1.css',
  '/static/css/modulo_2.css',
  '/static/css/modulo_3.css',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(PRECACHE.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Cache-first para assets estáticos.
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(req).then((cached) => {
        if (cached) return cached;
        return fetch(req).then((resp) => {
          if (resp && resp.status === 200) {
            const copy = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return resp;
        }).catch(() => cached);
      })
    );
    return;
  }

  // Network-first para navegación y API, con fallback.
  e.respondWith(
    fetch(req).catch(() =>
      caches.match(req).then((cached) =>
        cached || new Response(JSON.stringify({ offline: true }), {
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )
  );
});
