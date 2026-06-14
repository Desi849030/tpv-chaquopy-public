// tpv_boot_loader.js — Arranque de la app: inicialización, splash, carga de módulos
(function(){

        var bar=document.getElementById('boot-bar');
        var status=document.getElementById('boot-status');
        var nameEl=document.getElementById('boot-store-name');
        var screen=document.getElementById('tpv-boot-screen');
        var MIN_SPLASH=300;
        var FAILSAFE=4000;
        var MAX_INTENTOS=25;
        var intento=0;
        var bootOk=false;
        var startTime=Date.now();

        try{var sn=tpvStorage.getItem('tpv_custom_name');if(sn&&nameEl)nameEl.textContent=sn;}catch(e){}
        function setS(t){if(status)status.textContent=t;}
        function setB(p){if(bar)bar.style.width=Math.min(p,100)+'%';}
        function hide(){
            if(bootOk)return;bootOk=true;
            if(!screen)return;
            screen.classList.add('fade-out');
            setTimeout(function(){screen.style.display='none';},400);
            try{var sn=tpvStorage.getItem('tpv_custom_name');if(sn){var h=document.getElementById('tpv-custom-name');if(h)h.textContent=sn;}}catch(e){}
        }
        function scheduleHide(){
            var elapsed=Date.now()-startTime;
            var rem=Math.max(MIN_SPLASH-elapsed,0);
            if(rem>0)setTimeout(function(){hide();},rem);
            else hide();
        }
        // v6.10 FIX: Exponer para que tpv_auth.js pueda notificar cuando el login esté listo
        window._splashHide = scheduleHide;
        function tryConnect(){
            intento++;
            setB(Math.min(intento*2.5,88));
            var ctrl=new AbortController();
            var t=setTimeout(function(){ctrl.abort();},800);
            fetch('/api/health',{signal:ctrl.signal,cache:'no-store'})
                .then(function(r){clearTimeout(t);
                    // v6.9 FIX: Aceptar también 404 (endpoint puede no existir pero el servidor responde)
                    if(r.ok){
                        clearInterval(iv);setB(100);setS('Cargando pantalla de acceso...');
                        fetch('/api/config/publica',{cache:'no-store'})
                            .then(function(rc){return rc.json();})
                            .then(function(d){var n=d&&(d.nombre_tienda||d.nombre);
                                if(n){if(nameEl)nameEl.textContent=n;
                                try{tpvStorage.setItem('tpv_custom_name',n);}catch(e){}}})
                            .catch(function(){});
                        // v6.10.3 FIX: NO llamar scheduleHide() aqui.
                        // Solo tpv_auth.js debe esconder el splash cuando el login este listo.
                        // Si se esconde aqui, aparece pantalla en blanco mientras tpv_auth.js carga.
                    }
                })
                .catch(function(){clearTimeout(t);});
            if(intento>=MAX_INTENTOS)clearInterval(iv);
        }
        var iv=setInterval(tryConnect,250);
        var msgs=[[0,'Iniciando Sistema TPV...'],[800,'Cargando módulos del sistema...'],[1600,'Preparando base de datos...'],[3000,'Conectando con el servidor...'],[5000,'Cargando catálogo de productos...'],[8000,'Preparando pantalla de acceso...'],[12000,'Un momento más...']];
        msgs.forEach(function(m){setTimeout(function(){if(!bootOk)setS(m[1]);},m[0]);});
        setTimeout(function(){if(!bootOk){setB(100);setS('✅ Listo');hide();}},FAILSAFE);
    })();
