const SYNC_QUEUE_KEY = 'tpv_offline_sync_queue';
window.tpvSyncManager = {
    getQueue: () => JSON.parse(localStorage.getItem(SYNC_QUEUE_KEY) || '[]'),
    addToQueue: async (url, options) => {
        const q = window.tpvSyncManager.getQueue();
        q.push({url, method: options.method||'GET', body: options.body?JSON.parse(options.body):null, timestamp: Date.now()});
        localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(q));
        return { ok: false, offline: true, message: 'Sincronización pendiente' };
    },
    processQueue: async () => {
        const q = window.tpvSyncManager.getQueue();
        if(!q.length) return;
        const remaining = [];
        for(const r of q) {
            try { await fetch(r.url, {method: r.method, headers:{'Content-Type':'application/json'}, body: r.body?JSON.stringify(r.body):null}); }
            catch(e) { remaining.push(r); }
        }
        localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(remaining));
    }
};
window.addEventListener('online', () => { window.tpvSyncManager.processQueue(); });
