// tpv_nomenclator.js
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
        
