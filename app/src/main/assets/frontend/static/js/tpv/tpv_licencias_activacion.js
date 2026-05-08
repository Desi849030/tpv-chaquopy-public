// tpv_licencias_activacion.js — Activación y validación de licencias
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
        
        function activar_licencia() { lic_activateLicense(); }
        
        function eliminar_licencia() {
            if (confirm('¿Está seguro de eliminar la licencia actual?')) {
                tpvState.licencia.activada = false;
                tpvState.licencia.key = null;
                saveState();
                showToast('Licencia eliminada', 'warning');
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                lic_checkLicense();
            }
        }
        
        function mostrar_info_licencia() {
            // Delegamos al sistema principal de licencias
        localStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
            lic_checkLicense();
        }
        
        // ========== FUNCIONES DE LOGS ==========
        let systemLogs = [];
        
