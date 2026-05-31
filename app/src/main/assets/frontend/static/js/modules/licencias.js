// Módulo: licencias
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
            
            licencia.activada = true; licencia.tipo = 'premium';
            if(licencia.activada){
                estado.innerText = lang.license_act