// tpv_ventas_registros.js — Ventas del día, registros, cierres de caja
        function ventas_renderizarTablaHoy(){
            const hoy = getTodayDateString();
            const tablaBody = document.getElementById("ventas-hoy-tabla");
            if (!tablaBody) return; // No existe para este rol
            const ventasHoy = tpvState.ventasDiarias[hoy] ?? [];
            const lang = getLang();
            
            const _fechaEl = document.getElementById("ventas-fecha-hoy");
            if (_fechaEl) _fechaEl.innerText = new Date().toLocaleDateString();
            
            if(ventasHoy.length === 0){
                tablaBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">${lang.no_sales_today}</td></tr>`;
                const _totEl = document.getElementById("ventas-total-vendido-hoy"); if(_totEl) _totEl.innerText = formatCurrency(0);
                return;
            }
            
            const esVend = window.AUTH?.usuario?.rol === 'vendedor';
            tablaBody.innerHTML = ventasHoy.map(venta => `
                <tr>
                    <td>${new Date(venta.fecha).toLocaleTimeString()}</td>
                    <td>${venta.nombre}</td>
                    <td>${venta.cantidad}</td>
                    <td>${formatCurrency(venta.precioUnitario)}</td>
                    <td>${formatCurrency(venta.total)}</td>
                    <td>
                        ${esVend ? '' : `
                        <button class="btn btn-sm btn-warning" onclick="ventas_editarVenta('${venta.id}')"><i class="bi bi-pencil-fill"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="ventas_eliminarVenta('${venta.id}')"><i class="bi bi-trash-fill"></i></button>`}
                    </td>
                </tr>`).join("");
            
            const _totFin = document.getElementById("ventas-total-vendido-hoy"); if(_totFin) _totFin.innerText = formatCurrency(ventasHoy.reduce((s, v) => s + v.total, 0));
        }

        function ventas_editarVenta(id){
            const venta = (tpvState.ventasDiarias[getTodayDateString()] ?? []).find(v => v.id === id);
            if(!venta) return;
            
            document.getElementById("editSaleId").value = id;
            document.getElementById("editSaleProductName").innerText = venta.nombre;
            document.getElementById("editSaleQuantity").value = venta.cantidad;
            editSaleModal.show();
        }

        async function ventas_guardarEdicion(){
            const id = document.getElementById("editSaleId").value;
            const nuevaCantidad = parseInt(document.getElementById("editSaleQuantity").value, 10);
            const hoy = getTodayDateString();
            
            if(isNaN(nuevaCantidad) || nuevaCantidad < 0){
                showToast(getLang().toast_invalid_amount,"danger");
                return;
            }
            
            const ventaHoy = (tpvState.ventasDiarias[hoy] ?? []).find(v => v.id === id);
            const ventaHistorial = tpvState.historialVentas.find(v => v.id === id);
            if(!ventaHoy || !ventaHistorial) return;
            
            const diferencia = nuevaCantidad - ventaHoy.cantidad;
            
            if(nuevaCantidad === 0){
                await ventas_eliminarVenta(id, true);
            } else {
                ventaHoy.cantidad = nuevaCantidad;
                ventaHoy.total = ventaHoy.precioUnitario * nuevaCantidad;
                ventaHistorial.cantidad = nuevaCantidad;
                ventaHistorial.total = ventaHistorial.precioUnitario * nuevaCantidad;
                inv_actualizarStockPorVenta((document.getElementById("inv-fechaActual")?.value ?? getTodayDateString()), ventaHoy.productoId, diferencia);
            }
            
            editSaleModal.hide();
            ventas_renderizarTablaHoy();
            registros_renderizar();
            await inv_aplicarGananciaGlobal();
            showToast(getLang().toast_sale_updated,"success");
        }

        async function ventas_eliminarVenta(id, confirmado = false){
            const lang = getLang();
            if(!confirmado && !confirm(lang.confirm_delete_sale)) return;
            
            const hoy = getTodayDateString();
            const indexHoy = (tpvState.ventasDiarias[hoy] ?? []).findIndex(v => v.id === id);
            if(indexHoy === -1) return;
            
            const venta = tpvState.ventasDiarias[hoy][indexHoy];
            inv_actualizarStockPorVenta((document.getElementById("inv-fechaActual")?.value ?? getTodayDateString()), venta.productoId, -venta.cantidad);
            
            tpvState.ventasDiarias[hoy].splice(indexHoy, 1);
            tpvState.historialVentas = tpvState.historialVentas.filter(v => v.id !== id);
            
            ventas_renderizarTablaHoy();
            registros_renderizar();
            await inv_aplicarGananciaGlobal();
            showToast(lang.toast_sale_deleted,"info");
        }

        function registros_renderizar(){
            const tablaCierres = document.getElementById("registros-cierres-tabla");
            const tablaVentas = document.getElementById("registros-ventas-tabla");
            const lang = getLang();
            
            const cierres = tpvState.cierresCaja ?? [];
            tablaCierres.innerHTML = cierres.length === 0
                ? `<tr><td colspan="6" class="text-center text-muted">${lang.no_closures}</td></tr>`
                : [...cierres].sort((a, b) => new Date(b.fecha) - new Date(a.fecha)).map((c, index) => `
                    <tr>
                        <td>
                            ${new Date(c.fecha + "T00:00:00").toLocaleDateString()}
                            ${c.codigoAprendizaje ? `<br><small class="badge bg-warning text-dark mt-1"><i class="bi bi-lightbulb"></i> ${c.codigoAprendizaje}</small>` : ''}
                        </td>
                        <td class="money-column">${formatCurrency(c.ventas)}</td>
                        <td class="money-column">${formatCurrency(c.costo)}</td>
                        <td class="money-column">${formatCurrency(c.comision)}</td>
                        <td class="fw-bold money-column ${c.gananciaNeta >= 0 ? "text-success" : "text-danger"}">${formatCurrency(c.gananciaNeta)}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="eliminar_cierre('${c.fecha}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>`).join('');
            
            const historial = tpvState.historialVentas ?? [];
            tablaVentas.innerHTML = historial.length === 0
                ? `<tr><td colspan="5" class="text-center text-muted">${lang.no_sales_history}</td></tr>`
                : [...historial].sort((a, b) => new Date(b.fecha) - new Date(a.fecha)).map((v, index) => `
                    <tr>
                        <td>${new Date(v.fecha).toLocaleString()}</td>
                        <td>${v.nombre}</td>
                        <td>${v.cantidad}</td>
                        <td class="money-column">${formatCurrency(v.total)}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="eliminar_venta_individual(${index})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>`).join('');
        }

        async function caja_cerrarDia(){
            const fecha = (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            const lang = getLang();
            
            if(tpvState.cierresCaja.some(c => c.fecha === fecha)){
                return showToast(lang.toast_day_already_closed(fecha),"warning");
            }
            if(!tpvState.inventarios[fecha]){
                return showToast(lang.toast_no_inventory_data,"danger");
            }
            
            // CORRECCIÓN: Solicitar código de aprendizaje antes de cerrar
            const codigoAprendizaje = prompt("📝 Código de Aprendizaje para el próximo día:\n\n(Opcional: Anota algo que mejorar o aprender para mañana)") || "";
            
            await inv_aplicarGananciaGlobal(fecha);
            const resumen = tpvState.inventarios[fecha].reduce((t, i) => ({
                ventas: t.ventas + i.importe,
                costo: t.costo + (i.vendido * i.precioCosto),
                comision: t.comision + i.comision,
                gananciaNeta: t.gananciaNeta + i.gananciaNeta
            }), {ventas:0, costo:0, comision:0, gananciaNeta:0});
            
            // CORRECCIÓN: Guardar código de aprendizaje con el cierre
            tpvState.cierresCaja.push({ fecha, ...resumen, codigoAprendizaje });
            
            // CORRECCIÓN: Mostrar código para el siguiente día
            if (codigoAprendizaje) {
                tpvState.codigoAprendizajeActual = codigoAprendizaje;
                setTimeout(() => {
                    alert(`🎯 CÓDIGO DE APRENDIZAJE PARA HOY:\n\n"${codigoAprendizaje}"\n\n¡Recuerda aplicarlo durante el día!`);
                }, 500);
            }
            
            // Crear copia de seguridad automática
            await crear_backup_automatico('cierre_dia');
            await saveState();

            // Actualizar inventario_general con las cantidades finales del día
            try {
                const itemsCierre = (tpvState.inventarios[fecha] || []).map(i => ({
                    producto_id: i.id,
                    cant_final:  Math.max(0, (i.cantFinal ?? i.cantInicial ?? 0))
                }));
                if (itemsCierre.length) {
                    const rC = await fetch('/api/inventario/cierre-admin', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fecha, items: itemsCierre })
                    });
                    const dC = await rC.json();
                    if (dC.ok) {
                        dbg(`✅ Almacén actualizado al cierre: ${dC.actualizados} productos`);
                    }
                }
            } catch(e) {
                dbg('⚠️ cierre-admin: ' + e.message);
            }

            showToast(lang.toast_day_closed(fecha), "success");
            registros_renderizar();
        }

        // --- LÓGICA DE INVENTARIO ---
        function eliminar_backup_individual(backupKey) {
            if (confirm('¿Está seguro de eliminar esta copia de seguridad?')) {
                tpvStorage.removeItem(backupKey);
                showToast('Copia eliminada', 'info');
                actualizar_lista_backups();
            }
        }
        
        function eliminar_backups() {
            if (confirm('¿Está seguro de eliminar TODAS las copias de seguridad?')) {
                const allBackups = tpvStorage.keys().filter(key => key.startsWith('tpv_backup_'));
                allBackups.forEach(key => tpvStorage.removeItem(key));
                showToast('Todas las copias han sido eliminadas', 'warning');
                actualizar_lista_backups();
            }
        }
        
        // ========== FUNCIONES DE EXPORTACIÓN DE VENTAS ==========
        
        // NUEVO: Sistema de exportación mejorado para móviles con selector de ubicación
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
