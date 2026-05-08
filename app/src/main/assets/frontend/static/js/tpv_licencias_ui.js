/**
 * tpv_licencias_ui.js — TPV ULTRA SMART v5.0
 * Licencias: activar, verificar, auto-actualizacion
 * Extraido de script_5.js
 */

                // ===== LICENCIAS =====
        function lic_getRemainingDays() {
            const { licencia } = tpvState;
            if (licencia.activada || !licencia.fechaActivacion) {
                return licencia.diasPrueba;
            }
            const fechaInicio = new Date(licencia.fechaActivacion);
            const hoy = new Date();
            
            // Calcular tiempo restante según la unidad configurada
            const unidad = licencia.unidadTiempo || 'dias';
            let tiempoRestante;
            
            if (unidad === 'minutos') {
                const minutosPasados = Math.floor((hoy - fechaInicio) / (1000 * 60));
                tiempoRestante = Math.max(0, licencia.diasPrueba - minutosPasados);
            } else if (unidad === 'segundos') {
                const segundosPasados = Math.floor((hoy - fechaInicio) / 1000);
                tiempoRestante = Math.max(0, licencia.diasPrueba - segundosPasados);
            } else {
                // Días por defecto
                const diasPasados = Math.ceil((hoy - fechaInicio) / (1000 * 60 * 60 * 24));
                tiempoRestante = Math.max(0, licencia.diasPrueba - diasPasados);
            }
            
            return tiempoRestante;
        }
        
        function lic_getTimeUnitText() {
            const unidad = tpvState.licencia.unidadTiempo || 'dias';
            const tiempo = lic_getRemainingDays();
            
            if (unidad === 'minutos') {
                return `${tiempo} minuto${tiempo !== 1 ? 's' : ''}`;
            } else if (unidad === 'segundos') {
                return `${tiempo} segundo${tiempo !== 1 ? 's' : ''}`;
            } else {
                return `${tiempo} día${tiempo !== 1 ? 's' : ''}`;
            }
        }

        async function lic_activateLicense(){
            const key = document.getElementById("lic-key-input").value.trim();
            const { clienteId } = tpvState.licencia;
            const lang = getLang();
            
            if(!key) return showToast(lang.toast_license_key_missing,"warning");
            
            // Verificar clave administrativa (permanente)
            const adminHash = await lic_sha256("admin" + getSecretKey());
            
            if(key === adminHash){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                tpvState.licencia.unidadTiempo = 'dias';
                await saveState();
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
                showToast(lang.toast_admin_license_activated, "info");
                return;
            }
            
            // Verificar claves con duración personalizada
            let claveValida = false;
            let tiempoLicencia = 0;
            let unidadTiempo = 'dias';
            
            // Duraciones posibles en diferentes unidades
            const duracionesPosibles = [
                // Días
                { valor: 30, unidad: 'dias' },
                { valor: 60, unidad: 'dias' },
                { valor: 90, unidad: 'dias' },
                { valor: 180, unidad: 'dias' },
                { valor: 365, unidad: 'dias' },
                { valor: 730, unidad: 'dias' },
                // Minutos (para pruebas rápidas)
                { valor: 1, unidad: 'minutos' },
                { valor: 5, unidad: 'minutos' },
                { valor: 10, unidad: 'minutos' },
                { valor: 30, unidad: 'minutos' },
                { valor: 60, unidad: 'minutos' },
                // Segundos (para pruebas muy rápidas)
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
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
                startLicenseAutoCheck(); // Reiniciar el auto-check con la nueva unidad
                const unidadTexto = unidadTiempo === 'dias' ? 'días' : unidadTiempo === 'minutos' ? 'minutos' : 'segundos';
                showToast(`${lang.toast_license_activated} (${tiempoLicencia} ${unidadTexto})`, "success");
            } else {
                showToast(lang.toast_license_incorrect,"danger");
            }
        }

        function lic_checkLicense(){
            const { licencia } = tpvState;
            const estado = document.getElementById("lic-status");
            const countdownContainer = document.getElementById("lic-countdown-container");
            const countdownDisplay = document.getElementById("lic-countdown");
            const deactivateSection = document.getElementById("deactivate-license-section");
            const lang = getLang();
            const tiempoRestante = lic_getRemainingDays();
            const tiempoTexto = lic_getTimeUnitText();
            
            const _licEl = document.getElementById("lic-client-id"); if(_licEl) { _licEl.value = licencia.clienteId || "—"; _licEl.innerText = licencia.clienteId || "—"; }
            const overlay = document.getElementById("license-lock-overlay");
            const overlayClientId = document.getElementById("overlay-client-id");
            
            // Guardia: si los elementos del tab no existen aún, salir sin error
            if (!estado || !countdownContainer) return;
            
            // Actualizar ID en el overlay
            if (overlayClientId) {
                overlayClientId.value = licencia.clienteId;
            }
            
            // ⚡ MODO DE PRUEBA RÁPIDA: Permite usar sin licencia presionando Ctrl+Shift+T
            const modoTestRapido = localStorage.getItem('tpv_test_rapido') === 'true';
            
            if(modoTestRapido) {
                estado.innerText = "🔧 MODO PRUEBA RÁPIDA ACTIVADO";
                estado.className = "text-primary fw-bold";
                if(overlay) overlay.classList.add("d-none");
                countdownContainer.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
                return; // Salir sin bloquear
            }
            
            if(licencia.activada){
                estado.innerText = lang.license_activated;
                estado.className = "text-success fw-bold";
                if(overlay) overlay.classList.add("d-none");
                countdownContainer.classList.add("d-none");
                // Mostrar botón de desactivar cuando hay licencia activa
                if(deactivateSection) deactivateSection.classList.remove("d-none");
            } else if(tiempoRestante > 0){
                estado.innerText = `Prueba: ${tiempoTexto} restantes`;
                estado.className = "text-warning fw-bold";
                if(overlay) overlay.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
                
                // Mostrar contador con unidad correcta
                countdownContainer.classList.remove("d-none");
                if (countdownDisplay) countdownDisplay.innerText = tiempoTexto + ' restante' + (tiempoRestante !== 1 ? 's' : '');
                
                // Cambiar color según tiempo restante
                const unidad = licencia.unidadTiempo || 'dias';
                if (unidad === 'segundos') {
                    if (tiempoRestante <= 30) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 60) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                } else if (unidad === 'minutos') {
                    if (tiempoRestante <= 5) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 10) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                } else {
                    if (tiempoRestante <= 3) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 7) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                }
            } else {
                estado.innerText = lang.license_expired;
                estado.className = "text-danger fw-bold";
                if(overlay) overlay.classList.add("d-none");
                countdownContainer.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
            }
        }
        
        // ⚡ Función para activar/desactivar modo de prueba rápida (Ctrl+Shift+T)
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                const modoActual = localStorage.getItem('tpv_test_rapido') === 'true';
                localStorage.setItem('tpv_test_rapido', !modoActual);
                showToast(
                    !modoActual ? 
                    '🔧 MODO PRUEBA RÁPIDA ACTIVADO - Sin restricciones de licencia' : 
                    '🔒 MODO PRUEBA RÁPIDA DESACTIVADO - Licencia requerida',
                    !modoActual ? 'success' : 'warning'
                );
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
            }
        });
        
        function copyOverlayClientId() {
            const clientId = document.getElementById("overlay-client-id").value;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(clientId).then(() => {
                    showToast("ID copiado al portapapeles", "info");
                }).catch(err => {
                    console.error('Error al copiar: ', err);
                });
            }
        }
        
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
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
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
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
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
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
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
            localStorage.setItem('tpv_custom_name', customName);
            
            // Actualizar el título en el header
            conf_updateTPVName();
            
            showToast("Nombre del TPV actualizado correctamente", "success");
        }

        // --- FUNCIÓN PARA ACTUALIZAR EL NOMBRE DEL TPV EN EL HEADER ---
        function conf_updateTPVName() {
            const customName = localStorage.getItem('tpv_custom_name');
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
            const customName = localStorage.getItem('tpv_custom_name');
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
                // ===== RED Y CONECTIVIDAD =====
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
        
        // ==================== AUTO-ACTUALIZACIÓN DE LICENCIA ====================
        let licenseCheckInterval = null;
        
        function startLicenseAutoCheck() {
            // Limpiar intervalo existente
            if (licenseCheckInterval) {
                clearInterval(licenseCheckInterval);
            }
            
            const unidad = tpvState.licencia?.unidadTiempo || 'dias';
            
            // Configurar intervalo según la unidad
            if (unidad === 'segundos') {
                // Actualizar cada segundo
                licenseCheckInterval = setInterval(() => {
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 1000);
            } else if (unidad === 'minutos') {
                // Actualizar cada 10 segundos
                licenseCheckInterval = setInterval(() => {
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 10000);
            } else {
                // Para días, actualizar cada 5 minutos
                licenseCheckInterval = setInterval(() => {
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 300000);
            }
        }
        
        // ========== FUNCIONES DE BACKUP AUTOMÁTICO ==========
        async         // ===== COPIAS SEGURIDAD =====
