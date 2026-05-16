// smart_excel_compat.js -- Funciones compat para gestion_handleImportXLSX
// ==================== COMPAT: Funciones para gestion_handleImportXLSX ====================
function getTodayDateString(){
    var d=new Date();
    return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}

async function saveState(){
    try{
        var s={productos:tpvState.productos||[],categorias:tpvState.categorias||[],inventarios:tpvState.inventarios||{}};
        localStorage.setItem('tpv_state_backup',JSON.stringify(s));
        console.log('[Import] Estado persistido ('+s.productos.length+' productos)');
    }catch(e){console.warn('[saveState]',e)}
}

async function catalogo_sincronizarAlServidor(){
    try{
        var prods=tpvState.productos||[];
        if(!prods.length)return;
        var r=await fetch('/api/reconstruir-desde-productos',{
            method:'POST',credentials:'same-origin',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({productos:prods})
        });
        if(r.ok){var d=await r.json();if(d.ok)if(typeof showToast==='function')showToast('Sincronizados '+(d.sincronizados||0)+' productos','success');}
    }catch(e){console.warn('[catalogo_sync]',e.message)}
}

async function catalogo_cargarDesdeServidor(){
    try{
        var r=await fetch('/api/productos',{credentials:'same-origin'});
        if(r.ok){
            var d=await r.json();
            var list=Array.isArray(d)?d:(d&&d.productos)?d.productos:[];
            tpvState.productos=list;
            tpvState.categorias=[...new Set(list.map(function(p){return p.categoria||'General'}))];
            console.log('[catalogo] Cargados',list.length,'productos del servidor');
        }
    }catch(e){console.warn('[catalogo_load]',e.message)}
}
