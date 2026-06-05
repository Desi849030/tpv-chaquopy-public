/**
 * tpv_storage.js - IndexedDB wrapper que reemplaza localStorage
 * Sin limite de 5MB, persistencia permanente, 100% offline.
 */
(function() {
    'use strict';
    var DB_NAME = 'tpv_keyvalue_store', DB_VERSION = 1, STORE_NAME = 'kv';
    var _db = null, _dbPromise = null, _cache = {};

    function _openDB() {
        if (_db) return Promise.resolve(_db);
        if (_dbPromise) return _dbPromise;
        _dbPromise = new Promise(function(resolve, reject) {
            var req = indexedDB.open(DB_NAME, DB_VERSION);
            req.onupgradeneeded = function(e) {
                var db = e.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME))
                    db.createObjectStore(STORE_NAME, { keyPath: 'key' });
            };
            req.onsuccess = function(e) { _db = e.target.result; resolve(_db); };
            req.onerror = function(e) { _dbPromise = null; reject(e.target.error); };
        });
        return _dbPromise;
    }

    function _loadAll() {
        return _openDB().then(function(db) {
            return new Promise(function(resolve) {
                var tx = db.transaction(STORE_NAME, 'readonly');
                var req = tx.objectStore(STORE_NAME).openCursor();
                req.onsuccess = function(e) {
                    var c = e.target.result;
                    if (c) { _cache[c.value.key] = c.value.value; c.continue(); }
                    else resolve();
                };
                req.onerror = function() { resolve(); };
            });
        }).catch(function() {});
    }

    function _put(key, val) {
        _openDB().then(function(db) {
            db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put({key:key, value:val});
        });
    }
    function _del(key) {
        _openDB().then(function(db) {
            db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(key);
        });
    }

    window.tpvStorage = {
        init: function() { return _loadAll(); },
        ready: false,
        getItem: function(k) { return (k in _cache) ? _cache[k] : null; },
        setItem: function(k, v) { _cache[k] = v; _put(k, v); },
        removeItem: function(k) { delete _cache[k]; _del(k); },
        getJSON: function(k) { var r = _cache[k]; if(r==null) return null; try{return JSON.parse(r);}catch(e){return null;} },
        setJSON: function(k, o) { var s = JSON.stringify(o); _cache[k] = s; _put(k, s); },
        keys: function(p) { var a = Object.keys(_cache); if(!p) return a; return a.filter(function(k){return k.indexOf(p)===0;}); },
        removeByPrefix: function(p) { this.keys(p).forEach(function(k){delete _cache[k];_del(k);}); },
        clear: function() { _cache = {}; _openDB().then(function(db){db.transaction(STORE_NAME,'readwrite').objectStore(STORE_NAME).clear();}); },
        migrateFromLocalStorage: function() {
            try { if(!window.localStorage) return; var m=0;
                for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k&&!(k in _cache)){_cache[k]=localStorage.getItem(k);_put(k,_cache[k]);m++;}}
                if(m>0) console.log('[tpvStorage] Migrados '+m+' keys desde localStorage');
            } catch(e){}
        }
    };

    tpvStorage.init().then(function() {
        tpvStorage.migrateFromLocalStorage();
        tpvStorage.ready = true;
        console.log('[tpvStorage] IndexedDB lista - ' + Object.keys(_cache).length + ' claves');
    });
})();
