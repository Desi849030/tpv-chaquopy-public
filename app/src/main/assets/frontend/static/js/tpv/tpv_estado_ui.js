// tpv_estado_ui.js -- Persistencia, helpers, tabs, config, licencia, mantenimiento
        // ==================== PERSISTENCIA DE DATOS OFFLINE ====================
        // 
        // ✅ DURACIÓN DE DATOS: PERMANENTE (sin límite de tiempo)
        // 
        // Los datos se guardan en IndexedDB del navegador, que persiste:
        // - ✅ Sin conexión a Internet (funciona 100% offline)
        // - ✅ Sin electricidad (mientras el dispositivo tenga batería)
        // - ✅ Indefinidamente (30 días, 90 días, años... sin límite)
        // - ✅ Incluso si cierras el navegador o reinicias el dispositivo
        // 
        // IMPORTANTE:
        // - Los datos SOLO se borran si:
        //   1. Desinstalas el navegador
        //   2. Limpias manualmente los datos del sitio
        //   3. Usas la función "Limpiar Todo" en Mantenimiento
        // 
        // - Para SEGURIDAD adicional:
        //   1. Exporta regularmente a Excel (Herramientas → Exportar Excel)
        //   2. Guarda copias de seguridad JSON (Herramientas → Exportar Backup)
        //   3. Estos archivos pueden guardarse en USB, tarjeta SD, etc.
        // 
        // RECOMENDACIÓN PARA 30+ DÍAS SIN CONEXIÓN:
        // - Exporta el Excel cada 7 días y guárdalo en almacenamiento externo
        // - Así tendrás respaldo incluso si algo pasa con el dispositivo
        // ========================================================================

        async function loadState() { 
            try { 
                const db = await dbHelper.openDb();
                let savedState = await dbHelper.load(db);
                db.close();

                // Si IndexedDB está vacío, intentar recuperar del servidor
                if (!savedState) {
                    try {
                        const res = await fetch('/api/state', { credentials: 'same-origin' });
                        if (res.ok) {
                            const data = await res.json();
                            if (data.ok && data.estado) {
                                savedState = data.estado;
                                console.log('📦 Estado recuperado del servidor');
                            }
                        }
                    } catch(e) { /* offline, continuar */ }
                }

                const defaultState = getDefaultState();
                const parsedState = savedState ?? defaultState;

                tpvState = {
                    ...defaultState,
                    ...parsedState,
                    licencia: { ...defaultState.licencia, ...(parsedState.licencia ?? {}) },
                    config: { ...defaultState.config, ...(parsedState.config ?? {}) },
                    nomencladores: { ...defaultState.nomencladores, ...(parsedState.nomencladores ?? {}) },
                    nomencladorCantidades: parsedState.nomencladorCantidades ?? defaultState.nomencladorCantidades,
                };

                if (!tpvState.licencia.clienteId) {
                    tpvState.licencia.clienteId = `TPV-${Date.now().toString().slice(-6)}`;
                }
                if (!tpvState.licencia.fechaActivacion) {
                    tpvState.licencia.fechaActivacion = new Date().toISOString();
                }

                // ── Sincronizar catálogo desde el servidor (fuente de verdad compartida) ──
                await catalogo_cargarDesdeServidor();

            } catch(e) { 
                console.error("Error loading state from IndexedDB, resetting to default.", e); 
                showToast(getLang().toast_error_load, 'danger'); 
                tpvState = getDefaultState(); 
            } 
        }

        /** Carga el catálogo del servidor y actualiza tpvState.productos para todos los roles */
        async function catalogo_cargarDesdeServidor() {
            try {
                const res = await fetch('/api/catalogo', { credentials: 'same-origin' });
                if (!res.ok) return;
                const data = await res.json();
                if (data.ok && Array.isArray(data.productos) && data.productos.length > 0) {
                    const localMap = {};
                    tpvState.productos.forEach(p => { localMap[p.id] = p; });
                    tpvState.productos = data.productos.map(sp => ({
                        ...(localMap[sp.id] || {}),
                        ...sp,
                    }));
                    const cats = [...new Set(tpvState.productos.map(p => p.categoria || 'General'))].sort();
                    if (cats.length) tpvState.categorias = cats;
                    console.log(`📦 Catálogo del servidor: ${data.productos.length} productos`);
                }
            } catch(e) {
                console.warn('⚠️ Catálogo local (sin servidor):', e.message);
            }
        }

        /** El admin sube su catálogo al servidor para que todos los roles lo vean */
        async function catalogo_sincronizarAlServidor() {
            try {
                const res = await fetch('/api/catalogo/sync', {
                    method: 'POST', credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productos: tpvState.productos })
                });
                if (res.ok) console.log('☁️ Catálogo sincronizado al servidor');
            } catch(e) {
                console.warn('⚠️ No se pudo sincronizar catálogo:', e.message);
            }
        }

        async function saveState() { 
            try { 
                const db = await dbHelper.openDb();
                await dbHelper.save(db, tpvState); 
                db.close();
            } catch (e) { 
                console.error("Error saving state to IndexedDB:", e); 
                showToast(getLang().toast_error_save, 'danger'); 
            } 
        }

        /** Persiste el estado en el servidor de forma explícita (solo llamar cuando sea intencional) */
        async function saveStateServidor() {
            try {
                await fetch('/api/state', {
                    method: 'POST', credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(tpvState)
                });
            } catch(e) { /* offline */ }
        }

        async function initializeUI() {
            addToCartModal = new bootstrap.Modal('#addToCartModal');
            processPaymentModal = new bootstrap.Modal('#processPaymentModal');
            editSaleModal = new bootstrap.Modal('#editSaleModal');
            gestionModalProducto = new bootstrap.Modal('#gestion-modal-producto');
            invModalStock = new bootstrap.Modal('#inv-modal-stock');
            gestionModalCategoria = new bootstrap.Modal('#gestion-modal-categoria');
            
            document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => tab.addEventListener('shown.bs.tab', handleTabChange));
            document.getElementById('conf-language-selector')?.addEventListener('change', (e) => conf_setLanguage(e.target.value));
            document.getElementById('conf-theme-toggle')?.addEventListener('change', (e) => conf_setTheme(e.target.checked ? 'dark' : 'light'));
            
            await refreshAllUI();
        }

        async function refreshAllUI() {
            const { config } = tpvState;
            document.getElementById('conf-language-selector') && (document.getElementById('conf-language-selector').value = config.lang);
            conf_setTheme(config.theme);
            document.getElementById('conf-theme-toggle') && (document.getElementById('conf-theme-toggle').checked = (config.theme === 'dark'));
            document.getElementById('inv-globalProfitPercent') && (document.getElementById('inv-globalProfitPercent').value = config.globalProfitPercent);
            if (typeof _actualizarBotonesLang === 'function') _actualizarBotonesLang(config.lang || 'es');
            conf_setLanguage(config.lang).catch(function(){});

            // Siempre recargar catálogo del servidor (fuente de verdad)
            await catalogo_cargarDesdeServidor();

            tpv_renderizarProductos();
            tpv_renderizarFiltroCategorias();
            tpv_renderizarPedido();
            gestion_renderizarFiltrosProductos();
            gestion_renderizarTablaProductos();
            gestion_renderizarListaCategorias();
            ventas_renderizarTablaHoy();
            registros_renderizar();
            document.getElementById('nom-selectPais') && nom_cargarDenominaciones(document.getElementById('nom-selectPais').value);
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
            lic_checkLicense();
            cliente_renderizarDropdownCategoriasQR(); 
            
            // Inicializar nuevas pestañas
            actualizar_lista_backups();
            mostrar_info_licencia();
            actualizar_logs();
            
            const _invFechaEl = document.getElementById('inv-fechaActual'); if (_invFechaEl) _invFechaEl.value = getTodayDateString();
            inv_cargarInventario(getTodayDateString());
        }

        // --- HELPERS ---
        const getLang = () => {
            // Verificación segura: si tpvState o config no existen, usar español por defecto
            if (!tpvState || !tpvState.config || !tpvState.config.lang) {
                return i18n.es;
            }
            return i18n[tpvState.config.lang] ?? i18n.es;
        };
        const formatCurrency = (amount) => `$${Number(amount ?? 0).toFixed(2)}`;
        const getTodayDateString = () => new Date().toISOString().split('T')[0];

        // --- LÓGICA DE ETIQUETAS DE PRODUCTO (QR) ---

        function handleTabChange(event) {
            const targetId = event.target.getAttribute('data-bs-target');
            document.querySelectorAll('.dropdown-item').forEach(item => item.classList.remove('active'));
            const dropdownItem = document.querySelector(`.dropdown-item[data-bs-target="${targetId}"]`);
            if (dropdownItem) dropdownItem.classList.add('active');

            const refreshMap = {
                '#ventas-hoy-tab-pane': ventas_renderizarTablaHoy,
                '#registros-tab-pane': registros_renderizar,
                '#gestion-productos-tab-pane': async () => {
                    await catalogo_cargarDesdeServidor();
                    gestion_renderizarFiltrosProductos();
                    // Limpiar filtros de precio por si quedaron valores anteriores
                    const pMin = document.getElementById('gestion-filtro-precio-min');
                    const pMax = document.getElementById('gestion-filtro-precio-max');
                    if (pMin) pMin.value = '';
                    if (pMax) pMax.value = '';
                    gestion_renderizarTablaProductos();
                },
                '#dashboard-tab-pane': () => {
                    if (typeof dashboard_cargar === 'function') dashboard_cargar();
                },
                '#herramientas-tab-pane': (e) => {
                    if (typeof descuentos_cargarLista   === 'function') descuentos_cargarLista();
                    if (typeof actualizar_lista_backups === 'function') actualizar_lista_backups();
                    const tid = e?.target?.id || document.querySelector('.dropdown-item.active')?.id;
                    const smap = {'importar-exportar-tab':'seccion-importar-excel','copias-seguridad-tab':'seccion-copias-seguridad','herramientas-tab':'seccion-mantenimiento'};
                    const sec = smap[tid];
                    if (sec) setTimeout(()=>document.getElementById(sec)?.scrollIntoView({behavior:'smooth',block:'start'}),200);
                },
                '#gestion-categorias-tab-pane': gestion_renderizarListaCategorias,
                '#tpv-caja-tab-pane': () => { tpv_renderizarProductos(); tpv_renderizarFiltroCategorias(); },
                '#cliente-qr-tab-pane': () => {
                    cliente_renderizarDropdownCategoriasQR();
                    cliente_generarEtiquetas();
                },
                '#inv-inventario-tab-pane': () => {
                    const rol = window.AUTH?.usuario?.rol;
                    if (['administrador','desarrollador'].includes(rol)) {
                        if (typeof _setup_admin_inventario === 'function') _setup_admin_inventario();
                        // Siempre recargar datos frescos al entrar al tab
                        const activeBtn = document.querySelector('#inv-admin-btns .btn-primary, #inv-admin-btns .btn-success, #inv-admin-btns .btn-warning');
                        const btnId = activeBtn?.id;
                        if (btnId === 'inv-btn-vendedores') {
                            _admin_invVista('vendedores');
                        } else if (btnId === 'inv-btn-gastos') {
                            _admin_invVista('gastos');
                        } else {
                            // Almacén general — siempre recargar desde servidor
                            window._adminGeneral = [];
                            window._adminVends   = [];
                            _admin_invVista('almacen');
                            // Forzar recarga del almacén desde la API
                            if (typeof _admin_cargarVendedores === 'function') {
                                _admin_invVista('vendedores');
                                setTimeout(() => _admin_invVista('almacen'), 50);
                            }
                        }
                    }
                }
            };
            refreshMap[targetId]?.(event);
        }

        function showToast(message, type = 'info') { 
            const container = document.querySelector(".toast-container");
            if (!container) return;
            const toastId = `toast-${Date.now()}`;
            const toastHTML = `<div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex"><div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
            container.insertAdjacentHTML("beforeend", toastHTML);
            const toastEl = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
            toast.show();
            toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
        }

        // --- LÓGICA DE CONFIGURACIÓN ---
        async function conf_setLanguage(lang) {
            tpvState.config.lang = lang;
            document.documentElement.lang = lang;
            const translations = getLang();
            
            try {
                document.querySelectorAll('[data-i18n]').forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    const translation = translations[key];
                    
                    if (typeof translation === 'function') {
                        if (key === 'license_trial') {
                           el.innerText = translation(lic_getRemainingDays());
                        }
                    } else if (translation !== undefined) {
                        el.innerText = translation;
                    }
                });

                document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                    const key = el.getAttribute('data-i18n-placeholder');
                    if (translations[key] !== undefined) {
                        el.placeholder = translations[key];
                    }
                });
            } catch (error) {
                console.error("Error al aplicar traducciones:", error);
            }

            // Actualizar el nombre del TPV después de cambiar idioma
            conf_updateTPVName();

            await saveState();
            cliente_renderizarDropdownCategoriasQR();
            if ((document.getElementById('cliente-qr-display-container')?.children.length > 0)) {
                cliente_generarEtiquetas();
            }
        }


        async function conf_setTheme(theme){
            tpvState.config.theme = theme;
            document.body.classList.toggle("dark-mode", theme === "dark");
            document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
            await saveState();
            const _qrCont = document.getElementById('cliente-qr-display-container');
            if (_qrCont && _qrCont.children.length > 0) {
                cliente_generarEtiquetas();
            }
        }

        // --- TPV (Catálogo y Orden) ---
        // Obtiene el stock actual de un producto desde el inventario de hoy
        async function lic_activateFromOverlay() {
            const key = document.getElementById("overlay-license-key").value.trim();
            const errorMsg = document.getElementById("overlay-error-message");
            const { clienteId } = tpvState.licencia;
            
            if(!key) {
                errorMsg.textContent = "Por favor, ingrese una clave de licencia.";
                errorMsg.classList.remove("d-none");
                return;
            }
            
            // Verificar clave administrativa
            const adminHash = await lic_sha256("admin" + getSecretKey());
            
            if(key === adminHash){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                tpvState.licencia.unidadTiempo = 'dias';
                await saveState();
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
                showToast("Licencia de administrador activada", "success");
                document.getElementById("overlay-license-key").value = "";
                errorMsg.classList.add("d-none");
                return;
            }
            
            // Verificar claves con duración personalizada
            let claveValida = false;
            let tiempoLicencia = 0;
            let unidadTiempo = 'dias';
            
            const duracionesPosibles = [
                { valor: 30, unidad: 'dias' },
                { valor: 60, unidad: 'dias' },
                { valor: 90, unidad: 'dias' },
                { valor: 180, unidad: 'dias' },
                { valor: 365, unidad: 'dias' },
                { valor: 730, unidad: 'dias' },
                { valor: 1, unidad: 'minutos' },
                { valor: 5, unidad: 'minutos' },
                { valor: 10, unidad: 'minutos' },
                { valor: 30, unidad: 'minutos' },
                { valor: 60, unidad: 'minutos' },
                { valor: 30, unidad: 'segundos' },
                { valor: 60, unidad: 'segundos' },
                { valor: 120, unidad: 'segundos' },
                { valor: 300, unidad: 'segundos' }
            ];
            
            for (const duracion of duracionesPosibles) {
                const validHash = await lic_sha256(clienteId + getSecretKey() + duracion.valor + duracion.unidad);
                if (key === validHash) {
                    claveValida = true;
                    tiempoLicencia = duracion.valor;
                    unidadTiempo = duracion.unidad;
                    break;
                }
            }
            
            if(claveValida){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.diasPrueba = tiempoLicencia;
                tpvState.licencia.unidadTiempo = unidadTiempo;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                await saveState();
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
                startLicenseAutoCheck(); // Reiniciar el auto-check con la nueva unidad
                const unidadTexto = unidadTiempo === 'dias' ? 'días' : unidadTiempo === 'minutos' ? 'minutos' : 'segundos';
                showToast(`Licencia activada (${tiempoLicencia} ${unidadTexto})`, "success");
                document.getElementById("overlay-license-key").value = "";
                errorMsg.classList.add("d-none");
            } else {
                errorMsg.textContent = "Clave incorrecta. Verifique que el ID y la clave sean correctos.";
                errorMsg.classList.remove("d-none");
            }
        }

        // --- FUNCIÓN PARA DESACTIVAR LICENCIA (ÚTIL PARA PRUEBAS) ---
        async function lic_deactivateLicense() {
            if(confirm("¿Está seguro que desea desactivar la licencia actual?\n\nEsto es útil para probar diferentes claves de licencia.")){
                tpvState.licencia.activada = false;
                tpvState.licencia.key = "";
                tpvState.licencia.fechaActivacion = null;
                await saveState();
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
                showToast("Licencia desactivada. Ahora puede probar otras claves.", "info");
                // Limpiar el campo de entrada
                document.getElementById("lic-key-input").value = "";
            }
        }

        // --- FUNCIÓN PARA GUARDAR NOMBRE PERSONALIZADO DEL TPV ---
        function conf_saveTPVName() {
            const nameInput = document.getElementById("tpv-name-input");
            const customName = nameInput.value.trim();
            
            if (!customName) {
                showToast("Por favor ingrese un nombre para el sistema TPV", "warning");
                return;
            }
            
            // Guardar en localStorage
            tpvStorage.setItem('tpv_custom_name', customName);
            
            // Actualizar el título en el header
            conf_updateTPVName();
            
            showToast("Nombre del TPV actualizado correctamente", "success");
        }

        // --- FUNCIÓN PARA ACTUALIZAR EL NOMBRE DEL TPV EN EL HEADER ---
        function conf_updateTPVName() {
            const customName = tpvStorage.getItem('tpv_custom_name');
            const nameElement = document.getElementById('tpv-custom-name');
            const lang = getLang();
            
            if (nameElement) {
                if (customName) {
                    nameElement.textContent = customName;
                } else {
                    // Usar el título por defecto según el idioma
                    nameElement.textContent = lang.app_title || 'Sistema TPV Profesional';
                }
            }
        }

        // --- FUNCIÓN PARA CARGAR EL NOMBRE GUARDADO AL INICIAR ---
        function conf_loadTPVName() {
            const customName = tpvStorage.getItem('tpv_custom_name');
            const nameInput = document.getElementById("tpv-name-input");
            
            if (customName) {
                if (nameInput) {
                    nameInput.value = customName;
                }
            }
            // Siempre actualizar el nombre (sea personalizado o por defecto)
            conf_updateTPVName();
        }

        // --- LÓGICA DE MANTENIMIENTO ---
        async function conf_limpiarVentasHoy() {
            const lang = getLang();
            if (confirm(lang.confirm_clear_today_sales)) {
                const hoy = getTodayDateString();
                const ventasHoy = tpvState.ventasDiarias[hoy] ?? [];
                
                ventasHoy.forEach(v => inv_actualizarStockPorVenta((document.getElementById("inv-fechaActual")?.value ?? getTodayDateString()), v.productoId, -v.cantidad));
                tpvState.historialVentas = tpvState.historialVentas.filter(v => !ventasHoy.map(vh => vh.id).includes(v.id));
                tpvState.ventasDiarias[hoy] = [];
                
                await saveState();
                ventas_renderizarTablaHoy();
                registros_renderizar();
                await inv_aplicarGananciaGlobal();
                showToast(lang.toast_today_sales_cleared, "success");
            }
        }

        async function conf_limpiarCierres() {
            const lang = getLang();
            if (confirm(lang.confirm_clear_closures)) {
                tpvState.cierresCaja = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_closures_cleared, "success");
            }
        }

        async function conf_limpiarHistorial() {
            const lang = getLang();
            if (confirm(lang.confirm_clear_history)) {
                tpvState.historialVentas = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_history_cleared, "success");
            }
        }

        async function conf_limpiarInventarios() {
            const lang = getLang();
            if (confirm(lang.confirm_clear_inventories)) {
                tpvState.inventarios = {};
                await saveState();
                inv_cargarInventario(getTodayDateString());
                showToast(lang.toast_inventories_cleared, "success");
            }
        }

        async function conf_limpiarTodo() {
            const lang = getLang();
            if (confirm(lang.confirm_clear_everything)) {
                const { productos, categorias, config, licencia } = tpvState; // Preserve essential data
                tpvState = getDefaultState(); // Reset
                tpvState = { ...tpvState, productos, categorias, config, licencia }; // Restore
                await saveState();
                await refreshAllUI();
                showToast(lang.toast_app_reset, "success");
            }
        }

        // updateNetworkStatus: actualiza badge + indicador offline
        function updateNetworkStatus(showToastMsg) {
            const isOnline = window._realOnline !== undefined ? window._realOnline : navigator.onLine;
            const indicator = document.getElementById('offline-indicator');
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            if (indicator) indicator.style.display = isOnline ? 'none' : 'block';
            if (statusBadge && statusText) {
                const icon = statusBadge.querySelector('i');
                statusBadge.classList.toggle('bg-success', isOnline);
                statusBadge.classList.toggle('bg-danger', !isOnline);
                statusBadge.classList.toggle('offline', !isOnline);
                if (icon) icon.className = isOnline ? 'bi bi-wifi' : 'bi bi-wifi-off';
                statusText.textContent = isOnline ? 'Online' : 'Offline';
            }
            // Siempre trackear wasOffline para detectar cambios
            if (isOnline && window.wasOffline) {
                window.wasOffline = false;
                if (showToastMsg) {
                    showToast('Conexión restaurada', 'success');
                    conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
                }
            } else if (!isOnline) {
                window.wasOffline = true;
                if (showToastMsg) {
                    showToast('Modo Offline — datos guardados localmente', 'warning');
                }
            }
        }
        
        window.addEventListener('load', function() {
            conf_loadTPVName();
            updateNetworkStatus();
            
            // Indicar estado actual en consola
            if (!navigator.onLine) {
                console.log('📴 Actualmente sin conexión - Todo funciona normalmente');
            } else {
                console.log('📶 Conectado a internet');
            }
            
            // Iniciar verificación automática de licencia para unidades pequeñas
            startLicenseAutoCheck();
        });
        

// Exportar funciones al scope global para WebView
window.loadState = loadState;
window.initializeUI = initializeUI;
window.refreshAllUI = refreshAllUI;
window.showToast = showToast;
window.conf_setLanguage = conf_setLanguage;
