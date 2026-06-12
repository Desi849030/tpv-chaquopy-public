// ════════════════════════════════════════════════════════════════
// app3/05_inventario.js — Inventario diario: carga, stock, ganancia global, totales
// Extraído de app_3.js (líneas 1410–1673) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
        function inv_cargarInventario(fecha){
            if(!tpvState.inventarios[fecha]){
                tpvState.inventarios[fecha] = [];
                const fechaAnterior = new Date(fecha);
                fechaAnterior.setDate(fechaAnterior.getDate() - 1);
                const inventarioAnterior = tpvState.inventarios[fechaAnterior.toISOString().split('T')[0]];
                
                tpvState.productos.forEach(p => {
                    const itemAnterior = inventarioAnterior?.find(i => i.id === p.id);
                    const cantInicial = itemAnterior?.cantFinal ?? 0;
                    tpvState.inventarios[fecha].push({
                        id: p.id, nombre: p.nombre, categoria: p.categoria ?? "General", precioVenta: p.precio, um: p.um ?? "Un",
                        cantInicial, cantFinal: cantInicial, vendido: 0, importe: 0, precioCosto: 0, comision: 0, gananciaNeta: 0
                    });
                });
            }
            inv_recalcularVentasDelDia(fecha);
        }

        function inv_recalcularVentasDelDia(fecha){
            if(!tpvState.inventarios[fecha]) return;
            
            tpvState.inventarios[fecha].forEach(item => { item.vendido = 0; });
            
            tpvState.historialVentas.filter(v => v.fecha.startsWith(fecha)).forEach(venta => {
                const item = tpvState.inventarios[fecha].find(i => i.id === venta.productoId);
                if(item) item.vendido += venta.cantidad;
            });
            
            tpvState.inventarios[fecha].forEach(item => { item.cantFinal = item.cantInicial - item.vendido; });
            
            inv_aplicarGananciaGlobal(fecha);
        }

        async function inv_actualizarStockPorVenta(fecha, productoId, quantity){
            inv_cargarInventario(fecha);
            const item = tpvState.inventarios[fecha].find(i => i.id === productoId);
            if(item){
                item.vendido += quantity;
                item.cantFinal = item.cantInicial - item.vendido;
            }
        }

        async function inv_aplicarGananciaGlobal(fecha = null) {
            const fechaActual = fecha ?? (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            const el = document.getElementById("inv-globalProfitPercent");
            const porcentaje = el ? parseFloat(el.value) / 100 : (tpvState.config?.globalProfitPercent || 0) / 100;
            if(!tpvState.inventarios[fechaActual]) return;
            
            tpvState.config.globalProfitPercent = 100 * porcentaje;
            
            // CORRECCIÓN: Asegurar que los cálculos se realicen correctamente
            tpvState.inventarios[fechaActual].forEach(item => {
                // Recalcular vendido basado en cantInicial y cantFinal
                item.vendido = Math.max(0, item.cantInicial - item.cantFinal);
                
                // Calcular importe (precio de venta × cantidad vendida)
                item.importe = item.vendido * item.precioVenta;
                
                // Calcular ganancia bruta unitaria
                const gananciaBrutaUnitaria = item.precioVenta - item.precioCosto;
                
                // Calcular comisión unitaria
                const comisionUnitaria = gananciaBrutaUnitaria > 0 ? gananciaBrutaUnitaria * porcentaje : 0;
                
                // Calcular comisión total
                item.comision = item.vendido * comisionUnitaria;
                
                // Calcular ganancia neta
                item.gananciaNeta = (item.vendido * gananciaBrutaUnitaria) - item.comision;
            });
            
            inv_renderizarTabla(fechaActual);
            await saveState();
        }

        function inv_renderizarTabla(fecha){
            const inventario = tpvState.inventarios[fecha];
            const tablaBody = document.getElementById("inv-tablaInventario");
            const lang = getLang();
            
            const filtroCategoriaSelect = document.getElementById('inv-filter-categoria');
            const categoriasUnicas = [...new Set(tpvState.productos.map(p => p.categoria))];
            filtroCategoriaSelect.innerHTML = `<option value="">${lang.all_categories}</option>` + 
                categoriasUnicas.sort().map(cat => `<option value="${cat}" ${cat === filtroCategoriaSelect.value ? 'selected' : ''}>${cat}</option>`).join('');
            
            if(!inventario){
                tablaBody.innerHTML = `<tr><td colspan="13" class="text-muted text-center">${lang.select_date_inventory}</td></tr>`;
                inv_actualizarTotales(fecha);
                return;
            }
            
            const filtros = {
                nombre: document.getElementById('inv-filter-nombre')?.value.toLowerCase() || '',
                categoria: filtroCategoriaSelect.value,
                pventa: document.getElementById('inv-filter-pventa')?.value || '', um: document.getElementById('inv-filter-um')?.value.toLowerCase() || '',
                cinicial: document.getElementById('inv-filter-cinicial')?.value || '', cfinal: document.getElementById('inv-filter-cfinal')?.value || '',
                vendido: document.getElementById('inv-filter-vendido')?.value || '', iventa: document.getElementById('inv-filter-iventa')?.value || '',
                pcosto: document.getElementById('inv-filter-pcosto')?.value || '', comision: document.getElementById('inv-filter-comision')?.value || '',
                ganancia: document.getElementById('inv-filter-ganancia')?.value || '',
            };

            const inventarioFiltrado = inventario.filter(i => 
                (!filtros.nombre || i.nombre.toLowerCase().includes(filtros.nombre)) &&
                (!filtros.categoria || i.categoria === filtros.categoria) &&
                (!filtros.pventa || (Number(i.precioVenta)||0).toFixed(2).includes(filtros.pventa)) &&
                (!filtros.um || i.um?.toLowerCase().includes(filtros.um)) &&
                (!filtros.cinicial || String(i.cantInicial).includes(filtros.cinicial)) &&
                (!filtros.cfinal || String(i.cantFinal).includes(filtros.cfinal)) &&
                (!filtros.vendido || String(i.vendido).includes(filtros.vendido)) &&
                (!filtros.iventa || (Number(i.importe)||0).toFixed(2).includes(filtros.iventa)) &&
                (!filtros.pcosto || (Number(i.precioCosto)||0).toFixed(2).includes(filtros.pcosto)) &&
                (!filtros.comision || (Number(i.comision)||0).toFixed(2).includes(filtros.comision)) &&
                (!filtros.ganancia || (Number(i.gananciaNeta)||0).toFixed(2).includes(filtros.ganancia))
            ).sort((a,b) => (a.categoria ?? 'zz').localeCompare(b.categoria ?? 'zz') || a.nombre.localeCompare(b.nombre));

            tablaBody.innerHTML = inventarioFiltrado.map((item, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td>${item.nombre}</td>
                    <td>${item.categoria ?? 'N/A'}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${(Number(item.precioVenta)||0).toFixed(2)}" step="0.01" min="0" onchange="inv_updateField('${fecha}','${item.id}','precioVenta',this.valueAsNumber)" title="Precio de venta (editable)"></td>
                    <td>${item.um}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${item.cantInicial}" onchange="inv_updateField('${fecha}','${item.id}','cantInicial',this.valueAsNumber)"></td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${item.cantFinal}" onchange="inv_updateField('${fecha}','${item.id}','cantFinal',this.valueAsNumber)"></td>
                    <td>${item.vendido}</td>
                    <td class="money-column">${formatCurrency(item.importe)}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${(Number(item.precioCosto)||0).toFixed(2)}" step="0.01" onchange="inv_updateField('${fecha}','${item.id}','precioCosto',this.valueAsNumber)"></td>
                    <td class="money-column">${formatCurrency(item.comision)}</td>
                    <td class="fw-bold money-column ${item.gananciaNeta >= 0 ? "text-success" : "text-danger"}">${formatCurrency(item.gananciaNeta)}</td>
                    <td><button class="btn btn-sm btn-danger" onclick="inv_eliminarFila('${fecha}','${item.id}')"><i class="bi bi-trash"></i></button></td>
                </tr>`).join("");
            
            inv_actualizarTotales(fecha, inventarioFiltrado);
        }

        async function inv_updateField(fecha, id, campo, valor) {
            const item = tpvState.inventarios[fecha].find(i => i.id === id);
            if (item) {
                item[campo] = valor;
                if (campo === 'cantInicial') item.cantFinal = item.cantInicial - item.vendido;
                // Si cambia el precio de venta o costo, reflejarlo también en el
                // producto del catálogo (precios variables) y persistir en servidor.
                if (campo === 'precioVenta' || campo === 'precioCosto') {
                    const prod = (tpvState.productos || []).find(p => p.id === id);
                    if (prod) {
                        if (campo === 'precioVenta') prod.precio = valor;
                        if (campo === 'precioCosto') prod.costo = valor;
                    }
                    try {
                        await fetch('/api/productos/precio', {
                            method: 'POST', credentials: 'same-origin',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ id: id,
                                precio: campo === 'precioVenta' ? valor : undefined,
                                costo:  campo === 'precioCosto' ? valor : undefined })
                        });
                    } catch (e) { /* offline: queda en estado local */ }
                }
            }
            await inv_aplicarGananciaGlobal(fecha);
            if (typeof saveState === 'function') { try { await saveState(); } catch(e){} }
        }

        async function inv_eliminarFila(fecha, id){
            if ((await tpvConfirm(getLang().confirm_delete_product_inv))) {
                tpvState.inventarios[fecha] = tpvState.inventarios[fecha].filter(i => i.id !== id);
                await inv_aplicarGananciaGlobal(fecha);
            }
        }

        function inv_actualizarTotales(fecha, data = null) {
            const items = data ?? tpvState.inventarios[fecha] ?? [];
            const lang = getLang();

            // CORRECCIÓN FINAL: Lógica de totalización robusta con bucle for...of para máxima claridad.
            const totals = {
                pventa: 0, pcosto: 0,
                cantInicial: 0, cantFinal: 0, vendido: 0, importe: 0,
                costoVendido: 0, comision: 0, ganancia: 0
            };

            for (const item of items) {
                totals.pventa += Number(item.precioVenta) || 0;
                totals.pcosto += Number(item.precioCosto) || 0;
                totals.cantInicial += Number(item.cantInicial) || 0;
                totals.cantFinal += Number(item.cantFinal) || 0;
                totals.vendido += Number(item.vendido) || 0;
                totals.importe += Number(item.importe) || 0;
                totals.costoVendido += (Number(item.vendido) || 0) * (Number(item.precioCosto) || 0);
                totals.comision += Number(item.comision) || 0;
                totals.ganancia += Number(item.gananciaNeta) || 0;
            }

            const _set = (id, val) => { const e = document.getElementById(id); if (e) e.innerText = val; };
            _set("inv-totalPventa", '$' + totals.pventa.toFixed(2));
            _set("inv-totalPcosto", '$' + totals.pcosto.toFixed(2));
            _set("inv-totalCantInicial", parseFloat(totals.cantInicial.toFixed(2)));
            _set("inv-totalCantFinal", parseFloat(totals.cantFinal.toFixed(2)));
            _set("inv-totalVendido", parseFloat(totals.vendido.toFixed(2)));
            _set("inv-totalImporte", totals.importe.toFixed(2));
            _set("inv-totalComision", totals.comision.toFixed(2));
            _set("inv-totalGanancia", totals.ganancia.toFixed(2));
            // Compat: la celda antigua de costo vendido si aún existe
            const _cv = document.getElementById("inv-totalCostoVendido");
            if (_cv) { _cv.innerText = totals.costoVendido.toFixed(2); _cv.title = lang.tooltip_total_investment || ''; }
        }

        function inv_abrirModalProducto(){
            if (!invModalStock) {
                const el = document.getElementById('inv-modal-stock');
                if (!el) { console.warn('[TPV] Modal inv-modal-stock no encontrado'); return; }
                invModalStock = new bootstrap.Modal(el);
            }
            const select = document.getElementById("inv-stock-producto");
            if (!select) return;
            select.innerHTML = [...(tpvState.productos || [])].sort((a,b) => a.nombre.localeCompare(b.nombre)).map(p => `<option value="${p.id}">${p.nombre}</option>`).join("");
            invModalStock.show();
        }

        async function inv_agregarProductoAInventario(){
            const fecha = (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            const productoId = document.getElementById("inv-stock-producto").value;
            const cantidad = parseFloat(document.getElementById("inv-stock-cantidad").value);
            const costo = parseFloat(document.getElementById("inv-stock-costo").value);
            
            if(isNaN(cantidad) || isNaN(costo)){
                return showToast(getLang().toast_invalid_stock_data,"warning");
            }
            
            inv_cargarInventario(fecha);
            const item = tpvState.inventarios[fecha].find(i => i.id === productoId);
            if(item){
                item.cantInicial = cantidad;
                item.precioCosto = costo;
            } else {
                const producto = tpvState.productos.find(p => p.id === productoId);
                if(producto){
                    tpvState.inventarios[fecha].push({
                        id: producto.id, nombre: producto.nombre, categoria: producto.categoria ?? "General", precioVenta: producto.precio, um: producto.um ?? "Un",
                        cantInicial: cantidad, cantFinal: cantidad, vendido: 0, importe: 0, precioCosto: costo, comision: 0, gananciaNeta: 0
                    });
                }
            }
            invModalStock.hide();
            await inv_aplicarGananciaGlobal(fecha);

            // Sincronizar stock al servidor via TPV_API
            if (window.TPV_API) {
                const updates = (tpvState.inventarios[fecha] || []).map(i => ({
                    producto_id: i.id,
                    cant_inicial: i.cantInicial,
                    cant_final: i.cantFinal ?? i.cantInicial,
                    precio_costo: i.precioCosto
                }));
                if (updates.length) {
                    TPV_API.inventario.actualizarStockMasivo(updates).then(result => {
                        if (result && result.ok) console.log('✅ Stock sincronizado al servidor');
                    }).catch(e => console.warn('⚠️ Stock no sincronizado:', e.message));
                }
            }
        }

        // --- LÓGICA DE GESTIÓN (Productos y Categorías) ---
