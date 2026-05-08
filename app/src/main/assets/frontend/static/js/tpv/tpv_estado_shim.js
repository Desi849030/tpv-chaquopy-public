// tpv_estado_shim.js — Declaración inicial de tpvState (shim global)
    var tpvState = {
        config:{lang:'es',theme:'light',globalProfitPercent:20},
        productos:[],categorias:[],ordenActual:[],
        ventasDiarias:{},historialVentas:[],inventarios:{},
        cierresCaja:[],licencia:{activada:false,diasPrueba:15,clienteId:''},
        nomencladores:{USD:[100,50,20,10,5,1],EUR:[100,50,20,10,5],CUP:[1000,500,200,100,50,20,10,5,1]},
        nomencladorCantidades:{}
    };
    window.tpvState = tpvState;
    var _dbg_buffer = [];
    function dbg(msg,tipo){
        tipo=tipo||'info';
        var t=new Date().toLocaleTimeString('es',{hour12:false});
        _dbg_buffer.push({t:t,msg:msg,tipo:tipo});
        if(_dbg_buffer.length>300)_dbg_buffer.shift();
        // Rutear al nuevo panel si existe
        if(window.tpvDebugger&&typeof window.tpvDebugger.log==='function'){
            window.tpvDebugger.log(msg,tipo);
        }
    }
    window.dbg = dbg;
    // Shim _dbg_mostrar para compatibilidad
    window._dbg_mostrar = function(){
        if(window.tpvDebugger&&typeof window.tpvDebugger.activar==='function'){
            window.tpvDebugger.activar();
        }
    };
    window._dbg_toggle = window._dbg_mostrar;
    window._dbg_limpiar = function(){
        _dbg_buffer=[];
        if(window.tpvDebugger&&typeof window.tpvDebugger.log==='function'){
            // limpiar log interno
        }
    };
    window.onerror = function(msg,src,line,col,err){
        dbg('❌ [JS] '+msg+' — '+(src||'').split('/').pop()+':'+line,'error');
        return false;
    };
    window.addEventListener('unhandledrejection',function(e){
        dbg('❌ [PROMISE] '+(e.reason?.message||String(e.reason||'')),'error');
    });
