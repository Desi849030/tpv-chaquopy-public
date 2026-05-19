// === DEBOUNCE ===
function debounce(fn,ms){var t;return function(){var ctx=this,a=arguments;clearTimeout(t);t=setTimeout(function(){fn.apply(ctx,a)},ms);};}
// === SKELETON ===
function showSkeleton(el,n){if(!el)return;var h="";for(var i=0;i<(n||3);i++)h+='<div class="sk-text w'+[80,60,100,40][i%4]+' skeleton"></div>';el.innerHTML=h;}
function hideSkeleton(el,html){if(el)el.innerHTML=html||"";}
// tpv_utilidades.js — Helpers: logs, copiar texto, eliminaciones
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

