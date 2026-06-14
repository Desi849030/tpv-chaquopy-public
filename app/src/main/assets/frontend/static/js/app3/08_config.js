// ════════════════════════════════════════════════════════════════
// app3/08_config.js — Backup JSON, nomenclador, licencias, nombre TPV, limpieza y red
// Extraído de app_3.js (líneas 3883–4597) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
        /**
         * Exporta los datos del TPV de forma inteligente
         * Incluye validación y información del backup
         */
        function conf_handleExport(){
            try {
                // Preparar datos para exportar
                const backupData = {
                    version: "7.0",
                    fecha_exportacion: new Date().toISOString(),
                    entorno: TPV_CONFIG.getEnvironment(),
                    datos: tpvState
                };
                
                // Crear el blob con formato legible
                const dataStr = JSON.stringify(backupData, null, 2);
                const blob = new Blob([dataStr], {type: "application/json;charset=utf-8"});
                
                // Crear nombre descriptivo del archivo
                const fecha = getTodayDateString();
                const hora = new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
                const nombreArchivo = `tpv_backup_${fecha}_${hora}.json`;
                
                // Crear link temporal para descarga
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = nombreArchivo;
                link.style.display = "none";
                
                // Añadir al DOM, hacer click y limpiar
                document.body.appendChild(link);
                link.click();
                
                // Limpiar después de un pequeño delay
                setTimeout(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                }, 100);
                
                showToast(`✅ Backup exportado: ${nombreArchivo}`, "success");
                
                TPV_CONFIG.log(`Backup exportado: ${nombreArchivo}`);
            } catch (error) {
                console.error("Error al exportar:", error);
                showToast("❌ Error al exportar los datos. Intente nuevamente.", "danger");
            }
        }

        /**
         * Importa los datos del TPV de forma inteligente
         * Valida el formato y muestra información detallada
         */
        async function conf_handleImport(event){
            const file = event.target.files[0];
            
            if (!file) {
                event.target.value = "";
                return;
            }
            
            // Validar que sea un archivo JSON
            if (!file.name.toLowerCase().endsWith('.json')) {
                showToast("❌ Por favor, seleccione un archivo JSON válido.", "danger");
                event.target.value = "";
                return;
            }
            
            // Confirmar antes de importar
            if (!(await tpvConfirm("⚠️ ¿Está seguro de importar este backup?\n\nEsto reemplazará todos los datos actuales.\n\nSe recomienda exportar un backup antes de continuar."))) {
                event.target.value = "";
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                try {
                    const importedData = JSON.parse(e.target.result);
                    
                    // Determinar si es un backup nuevo (con metadata) o antiguo
                    let dataToImport;
                    let backupVersion = "desconocida";
                    let backupDate = "desconocida";
                    
                    if (importedData.version && importedData.datos) {
                        // Formato nuevo con metadata
                        dataToImport = importedData.datos;
                        backupVersion = importedData.version;
                        backupDate = new Date(importedData.fecha_exportacion).toLocaleString();
                    } else if (importedData.config && importedData.productos) {
                        // Formato antiguo (directo)
                        dataToImport = importedData;
                    } else {
                        throw new Error("Formato de backup no válido");
                    }
                    
                    // Validar estructura mínima
                    if (!dataToImport.config || !dataToImport.productos) {
                        throw new Error("El archivo no contiene datos válidos del TPV");
                    }
                    
                    // Migrar datos si es necesario
                    if (!dataToImport.licencia) {
                        dataToImport.licencia = {
                            activa: false,
                            clienteId: "",
                            vencimiento: null,
                            permanente: false,
                            unidadTiempo: "dias"
                        };
                    }
                    
                    // Aplicar los datos importados
                    tpvState = { ...getDefaultState(), ...dataToImport };
                    await saveState();
                    
                    showToast(`✅ Backup importado correctamente\n📦 Versión: ${backupVersion}\n📅 Fecha: ${backupDate}`, "success");
                    
                    TPV_CONFIG.log(`Backup importado - Versión: ${backupVersion}`);
                    
                    // Recargar la página después de 2 segundos
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                    
                } catch (err) {
                    console.error("Error al importar:", err);
                    showToast(`❌ Error al importar: ${err.message}`, "danger");
                } finally {
                    event.target.value = "";
                }
            };
            
            reader.onerror = () => {
                showToast("❌ Error al leer el archivo.", "danger");
                event.target.value = "";
            };
            
            reader.readAsText(file);
        }

        // --- LÓGICA DE NOMENCLADOR ---
        async function nom_cargarDenominaciones(moneda) {
            const contenedor = document.getElementById("nom-contenedorDivisas");
            if (!contenedor) return;
            if (!tpvState || !tpvState.nomencladores) return;
            const denominaciones = (tpvState.nomencladores[moneda] ?? []).sort((a,b) => b-a);
            const cantidades = tpvState.nomencladorCantidades[moneda] ?? {};
            
            contenedor.innerHTML = denominaciones.map(d => {
                const cantidad = cantidades[d] ?? '';
                const subtotal = d * (cantidad || 0);
                return `<div class="input-group input-group-sm mb-2">
                    <span class="input-group-text fw-bold" style="width: 70px;">${formatCurrency(d).replace('.00','')}</span>
                    <input type="number" class="form-control text-end" data-valor="${d}" oninput="nom_actualizarTotalDenominaciones()" placeholder="Cantidad" min="0" value="${cantidad}">
                    <span class="input-group-text text-muted" id="nom-subtotal-${d}" style="width: 110px; justify-content: flex-end;">= ${subtotal.toFixed(2)}</span>
                    <button class="btn btn-sm btn-outline-danger" onclick="nom_eliminarDenominacion('${moneda}', ${d})">×</button>
                </div>`;
            }).join('');
            nom_actualizarTotalDenominaciones();
        }

        async function nom_agregarDenominacion(){
            if (!tpvState || !tpvState.nomencladores) return;
            const moneda = document.getElementById("nom-selectPais")?.value;
            if (!moneda) return;
            const input = document.getElementById("nom-inputNueva");
            const valor = parseInt(input?.value, 10);
            if(!isNaN(valor) && valor > 0 && !tpvState.nomencladores[moneda].includes(valor)){
                tpvState.nomencladores[moneda].push(valor);
                if (input) input.value = "";
                await saveState();
                nom_cargarDenominaciones(moneda);
            }
        }

        async function nom_eliminarDenominacion(moneda, denominacion){
            tpvState.nomencladores[moneda] = tpvState.nomencladores[moneda].filter(d => d !== denominacion);
            if(tpvState.nomencladorCantidades[moneda]) delete tpvState.nomencladorCantidades[moneda][denominacion];
            await saveState();
            nom_cargarDenominaciones(moneda);
        }

        function nom_actualizarTotalDenominaciones() {
            const selEl = document.getElementById("nom-selectPais");
            if (!selEl) return;
            const moneda = selEl.value;
            tpvState.nomencladorCantidades[moneda] = {};
            let totalValor = 0, totalCantidad = 0;
            
            document.querySelectorAll("#nom-contenedorDivisas input").forEach(input => {
                const d = parseFloat(input.dataset.valor);
                const c = parseInt(input.value) || 0;
                totalValor += d * c;
                totalCantidad += c;
                const _ns = document.getElementById(`nom-subtotal-${d}`); if(_ns) _ns.innerText = `= ${(d*c).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                if(c > 0) tpvState.nomencladorCantidades[moneda][d] = c;
            });

            const _nomTot = document.getElementById("nom-totalesDenominaciones"); if(_nomTot) _nomTot.innerText = totalValor.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const _nomCant = document.getElementById("nom-totalCantidadDenominaciones"); if(_nomCant) _nomCant.innerText = totalCantidad;
            saveState();
        }

        // --- LÓGICA DE LICENCIA ---
        const lic_sha256 = async (text) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))).map(b => b.toString(16).padStart(2, '0')).join('');
        
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
            
            licencia.activada = true; licencia.tipo = 'premium';
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
                estado.innerText = "Activa - Sin límite";
                estado.className = "text-danger fw-bold";
                if(overlay) overlay.classList.remove("d-none");
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
            if((await tpvConfirm("¿Está seguro que desea desactivar la licencia actual?\n\nEsto es útil para probar diferentes claves de licencia."))){
                tpvState.licencia.activada = false;
                tpvState.licencia.key = "";
                tpvState.licencia.fechaActivacion = null;
                await saveState();
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
            if ((await tpvConfirm(lang.confirm_clear_today_sales))) {
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
            if ((await tpvConfirm(lang.confirm_clear_closures))) {
                tpvState.cierresCaja = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_closures_cleared, "success");
            }
        }

        async function conf_limpiarHistorial() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_history))) {
                tpvState.historialVentas = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_history_cleared, "success");
            }
        }

        async function conf_limpiarInventarios() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_inventories))) {
                tpvState.inventarios = {};
                await saveState();
                inv_cargarInventario(getTodayDateString());
                showToast(lang.toast_inventories_cleared, "success");
            }
        }

        async function conf_limpiarTodo() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_everything))) {
                const { productos, categorias, config, licencia } = tpvState; // Preserve essential data
                tpvState = getDefaultState(); // Reset
                tpvState = { ...tpvState, productos, categorias, config, licencia }; // Restore
                await saveState();
                await refreshAllUI();
                showToast(lang.toast_app_reset, "success");
            }
        }

        // updateNetworkStatus: actualiza badge + indicador offline
        // Pinta el estado. Si se pasa 'estadoReal' (bool) lo usa; si no, navigator.onLine.
        function updateNetworkStatus(showToastMsg, estadoReal) {
            const isOnline = (typeof estadoReal === 'boolean') ? estadoReal : navigator.onLine;
            const indicator = document.getElementById('offline-indicator');
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            // El cartel naranja "Modo Sin Conexión" ya no es necesario: el propio
            // badge se pone ROJO con texto "Offline". Lo mantenemos siempre oculto
            // para no duplicar el aviso.
            if (indicator) indicator.style.display = 'none';
            if (statusBadge && statusText) {
                const icon = statusBadge.querySelector('i');
                statusBadge.classList.toggle('bg-success', isOnline);
                statusBadge.classList.toggle('bg-danger', !isOnline);
                statusBadge.classList.toggle('offline', !isOnline);
                if (icon) icon.className = isOnline ? 'bi bi-wifi' : 'bi bi-wifi-off';
                statusText.textContent = isOnline ? 'Online' : 'Offline';
            }
            if (showToastMsg) {
                if (isOnline && window.wasOffline) {
                    showToast('Conexión restaurada', 'success');
                    window.wasOffline = false;
                    conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
                } else if (!isOnline) {
                    showToast('Modo Offline — datos guardados localmente', 'warning');
                    window.wasOffline = true;
                }
            }
        }

        // Chequeo REAL de internet: navigator.onLine en el WebView siempre es true
        // (hay red hacia 127.0.0.1). Hacemos un fetch real a un recurso externo.
        async function _checkInternetReal() {
            if (!navigator.onLine) return false;
            try {
                const ctrl = new AbortController();
                setTimeout(() => ctrl.abort(), 3500);
                // Recurso liviano y permisivo con CORS; no-cors evita bloqueos.
                await fetch('https://www.gstatic.com/generate_204',
                            { method: 'GET', mode: 'no-cors', cache: 'no-store', signal: ctrl.signal });
                return true;
            } catch (e) {
                return false;
            }
        }

        let _netPrev = null;
        async function _monitorRed(conToast) {
            const real = await _checkInternetReal();
            if (real !== _netPrev) {
                updateNetworkStatus(conToast === true && _netPrev !== null, real);
                _netPrev = real;
            }
        }
        // Polling cada 8s + reacción inmediata a eventos del navegador.
        setInterval(() => _monitorRed(true), 8000);
        window.addEventListener('online',  () => _monitorRed(true));
        window.addEventListener('offline', () => { _netPrev = false; updateNetworkStatus(true, false); });
        setTimeout(() => _monitorRed(false), 1500);
        
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
        
