// ════════════════════════════════════════════════════════════════
// app3/10_hotfixes.js — Hotfixes v8.0.x: refresh en tiempo real, window exports, auto-refresh, rebuild inventario
// Extraído de app_3.js (líneas 5392–5484) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
// ═══ HOTFIX v8.0.1 - Refresh en tiempo real ═══
async function tpv_refreshFromServer() {
    try {
        const r = await fetch('/api/publico/catalogo', {credentials:'same-origin'});
        const d = await r.json();
        if (d.ok && d.productos && d.productos.length) {
            const hoy = new Date().toISOString().split('T')[0];
            tpvState.productos = d.productos;
            tpvState.categorias = d.categorias || [...new Set(d.productos.map(p=>p.categoria))].sort();
            tpvState.inventarios[hoy] = d.productos.map(p => ({
                id: p.id, nombre: p.nombre,
                categoria: p.categoria ?? 'General', um: p.um ?? 'Un',
                cantInicial: Number(p.stock) || 0, vendido: 0,
                cantFinal: Number(p.stock) || 0,
                precioVenta: Number(p.precio) || 0,
                precioCosto: Number(p.costo) || 0,
                costoUnitario: Number(p.costo) || 0,
                importe: 0, comision: 0, gananciaNeta: 0
            }));
            if (typeof inv_recalcularVentasDelDia === 'function') {
                try { inv_recalcularVentasDelDia(hoy); } catch(_e) {}
            }
            if (typeof tpv_renderizarProductos === 'function') tpv_renderizarProductos();
            if (typeof tpv_renderizarFiltroCategorias === 'function') tpv_renderizarFiltroCategorias();
            if (typeof inv_renderizarTabla === 'function') inv_renderizarTabla(hoy);
            if (typeof ventas_renderizarTablaHoy === 'function') ventas_renderizarTablaHoy();
            if (typeof dashboard_cargar === 'function') dashboard_cargar();
            console.log('TPV refrescado: ' + d.productos.length + ' productos');
        }
    } catch(e) { console.warn('Refresh fallo:', e.message); }
}
setInterval(() => {
    if (document.visibilityState === 'visible' && window.AUTH?.usuario) tpv_refreshFromServer();
}, 30000);


// ═══ HOTFIX v8.0.2 — Window exports ═══
(function(){
  if(typeof tpv_renderizarProductos==='function' && !window.tpv_renderizarProductos) window.tpv_renderizarProductos=tpv_renderizarProductos;
  if(typeof conf_setLanguage==='function' && !window.conf_setLanguage) window.conf_setLanguage=conf_setLanguage;
  if(typeof saveState==='function' && !window.saveState) window.saveState=saveState;
  if(typeof loadState==='function' && !window.loadState) window.loadState=loadState;
  if(typeof refreshAllUI==='function' && !window.refreshAllUI) window.refreshAllUI=refreshAllUI;
  if(typeof inv_renderizarTabla==='function' && !window.inv_renderizarTabla) window.inv_renderizarTabla=inv_renderizarTabla;
  if(typeof registros_renderizar==='function' && !window.registros_renderizar) window.registros_renderizar=registros_renderizar;
  if(typeof gestion_guardarProducto==='function' && !window.gestion_guardarProducto) window.gestion_guardarProducto=gestion_guardarProducto;
  if(typeof ventas_renderizarTablaHoy==='function' && !window.ventas_renderizarTablaHoy) window.ventas_renderizarTablaHoy=ventas_renderizarTablaHoy;
})();

// ═══ HOTFIX v8.0.2 — Auto-refresh cada 30s ═══
(function(){
    if(window._tpvAutoRefresh) return;
    window._tpvAutoRefresh = true;
    setInterval(async function(){
        if(typeof catalogo_cargarDesdeServidor==='function'){
            try{
                await catalogo_cargarDesdeServidor();
                if(typeof tpv_renderizarProductos==='function') tpv_renderizarProductos();
                if(typeof tpv_renderizarFiltroCategorias==='function') tpv_renderizarFiltroCategorias();
            }catch(e){}
        }
    },30000);
    console.log('🔄 Auto-refresh instalado (30s)');
})();

// ═══ HOTFIX v8.0.2 — Rebuild inventario diario desde catalogo ═══
(function(){
    if(window._tpvRebuildInv) return;
    window._tpvRebuildInv = true;
    var _origCargar = typeof catalogo_cargarDesdeServidor==='function'?catalogo_cargarDesdeServidor:null;
    if(_origCargar){
        window.catalogo_cargarDesdeServidor = async function(){
            await _origCargar();
            var hoy = typeof getTodayDateString==='function'?getTodayDateString():new Date().toISOString().split('T')[0];
            if(!tpvState.inventarios) tpvState.inventarios={};
            if(!tpvState.inventarios[hoy]) tpvState.inventarios[hoy]=[];
            var invArr = tpvState.inventarios[hoy];
            var invMap = {};
            invArr.forEach(function(it){invMap[it.id]=it;});
            tpvState.productos.forEach(function(p){
                if(!invMap[p.id]){
                    var stock = p.stock||0;
                    invArr.push({
                        id:p.id, nombre:p.nombre, categoria:p.categoria||'General',
                        pVenta:p.precio||0, um:p.um||'Un',
                        cantInicial:stock, cantFinal:stock, vendido:0,
                        iVenta:0, pCosto:p.costo||0, comision:0, ganancia:0
                    });
                }
            });
        };
    }
})();
