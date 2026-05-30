self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).catch(() => {
      return new Response(JSON.stringify({offline: true}), {
        headers: {'Content-Type': 'application/json'}
      });
    })
  );
});
