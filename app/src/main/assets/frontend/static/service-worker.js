// Service Worker Desactivado para evitar caché de login
self.addEventListener('install', function(e) { self.skipWaiting(); });
self.addEventListener('activate', function(e) { 
    e.waitUntil(self.registration.unregister().then(() => self.clients.matchAll().then(clients => clients.forEach(c => c.navigate(c.url)))));
});
