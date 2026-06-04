/**
 * ============================================================
 *  TPV Ultra Smart v8.0 — Capa API (tpv_api.js)
 * ============================================================
 *
 *  Módulo API-first que reemplaza IndexedDB como fuente de datos
 *  principal del frontend TPV. Todas las lecturas van al backend
 *  Flask; si fallan, se recurre al caché local (memoria + IndexedDB).
 *
 *  Características:
 *  - Envoltura consistente para 120+ endpoints REST
 *  - Fallback offline: si la API no responde, lee de IndexedDB
 *  - Caché inteligente en memoria (TTL configurable) + IndexedDB
 *  - Cola de escritura: operaciones POST se encolan si no hay red
 *  - Auto-sync periódico para volcar la cola y refrescar datos
 *  - Detección automática de estado online/offline
 *
 *  Uso:
 *    await TPV_API.init();
 *    const productos = await TPV_API.catalogo.getAll();
 *    const venta = await TPV_API.ventas.registrar(items, 'efectivo', 'admin');
 *
 * ============================================================
 */

(function () {
    'use strict';

    // ────────────────────────────────────────────────────────────
    //  Configuración global
    // ────────────────────────────────────────────────────────────

    const CONFIG = {
        /** URL base del backend Flask */
        BASE_URL: window.TPV_CONFIG?.apiBase || window.TPV_CONFIG?.API_URL || '',

        /** Tiempo de vida del caché en memoria (ms). Por defecto 5 min */
        CACHE_TTL: 5 * 60 * 1000,

        /** TTL corto para datos que cambian seguido (ventas hoy, métricas) */
        CACHE_TTL_CORTO: 30 * 1000,

        /** Intervalo de auto-sync (ms). Por defecto cada 2 min */
        SYNC_INTERVAL: 2 * 60 * 1000,

        /** Intervalo de chequeo de salud (ms). Por defecto cada 5 min */
        HEALTH_INTERVAL: 5 * 60 * 1000,

        /** Timeout para peticiones fetch (ms) */
        FETCH_TIMEOUT: 15 * 1000,

        /** Nombre de la base de datos IndexedDB para caché */
        IDB_NAME: 'tpv_api_cache',

        /** Versión de IndexedDB */
        IDB_VERSION: 1,

        /** Nombre del store de caché en IndexedDB */
        IDB_STORE: 'cache',

        /** Nombre del store para la cola de escritura */
        IDB_QUEUE_STORE: 'write_queue',
    };

    // ────────────────────────────────────────────────────────────
    //  Estado interno
    // ────────────────────────────────────────────────────────────

    /** Caché en memoria: { clave: { datos, timestamp, ttl } } */
    const _cache = {};

    /** Estado de conexión */
    let _isOnline = navigator.onLine !== false;

    /** Cola de escrituras pendientes (se restaura de IndexedDB al init) */
    let _writeQueue = [];

    /** Temporizador de auto-sync */
    let _syncTimer = null;

    /** Temporizador de health-check */
    let _healthTimer = null;

    /** Bandera de inicialización */
    let _initialized = false;

    /** Último chequeo de salud */
    let _lastHealth = null;

    // ────────────────────────────────────────────────────────────
    //  Utilidades internas
    // ────────────────────────────────────────────────────────────

    /**
     * Genera una clave única de caché a partir de método + ruta + parámetros.
     * @param {string} metodo - GET, POST, etc.
     * @param {string} ruta   - Ruta del endpoint.
     * @param {object} [params] - Parámetros de query o body (se serializan).
     * @returns {string}
     */
    function _cacheKey(metodo, ruta, params) {
        const base = `${metodo}:${ruta}`;
        if (!params) return base;
        try {
            return `${base}:${JSON.stringify(params)}`;
        } catch {
            return base;
        }
    }

    /**
     * Recupera un valor del caché en memoria si no ha expirado.
     * @param {string} clave
     * @returns {*|null}
     */
    function _cacheGet(clave) {
        const entry = _cache[clave];
        if (!entry) return null;
        const edad = Date.now() - entry.timestamp;
        if (edad > entry.ttl) {
            delete _cache[clave];
            return null;
        }
        return entry.datos;
    }

    /**
     * Guarda un valor en el caché en memoria.
     * @param {string} clave
     * @param {*} datos
     * @param {number} [ttl] - TTL personalizado en ms.
     */
    function _cacheSet(clave, datos, ttl) {
        _cache[clave] = {
            datos,
            timestamp: Date.now(),
            ttl: ttl || CONFIG.CACHE_TTL,
        };
    }

    /**
     * Invalida entradas de caché que coincidan con un prefijo.
     * @param {string} prefijo - Ej: 'GET:/api/catalogo'
     */
    function _cacheInvalidate(prefijo) {
        Object.keys(_cache).forEach((k) => {
            if (k.startsWith(prefijo)) delete _cache[k];
        });
    }

    /**
     * Abre (o crea) la base de datos IndexedDB de caché.
     * @returns {Promise<IDBDatabase>}
     */
    function _abrirIDB() {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open(CONFIG.IDB_NAME, CONFIG.IDB_VERSION);
            req.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains(CONFIG.IDB_STORE)) {
                    db.createObjectStore(CONFIG.IDB_STORE, { keyPath: 'clave' });
                }
                if (!db.objectStoreNames.contains(CONFIG.IDB_QUEUE_STORE)) {
                    db.createObjectStore(CONFIG.IDB_QUEUE_STORE, {
                        keyPath: 'id',
                        autoIncrement: true,
                    });
                }
            };
            req.onsuccess = (e) => resolve(e.target.result);
            req.onerror = (e) => reject(e.target.error);
        });
    }

    /**
     * Lee un valor del caché en IndexedDB.
     * @param {string} clave
     * @returns {Promise<*|null>}
     */
    async function _idbGet(clave) {
        try {
            const db = await _abrirIDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(CONFIG.IDB_STORE, 'readonly');
                const store = tx.objectStore(CONFIG.IDB_STORE);
                const req = store.get(clave);
                req.onsuccess = () => {
                    const entry = req.result;
                    if (!entry) return resolve(null);
                    // Verificar TTL en IndexedDB también
                    const edad = Date.now() - (entry.timestamp || 0);
                    if (edad > (entry.ttl || CONFIG.CACHE_TTL)) {
                        // Expirado — lo borramos y devolvemos null
                        const txDel = db.transaction(CONFIG.IDB_STORE, 'readwrite');
                        txDel.objectStore(CONFIG.IDB_STORE).delete(clave);
                        resolve(null);
                    } else {
                        resolve(entry.datos);
                    }
                };
                req.onerror = () => reject(req.error);
            });
        } catch {
            return null;
        }
    }

    /**
     * Guarda un valor en el caché de IndexedDB.
     * @param {string} clave
     * @param {*} datos
     * @param {number} [ttl]
     */
    async function _idbSet(clave, datos, ttl) {
        try {
            const db = await _abrirIDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(CONFIG.IDB_STORE, 'readwrite');
                const store = tx.objectStore(CONFIG.IDB_STORE);
                store.put({
                    clave,
                    datos,
                    timestamp: Date.now(),
                    ttl: ttl || CONFIG.CACHE_TTL,
                });
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            });
        } catch {
            /* silenciar errores de escritura en caché */
        }
    }

    /**
     * Persiste la cola de escritura en IndexedDB para sobrevivir recargas.
     */
    async function _persistirCola() {
        try {
            const db = await _abrirIDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(CONFIG.IDB_QUEUE_STORE, 'readwrite');
                const store = tx.objectStore(CONFIG.IDB_QUEUE_STORE);
                // Limpiar store existente
                store.clear();
                // Escribir todos los elementos de la cola
                _writeQueue.forEach((item) => {
                    store.add(item);
                });
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            });
        } catch {
            /* silenciar */
        }
    }

    /**
     * Restaura la cola de escritura desde IndexedDB.
     */
    async function _restaurarCola() {
        try {
            const db = await _abrirIDB();
            return new Promise((resolve, reject) => {
                const tx = db.transaction(CONFIG.IDB_QUEUE_STORE, 'readonly');
                const store = tx.objectStore(CONFIG.IDB_QUEUE_STORE);
                const req = store.getAll();
                req.onsuccess = () => {
                    _writeQueue = req.result || [];
                    resolve();
                };
                req.onerror = () => reject(req.error);
            });
        } catch {
            _writeQueue = [];
        }
    }

    // ────────────────────────────────────────────────────────────
    //  Núcleo de peticiones HTTP
    // ────────────────────────────────────────────────────────────

    /**
     * Realiza una petición fetch con timeout y manejo consistente.
     *
     * @param {string} ruta    - Ruta relativa del endpoint (ej: '/api/catalogo')
     * @param {object} [opciones] - Opciones de fetch (method, body, headers, etc.)
     * @returns {Promise<{ok: boolean, data: *, status: number}>}
     */
    async function _fetch(ruta, opciones = {}) {
        const url = CONFIG.BASE_URL + ruta;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT);

        const fetchOpts = {
            ...opciones,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
                ...(opciones.headers || {}),
            },
        };

        // Si hay body y es objeto, serializar a JSON
        if (fetchOpts.body && typeof fetchOpts.body === 'object') {
            fetchOpts.body = JSON.stringify(fetchOpts.body);
        }

        try {
            const resp = await fetch(url, fetchOpts);
            clearTimeout(timeoutId);

            // Intentar parsear JSON; si falla, devolver texto
            let data;
            const contentType = resp.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                data = await resp.json();
            } else {
                const text = await resp.text();
                try {
                    data = JSON.parse(text);
                } catch {
                    data = { ok: false, error: text };
                }
            }

            return {
                ok: resp.ok,
                status: resp.status,
                data,
            };
        } catch (err) {
            clearTimeout(timeoutId);

            // Si fue abort por timeout
            if (err.name === 'AbortError') {
                console.warn(`[TPV_API] Timeout en ${ruta}`);
                return {
                    ok: false,
                    status: 0,
                    data: { ok: false, error: 'Timeout de conexión' },
                };
            }

            // Error de red (sin conexión)
            console.warn(`[TPV_API] Error de red en ${ruta}:`, err.message);
            return {
                ok: false,
                status: 0,
                data: { ok: false, error: err.message || 'Error de conexión' },
            };
        }
    }

    /**
     * Petición GET con estrategia de caché + fallback.
     *
     * Flujo:
     *  1. Si hay en caché en memoria y no expiró → devolver de caché
     *  2. Si la API responde OK → guardar en caché y devolver
     *  3. Si la API falla → intentar caché en IndexedDB
     *  4. Si no hay nada → devolver respuesta de error
     *
     * @param {string} ruta
     * @param {object} [opciones] - { ttl, params, cacheKey }
     * @returns {Promise<*>}
     */
    async function _get(ruta, opciones = {}) {
        const clave = opciones.cacheKey || _cacheKey('GET', ruta, opciones.params);

        // 1. Caché en memoria
        const memHit = _cacheGet(clave);
        if (memHit !== null) return memHit;

        // 2. Intentar API
        if (_isOnline) {
            let url = ruta;
            if (opciones.params) {
                const qs = new URLSearchParams(opciones.params).toString();
                url += (url.includes('?') ? '&' : '?') + qs;
            }

            const result = await _fetch(url, { method: 'GET' });

            if (result.ok && result.data && result.data.ok !== false) {
                const datos = result.data;
                const ttl = opciones.ttl || CONFIG.CACHE_TTL;
                _cacheSet(clave, datos, ttl);
                // Persistir en IndexedDB como respaldo
                _idbSet(clave, datos, ttl);
                return datos;
            }

            // API respondió pero con error de negocio — igual intentar caché
            if (result.ok) return result.data;
        }

        // 3. Fallback a IndexedDB
        const idbHit = await _idbGet(clave);
        if (idbHit !== null) {
            console.log(`[TPV_API] Fallback IDB para ${ruta}`);
            _cacheSet(clave, idbHit); // Promover a memoria
            return idbHit;
        }

        // 4. No hay datos disponibles
        return { ok: false, error: 'Sin conexión y sin datos en caché' };
    }

    /**
     * Petición POST con cola de escritura offline.
     *
     * Flujo:
     *  1. Si estamos online → enviar al servidor
     *  2. Si el servidor responde OK → invalidar cachés afectados y devolver
     *  3. Si estamos offline o la petición falla → encolar para replay
     *
     * @param {string} ruta
     * @param {object} body   - Cuerpo de la petición
     * @param {object} [opciones] - { invalidarCache: [prefijos], metodo }
     * @returns {Promise<*>}
     */
    async function _post(ruta, body, opciones = {}) {
        const metodo = opciones.metodo || 'POST';

        // Si estamos online, intentar enviar directamente
        if (_isOnline) {
            const result = await _fetch(ruta, {
                method: metodo,
                body,
            });

            if (result.ok) {
                // Invalidar cachés afectados
                if (opciones.invalidarCache) {
                    opciones.invalidarCache.forEach((prefijo) => _cacheInvalidate(prefijo));
                }
                return result.data;
            }

            // Si es error 4xx (bad request, unauthorized, etc.), NO encolar
            if (result.status >= 400 && result.status < 500) {
                return result.data;
            }
        }

        // Encolar para replay posterior
        const entrada = {
            ruta,
            metodo,
            body,
            opciones,
            timestamp: Date.now(),
            intentos: 0,
        };
        _writeQueue.push(entrada);
        await _persistirCola();

        console.log(`[TPV_API] Escritura encolada: ${metodo} ${ruta} (cola: ${_writeQueue.length})`);

        // Invalidar cachés para que la siguiente lectura vaya al servidor
        if (opciones.invalidarCache) {
            opciones.invalidarCache.forEach((prefijo) => _cacheInvalidate(prefijo));
        }

        return {
            ok: true,
            encolado: true,
            mensaje: 'Operación encolada — se enviará al recuperar conexión',
        };
    }

    // ────────────────────────────────────────────────────────────
    //  Cola de escritura y auto-sync
    // ────────────────────────────────────────────────────────────

    /**
     * Procesa la cola de escrituras pendientes, enviándolas al servidor.
     * Se llama automáticamente al recuperar conexión y periódicamente.
     *
     * @returns {Promise<{procesados: number, fallidos: number}>}
     */
    async function _flushQueue() {
        if (_writeQueue.length === 0) return { procesados: 0, fallidos: 0 };

        if (!_isOnline) {
            console.log('[TPV_API] Flush omitido — sin conexión');
            return { procesados: 0, fallidos: 0 };
        }

        console.log(`[TPV_API] Procesando cola de escritura (${_writeQueue.length} elementos)...`);

        let procesados = 0;
        let fallidos = 0;
        const pendientes = [..._writeQueue];
        _writeQueue = [];

        for (const entrada of pendientes) {
            entrada.intentos = (entrada.intentos || 0) + 1;

            try {
                const result = await _fetch(entrada.ruta, {
                    method: entrada.metodo,
                    body: entrada.body,
                });

                if (result.ok) {
                    procesados++;
                    // Invalidar cachés asociados
                    if (entrada.opciones && entrada.opciones.invalidarCache) {
                        entrada.opciones.invalidarCache.forEach((prefijo) => _cacheInvalidate(prefijo));
                    }
                    console.log(`[TPV_API] Cola OK: ${entrada.metodo} ${entrada.ruta}`);
                } else {
                    // Si falla por error de servidor, re-encolar con límite
                    if (entrada.intentos < 5) {
                        _writeQueue.push(entrada);
                    } else {
                        console.error(
                            `[TPV_API] Descartando tras ${entrada.intentos} intentos: ${entrada.ruta}`
                        );
                        fallidos++;
                    }
                }
            } catch {
                if (entrada.intentos < 5) {
                    _writeQueue.push(entrada);
                } else {
                    fallidos++;
                }
            }
        }

        await _persistirCola();

        const resumen = { procesados, fallidos };
        console.log('[TPV_API] Flush completado:', resumen);
        return resumen;
    }

    /**
     * Ciclo de auto-sync: refresca datos clave y procesa la cola.
     */
    async function _autoSync() {
        if (!_isOnline || !_initialized) return;

        try {
            // Procesar cola de escrituras
            await _flushQueue();

            // Refrescar datos críticos (invalidar caché corto para forzar re-lectura)
            _cacheInvalidate('GET:/api/metrics');
            _cacheInvalidate('GET:/api/ventas/hoy');
            _cacheInvalidate('GET:/api/ventas/totales');
            _cacheInvalidate('GET:/api/notificaciones');
            _cacheInvalidate('GET:/api/reportes/resumen');

            // Pre-cargar datos clave en segundo plano
            await Promise.allSettled([
                TPV_API.metricas.getDashboard(),
                TPV_API.ventas.getTotales(),
            ]);
        } catch (err) {
            console.warn('[TPV_API] Error en auto-sync:', err);
        }
    }

    /**
     * Chequeo de salud periódico del backend.
     */
    async function _healthCheck() {
        try {
            const result = await _fetch('/api/health', { method: 'GET' });
            const estabaOffline = !_isOnline;

            if (result.ok) {
                _isOnline = true;
                _lastHealth = result.data;

                // Si recuperamos conexión, procesar cola
                if (estabaOffline) {
                    console.log('[TPV_API] Conexión recuperada — procesando cola...');
                    await _flushQueue();
                }
            } else {
                _isOnline = false;
            }
        } catch {
            _isOnline = false;
        }
    }

    // ────────────────────────────────────────────────────────────
    //  Detección de estado online/offline
    // ────────────────────────────────────────────────────────────

    function _setupOnlineDetection() {
        window.addEventListener('online', async () => {
            console.log('[TPV_API] Evento: online');
            _isOnline = true;
            await _flushQueue();
            // Refrescar datos al recuperar conexión
            _cacheInvalidate('GET:');
        });

        window.addEventListener('offline', () => {
            console.log('[TPV_API] Evento: offline');
            _isOnline = false;
        });
    }

    // ────────────────────────────────────────────────────────────
    //  Módulo de Autenticación
    // ────────────────────────────────────────────────────────────

    const auth = {
        /**
         * Inicia sesión con credenciales.
         * @param {string} username
         * @param {string} password
         * @returns {Promise<{ok, usuario}>}
         */
        async login(username, password) {
            const result = await _post('/api/auth/login', { username, password }, {
                invalidarCache: ['GET:/api/auth/me', 'GET:/api/admin/privilegios'],
            });
            return result;
        },

        /**
         * Cierra la sesión actual.
         * @returns {Promise<{ok}>}
         */
        async logout() {
            const result = await _post('/api/auth/logout', {});
            // Limpiar cachés sensibles al cerrar sesión
            _cacheInvalidate('GET:');
            return result;
        },

        /**
         * Obtiene información del usuario autenticado.
         * @returns {Promise<{autenticado, usuario}>}
         */
        async me() {
            return _get('/api/auth/me', { ttl: CONFIG.CACHE_TTL_CORTO });
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Catálogo / Productos
    // ────────────────────────────────────────────────────────────

    /** Caché local de productos para búsquedas rápidas */
    let _productosCache = null;

    const catalogo = {
        /**
         * Obtiene todos los productos del catálogo.
         * Primero intenta la API; si falla, recurre al caché.
         * @returns {Promise<{ok, productos, total, categorias}>}
         */
        async getAll() {
            const result = await _get('/api/catalogo', {
                cacheKey: 'GET:/api/catalogo',
            });
            // Actualizar caché local para búsquedas
            if (result && result.ok && result.productos) {
                _productosCache = result.productos;
            }
            return result;
        },

        /**
         * Filtra productos por categoría (búsqueda en lado cliente).
         * @param {string} categoria
         * @returns {Promise<Array>}
         */
        async getByCategory(categoria) {
            const data = await this.getAll();
            const productos = data?.productos || _productosCache || [];
            return productos.filter((p) => p.categoria === categoria);
        },

        /**
         * Busca productos por nombre o código (búsqueda en lado cliente).
         * @param {string} query - Texto de búsqueda
         * @returns {Promise<Array>}
         */
        async search(query) {
            const data = await this.getAll();
            const productos = data?.productos || _productosCache || [];
            if (!query) return productos;

            const q = query.toLowerCase().trim();
            return productos.filter(
                (p) =>
                    (p.nombre && p.nombre.toLowerCase().includes(q)) ||
                    (p.codigo && p.codigo.toLowerCase().includes(q)) ||
                    (p.categoria && p.categoria.toLowerCase().includes(q))
            );
        },

        /**
         * Importa productos desde un array (Excel, etc.).
         * @param {Array} productos - Lista de productos a importar
         * @returns {Promise<{ok, importados, actualizados}>}
         */
        async importarExcel(productos) {
            return _post('/api/importar/excel', { productos }, {
                invalidarCache: ['GET:/api/catalogo', 'GET:/api/inventario/general', 'GET:/api/metrics'],
            });
        },

        /**
         * Previsualiza una importación de productos.
         * @param {Array} productos
         * @returns {Promise<*>}
         */
        async previsualizarImportacion(productos) {
            return _post('/api/importar/previsualizar', { productos });
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Ventas
    // ────────────────────────────────────────────────────────────

    const ventas = {
        /**
         * Registra una nueva venta.
         * @param {Array} items - [{id, nombre, cantidad, precio}]
         * @param {string} metodoPago - 'efectivo', 'tarjeta', 'transferencia', etc.
         * @param {string} vendedor - Nombre del vendedor
         * @returns {Promise<{ok, venta_id, total, items, fecha}>}
         */
        async registrar(items, metodoPago, vendedor) {
            return _post('/api/ventas/registrar', {
                items,
                metodo_pago: metodoPago,
                vendedor,
            }, {
                invalidarCache: [
                    'GET:/api/ventas/hoy',
                    'GET:/api/ventas/totales',
                    'GET:/api/metrics',
                    'GET:/api/reportes/resumen',
                    'GET:/api/inventario/general',
                    'GET:/api/catalogo',
                    'GET:/api/notificaciones',
                ],
            });
        },

        /**
         * Obtiene las ventas del día actual.
         * @returns {Promise<{ok, ventas, total, cantidad}>}
         */
        async getHoy() {
            return _get('/api/ventas/hoy', { ttl: CONFIG.CACHE_TTL_CORTO });
        },

        /**
         * Obtiene los cierres de caja.
         * @returns {Promise<{ok, cierres}>}
         */
        async getCierres() {
            return _get('/api/ventas/cierres');
        },

        /**
         * Realiza el cierre de caja.
         * @param {string} fecha - Fecha del cierre (YYYY-MM-DD)
         * @param {string} cerradoPor - Nombre de quien cierra
         * @returns {Promise<{ok, fecha, total_ventas, num_transacciones}>}
         */
        async cerrarCaja(fecha, cerradoPor) {
            return _post('/api/ventas/cierre', {
                fecha,
                cerrado_por: cerradoPor,
            }, {
                invalidarCache: [
                    'GET:/api/ventas/hoy',
                    'GET:/api/ventas/totales',
                    'GET:/api/ventas/cierres',
                    'GET:/api/metrics',
                ],
            });
        },

        /**
         * Obtiene totales de ventas (hoy y mes).
         * @returns {Promise<{ok, hoy, mes}>}
         */
        async getTotales() {
            return _get('/api/ventas/totales', { ttl: CONFIG.CACHE_TTL_CORTO });
        },

        /**
         * Obtiene reporte de ventas por rango de fechas.
         * @param {string} desde - Fecha inicio (YYYY-MM-DD)
         * @param {string} hasta - Fecha fin (YYYY-MM-DD)
         * @returns {Promise<{ok, ventas, total, cantidad}>}
         */
        async getReporte(desde, hasta) {
            return _get('/api/reportes/ventas', {
                params: { desde, hasta },
            });
        },

        /**
         * Exporta reporte de ventas como CSV.
         * @param {string} desde
         * @param {string} hasta
         * @returns {Promise<string>} - Contenido CSV
         */
        async exportarReporte(desde, hasta) {
            // Esta petición devuelve CSV, no JSON — usar fetch directo
            try {
                const url = `${CONFIG.BASE_URL}/api/reportes/exportar?desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`;
                const resp = await fetch(url);
                if (resp.ok) return await resp.text();
                return null;
            } catch {
                return null;
            }
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Inventario
    // ────────────────────────────────────────────────────────────

    const inventario = {
        /**
         * Obtiene el inventario general con stock actual.
         * @returns {Promise<{ok, inventario, total}>}
         */
        async getGeneral() {
            return _get('/api/inventario/general');
        },

        /**
         * Obtiene el inventario diario para una fecha específica.
         * @param {string} fecha - Fecha (YYYY-MM-DD)
         * @returns {Promise<{ok, fecha, inventario, conteo}>}
         */
        async getDiario(fecha) {
            return _get(`/api/inventario/diario/${encodeURIComponent(fecha)}`);
        },

        /**
         * Importa el catálogo al inventario.
         * @returns {Promise<{ok, nuevos, existentes}>}
         */
        async importarCatalogo() {
            return _post('/api/inventario/importar-catalogo', {}, {
                invalidarCache: ['GET:/api/inventario/general', 'GET:/api/catalogo'],
            });
        },

        /**
         * Actualización masiva de stock.
         * @param {Array} updates - Lista de actualizaciones de stock
         * @returns {Promise<*>}
         */
        async actualizarStockMasivo(updates) {
            return _post('/api/stock/masivo', { updates }, {
                invalidarCache: [
                    'GET:/api/inventario/general',
                    'GET:/api/catalogo',
                    'GET:/api/metrics',
                    'GET:/api/notificaciones',
                ],
            });
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Métricas y Dashboard
    // ────────────────────────────────────────────────────────────

    const metricas = {
        /**
         * Obtiene métricas del dashboard principal.
         * @returns {Promise<{ok, ventas_hoy, ingresos_hoy, ingresos_mes, productos, ganancia_hoy, top_producto}>}
         */
        async getDashboard() {
            return _get('/api/metrics', { ttl: CONFIG.CACHE_TTL_CORTO });
        },

        /**
         * Obtiene el resumen general del negocio.
         * @returns {Promise<{ok, resumen}>}
         */
        async getResumen() {
            return _get('/api/reportes/resumen', { ttl: CONFIG.CACHE_TTL_CORTO });
        },

        /**
         * Obtiene las notificaciones activas.
         * @returns {Promise<{ok, notificaciones, total}>}
         */
        async getNotificaciones() {
            return _get('/api/notificaciones', { ttl: CONFIG.CACHE_TTL_CORTO });
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Herramientas (AI / Análisis)
    // ────────────────────────────────────────────────────────────

    const herramientas = {
        /**
         * Obtiene resumen financiero inteligente.
         * @returns {Promise<{ok, ventas_hoy, productos, margen_promedio, ganancia_estimada}>}
         */
        async getFinanzas() {
            return _get('/api/tools/finanzas');
        },

        /**
         * Obtiene análisis de stock con productos críticos.
         * @returns {Promise<{ok, total, criticos, productos}>}
         */
        async getStock() {
            return _get('/api/tools/stock');
        },

        /**
         * Obtiene recomendaciones del sistema.
         * @returns {Promise<{ok, recomendaciones}>}
         */
        async getRecomendar() {
            return _get('/api/tools/recomendar');
        },

        /**
         * Obtiene predicciones de ventas.
         * @returns {Promise<{ok, prediccion}>}
         */
        async getPrediccion() {
            return _get('/api/tools/prediccion');
        },

        /**
         * Obtiene análisis ABC de productos.
         * @returns {Promise<{ok, analisis}>}
         */
        async getABC() {
            return _get('/api/tools/abc');
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Administración
    // ────────────────────────────────────────────────────────────

    const admin = {
        /**
         * Obtiene privilegios y permisos por rol.
         * @param {string} [rol] - Rol a consultar
         * @returns {Promise<{ok, jerarquia, permisos_por_rol, puede_crear, usuarios}>}
         */
        async getPrivilegios(rol) {
            const params = rol ? { rol } : undefined;
            return _get('/api/admin/privilegios', { params });
        },

        /**
         * Crea un nuevo usuario.
         * @param {object} data - {username, password, nombre, rol}
         * @returns {Promise<*>}
         */
        async crearUsuario(data) {
            return _post('/api/admin/usuarios/crear', data, {
                invalidarCache: ['GET:/api/admin/privilegios'],
            });
        },

        /**
         * Activa o desactiva un usuario.
         * @param {string|number} uid - ID del usuario
         * @param {boolean} activo - Nuevo estado
         * @returns {Promise<*>}
         */
        async toggleUsuario(uid, activo) {
            return _post(`/api/admin/usuarios/${encodeURIComponent(uid)}/toggle`, { activo }, {
                metodo: 'PUT',
                invalidarCache: ['GET:/api/admin/privilegios'],
            });
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Clientes
    // ────────────────────────────────────────────────────────────

    const clientes = {
        /**
         * Registra un nuevo cliente.
         * @param {object} data - {nombre, telefono, email}
         * @returns {Promise<*>}
         */
        async registrar(data) {
            return _post('/api/clientes/registrar', data);
        },

        /**
         * Obtiene todos los clientes.
         * @returns {Promise<{ok, clientes}>}
         */
        async getAll() {
            return _get('/api/clientes');
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Backup
    // ────────────────────────────────────────────────────────────

    const backup = {
        /**
         * Crea un backup de la base de datos.
         * @returns {Promise<{ok, backup, size}>}
         */
        async crear() {
            return _post('/api/db/backup', {});
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Seguridad
    // ────────────────────────────────────────────────────────────

    const seguridad = {
        /**
         * Ejecuta chequeos de seguridad.
         * @returns {Promise<*>}
         */
        async check() {
            return _get('/api/seguridad/check');
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Licencias
    // ────────────────────────────────────────────────────────────

    const licencias = {
        /**
         * Obtiene el estado de la licencia actual.
         * @returns {Promise<{ok, activa, tipo, expiracion, dias_restantes}>}
         */
        async getEstado() {
            return _get('/api/licencias/estado');
        },

        /**
         * Obtiene todas las licencias.
         * @returns {Promise<{ok, licencias, activa, tipo, dias_restantes}>}
         */
        async getAll() {
            return _get('/api/licencias');
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo de Agente IA
    // ────────────────────────────────────────────────────────────

    const agente = {
        /**
         * Envía un mensaje al agente IA.
         * @param {string} mensaje - Mensaje del usuario
         * @param {string} [rol] - Rol del usuario
         * @param {string} [nombre] - Nombre del usuario
         * @returns {Promise<{ok, respuesta, intencion, confianza, herramientas}>}
         */
        async chat(mensaje, rol, nombre) {
            return _post('/api/agent/chat', { mensaje, rol, nombre });
        },

        /**
         * Obtiene el estado del agente IA.
         * @returns {Promise<{ok, agent, version}>}
         */
        async status() {
            return _get('/api/agent/status');
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Módulo QR
    // ────────────────────────────────────────────────────────────

    const qr = {
        /**
         * Obtiene datos QR de un producto.
         * @param {string|number} productoId
         * @returns {Promise<{ok, qr_data}>}
         */
        async get(productoId) {
            return _get(`/api/qr/${encodeURIComponent(productoId)}`);
        },
    };

    // ────────────────────────────────────────────────────────────
    //  Funciones globales
    // ────────────────────────────────────────────────────────────

    /**
     * Chequeo de salud del backend.
     * @returns {Promise<{status, version, db}>}
     */
    async function health() {
        const result = await _get('/api/health', { ttl: CONFIG.CACHE_TTL_CORTO });
        return result;
    }

    /**
     * Inicializa el módulo API:
     *  - Configura detección online/offline
     *  - Restaura la cola de escritura desde IndexedDB
     *  - Verifica conexión con el backend
     *  - Precarga datos esenciales
     *  - Inicia auto-sync periódico
     *
     * @returns {Promise<{online: boolean, health: *}>}
     */
    async function init() {
        if (_initialized) {
            console.log('[TPV_API] Ya inicializado — omitiendo');
            return { online: _isOnline, health: _lastHealth };
        }

        console.log('[TPV_API] Inicializando capa API...');

        // 1. Configurar detección de red
        _setupOnlineDetection();

        // 2. Restaurar cola de escritura pendiente
        await _restaurarCola();
        console.log(`[TPV_API] Cola restaurada: ${_writeQueue.length} escrituras pendientes`);

        // 3. Verificar conexión con el backend
        try {
            const healthResult = await _fetch('/api/health', { method: 'GET' });
            _isOnline = healthResult.ok;
            _lastHealth = healthResult.data;
            console.log('[TPV_API] Backend:', _isOnline ? 'EN LÍNEA' : 'NO DISPONIBLE');
        } catch {
            _isOnline = false;
            console.log('[TPV_API] Backend: NO DISPONIBLE (inicialización)');
        }

        // 4. Si estamos online, procesar cola y precargar datos
        if (_isOnline) {
            // Procesar cola de escrituras pendientes
            await _flushQueue();

            // Precargar datos esenciales en segundo plano
            console.log('[TPV_API] Precargando datos esenciales...');
            await Promise.allSettled([
                catalogo.getAll(),
                metricas.getDashboard(),
                ventas.getTotales(),
            ]);
            console.log('[TPV_API] Datos esenciales precargados');
        }

        // 5. Iniciar auto-sync periódico
        _syncTimer = setInterval(_autoSync, CONFIG.SYNC_INTERVAL);

        // 6. Iniciar health-check periódico
        _healthTimer = setInterval(_healthCheck, CONFIG.HEALTH_INTERVAL);

        _initialized = true;
        console.log('[TPV_API] ✅ Inicialización completada');

        return { online: _isOnline, health: _lastHealth };
    }

    /**
     * Detiene los temporizadores y limpia recursos.
     */
    function destroy() {
        if (_syncTimer) clearInterval(_syncTimer);
        if (_healthTimer) clearInterval(_healthTimer);
        _syncTimer = null;
        _healthTimer = null;
        _initialized = false;
        console.log('[TPV_API] Módulo detenido');
    }

    /**
     * Fuerza una invalidación completa del caché.
     * Útil tras operaciones críticas (cierre de caja, importación masiva).
     */
    function clearCache() {
        Object.keys(_cache).forEach((k) => delete _cache[k]);
        _productosCache = null;
        console.log('[TPV_API] Caché en memoria limpiado');
    }

    /**
     * Devuelve información de diagnóstico del módulo.
     * @returns {object}
     */
    function diagnostico() {
        return {
            inicializado: _initialized,
            online: _isOnline,
            colaPendientes: _writeQueue.length,
            entradasCache: Object.keys(_cache).length,
            ultimoHealth: _lastHealth,
            productosEnCache: _productosCache ? _productosCache.length : 0,
            config: { ...CONFIG },
        };
    }

    // ────────────────────────────────────────────────────────────
    //  Registro global: window.TPV_API
    // ────────────────────────────────────────────────────────────

    window.TPV_API = {
        // Inicialización y ciclo de vida
        init,
        destroy,

        // Módulos de dominio
        auth,
        catalogo,
        ventas,
        inventario,
        metricas,
        herramientas,
        admin,
        clientes,
        backup,
        seguridad,
        licencias,
        agente,
        qr,

        // Funciones globales
        health,

        // Utilidades
        clearCache,
        diagnostico,

        // Acceso directo al estado interno (solo lectura vía diagnóstico)
        get _cache() { return _cache; },
        get _isOnline() { return _isOnline; },
        get _writeQueue() { return [..._writeQueue]; },
        _flushQueue,

        // Configuración (modificable antes de init)
        CONFIG,
    };

    console.log('[TPV_API] Módulo registrado en window.TPV_API');
})();
