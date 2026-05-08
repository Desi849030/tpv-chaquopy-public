/**
 * tpv_logs_ui.js — TPV ULTRA SMART v5.0
 * Logs: agregar, mostrar, limpiar logs de actividad
 * Extraido de script_5.js
 */

        // ========== FUNCIONES DE LOGS ==========
        let systemLogs = [];
        
                // ===== LOGS Y LIMPIEZA =====
        function agregar_log(mensaje, tipo = 'info') {
            const timestamp = new Date().toISOString();
            systemLogs.push({ timestamp, tipo, mensaje });
            
            // Mantener solo los últimos 100 logs
            if (systemLogs.length > 100) {
                systemLogs = systemLogs.slice(-100);
            }
            
            actualizar_logs();
        }
        
        function actualizar_logs() {
            const display = document.getElementById('logs-display');
            if (!display) return;
            
            const logsHTML = systemLogs.map(log => {
                const fecha = new Date(log.timestamp).toLocaleString();
                const color = log.tipo === 'error' ? '#f00' : log.tipo === 'warning' ? '#ff0' : '#0f0';
                return `<p style="color: ${color}; margin: 0.25rem 0;">[${fecha}] ${log.mensaje}</p>`;
            }).reverse().join('');
            
            display.innerHTML = logsHTML || '<p>No hay logs disponibles</p>';
        }
        
        function limpiar_logs() {
            if (confirm('¿Está seguro de limpiar todos los logs?')) {
                systemLogs = [];
                actualizar_logs();
                showToast('Logs limpiados', 'info');
            }
        }
        
        // Agregar log inicial
        agregar_log('Sistema TPV iniciado correctamente', 'info');
        
        // ========== FUNCIONES DE ELIMINACIÓN DE REGISTROS ==========
        async function eliminar_cierre(fecha) {
            if (confirm(`¿Está seguro de eliminar el cierre del día ${fecha}?`)) {
                tpvState.cierresCaja = tpvState.cierresCaja.filter(c => c.fecha !== fecha);
                await saveState();
                showToast('Cierre eliminado exitosamente', 'success');
                registros_renderizar();
            }
        }
        
        async function eliminar_todos_cierres() {
            if (confirm('¿Está seguro de eliminar TODOS los cierres de caja? Esta acción no se puede deshacer.')) {
                tpvState.cierresCaja = [];
                await saveState();
                showToast('Todos los cierres han sido eliminados', 'warning');
                registros_renderizar();
            }
        }
        
        async function eliminar_venta_individual(index) {
            const sortedHistorial = [...tpvState.historialVentas].sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
            const venta = sortedHistorial[index];
            
            if (confirm(`¿Está seguro de eliminar esta venta de ${venta.nombre}?`)) {
                const ventaIndex = tpvState.historialVentas.indexOf(venta);
                tpvState.historialVentas.splice(ventaIndex, 1);
                await saveState();
                showToast('Venta eliminada exitosamente', 'success');
                registros_renderizar();
            }
        }
        
        async function eliminar_todas_ventas() {
            if (confirm('¿Está seguro de eliminar TODO el historial de ventas? Esta acción no se puede deshacer.')) {
                tpvState.historialVentas = [];
                await saveState();
                showToast('Todo el historial de ventas ha sido eliminado', 'warning');
                registros_renderizar();
            }
        }
        
        // Funciones auxiliares simples
        async function copiarTexto(texto) {
            try {
                await navigator.clipboard.writeText(texto);
                showToast('✅ Copiado', 'success');
            } catch {
                const ta = document.createElement('textarea');
                ta.value = texto;
                ta.style.position = 'fixed';
                ta.style.opacity = '0';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                showToast('✅ Copiado', 'success');
            }
        }
