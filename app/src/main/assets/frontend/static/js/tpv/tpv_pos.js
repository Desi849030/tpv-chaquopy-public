// tpv_pos.js
        function tpv_getStock(productoId) {
            const hoy = getTodayDateString();
            const inv = tpvState.inventarios?.[hoy] || [];
            const item = inv.find(i => i.id === productoId);
            return item ? (item.cantFinal ?? item.cantInicial ?? 0) : null;
        }

        function tpv_stockBadge(stock) {
            if (stock === null) return '';
            const n = parseFloat(stock) || 0;
            let cls, label;
            if      (n >= 24) { cls = 'stock-verde';    label = `${n} uds`; }
            else if (n >= 15) { cls = 'stock-amarillo'; label = `${n} uds`; }
            else if (n >= 2)  { cls = 'stock-naranja';  label = `${n} uds`; }
            else              { cls = 'stock-rojo';      label = n === 0 ? 'Agotado' : `${n} uds`; }
            return `<div class="stock-badge ${cls}">${label}</div>`;
        }

        function tpv_renderizarProductos() { 
            const container = document.getElementById("tpv-productos-container");
            const categoriaSeleccionada = document.getElementById("tpv-category-filter")?.value || "all";
            const lang = getLang();
            
            let productosFiltrados = (categoriaSeleccionada === "all" || !categoriaSeleccionada) 
                ? tpvState.productos 
                : tpvState.productos.filter(p => p.categoria === categoriaSeleccionada);
            
            productosFiltrados.sort((a,b) => a.nombre.localeCompare(b.nombre)); 
            
            if (productosFiltrados.length === 0) {
                container.innerHTML = `<p class="text-center p-3 text-muted">${lang.no_products_in_category}</p>`;
                return;
            }
            
            container.innerHTML = productosFiltrados.map(p => {
                const stock = tpv_getStock(p.id);
                return `
                <div class="col">
                    <div class="product-card" onclick="tpv_mostrarConfirmacionAgregar('${p.id}')">
                        <div class="product-img" style="position:relative;${p.imagen ? `background-image: url('${p.imagen}')` : ""}">
                            ${p.imagen ? "" : '<i class="bi bi-image-alt"></i>'}
                            ${tpv_stockBadge(stock)}
                        </div>
                        <div class="product-info">
                            <div class="product-name">${p.onSale ? '<i class="bi bi-star-fill text-warning me-1"></i>' : ''}${p.nombre}</div>
                            <div class="product-price">${formatCurrency(p.precio)}</div>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }

        function tpv_renderizarFiltroCategorias() {
            const filtro = document.getElementById("tpv-category-filter");
            const lang = getLang();
            const categoriasOrdenadas = [...tpvState.categorias].sort((a, b) => a === 'General' ? -1 : b === 'General' ? 1 : a.localeCompare(b));
            
            filtro.innerHTML = `<option value="all">${lang.all_categories}</option>`;
            filtro.innerHTML += categoriasOrdenadas.map(c => `<option value="${c}">${c}</option>`).join('');
            filtro.onchange = tpv_renderizarProductos;
        }

        function tpv_mostrarConfirmacionAgregar(id){
            const producto = tpvState.productos.find(p => p.id === id);
            if(!producto) return;
            
            document.getElementById("addToCartProductId").value = producto.id;
            document.getElementById("addToCartProductName").innerText = producto.nombre;
            document.getElementById("addToCartProductPrice").innerText = `${getLang().form_label_price}: ${formatCurrency(producto.precio)}`;
            document.getElementById("addToCartQuantity").value = 1;
            addToCartModal.show();
        }

        function tpv_confirmarAgregarAlPedido(){
            const id = document.getElementById("addToCartProductId").value;
            const cantidad = parseInt(document.getElementById("addToCartQuantity").value, 10);
            
            if(isNaN(cantidad) || cantidad < 1){
                showToast(getLang().toast_invalid_quantity,"warning");
                return;
            }
            
            tpv_agregarAlPedido(id, cantidad);
            addToCartModal.hide();
        }

        function tpv_agregarAlPedido(id, cantidad = 1){
            const producto = tpvState.productos.find(p => p.id === id);
            if(!producto) return;
            
            const itemExistente = tpvState.ordenActual.find(item => item.id === id);
            itemExistente ? (itemExistente.cantidad += cantidad) : tpvState.ordenActual.push({ ...producto, cantidad });
            
            showToast(`${cantidad} x ${producto.nombre} añadido a la orden.`, "success");
            tpv_renderizarPedido();
        }

        function tpv_renderizarPedido(){
            const contenedor = document.getElementById("tpv-order-items-container");
            const totalElement = document.getElementById("tpv-total");
            const badge = document.getElementById("order-badge");
            
            if (!contenedor) return; // No existe para este rol
            if(tpvState.ordenActual.length === 0){
                contenedor.innerHTML = `<p class="text-center p-3 text-muted">${getLang().empty_order}</p>`;
                if (totalElement) totalElement.innerText = formatCurrency(0);
                if (badge) badge.classList.add("d-none");
                return;
            }
            
            contenedor.innerHTML = tpvState.ordenActual.map(item => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div><strong class="d-block">${item.nombre}</strong><small class="text-muted">${item.cantidad} x ${formatCurrency(item.precio)}</small></div>
                    <strong>${formatCurrency(item.cantidad * item.precio)}</strong>
                </div>`).join("");
            
            const total = tpvState.ordenActual.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
            totalElement.innerText = formatCurrency(total);
            badge.innerText = tpvState.ordenActual.length;
            badge.classList.remove("d-none");
        }

        function tpv_cancelarPedido(){
            if(tpvState.ordenActual.length > 0 && confirm(getLang().confirm_cancel_order)){
                tpvState.ordenActual = [];
                tpv_renderizarPedido();
                showToast(getLang().toast_order_cancelled, "info");
            }
        }

        function tpv_mostrarModalPago(){
            if(tpvState.ordenActual.length === 0) return;
            const subtotal = tpvState.ordenActual.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
            const desc = tpv_calcularDescuento(subtotal);
            const total = Math.max(0, subtotal - desc);
            document.getElementById("paymentModalTotal").innerText = formatCurrency(total);
            // Mostrar desglose de descuento si aplica
            const descEl = document.getElementById("paymentModalDescuento");
            if (descEl) {
                if (desc > 0) {
                    descEl.innerHTML = `<span class="text-success small">Descuento: -${formatCurrency(desc)}</span>`;
                    descEl.style.display = '';
                } else {
                    descEl.style.display = 'none';
                }
            }
            tpv_cargarDescuentos();
            processPaymentModal.show();
        }

        // Descuento activo seleccionado: { tipo:'porcentaje'|'fijo', valor:N } o null
        let _descuentoActivo = null;

        function tpv_calcularDescuento(subtotal) {
            if (!_descuentoActivo) return 0;
            if (_descuentoActivo.tipo === 'porcentaje') return subtotal * (_descuentoActivo.valor / 100);
            return Math.min(_descuentoActivo.valor, subtotal);
        }

        function tpv_aplicarDescuento(tipo, valor, nombre) {
            _descuentoActivo = tipo ? { tipo, valor, nombre } : null;
            const sub = tpvState.ordenActual.reduce((s,i) => s + i.precio*i.cantidad, 0);
            const desc = tpv_calcularDescuento(sub);
            const total = Math.max(0, sub - desc);
            document.getElementById("paymentModalTotal").innerText = formatCurrency(total);
            const descEl = document.getElementById("paymentModalDescuento");
            if (descEl) {
                if (desc > 0) {
                    descEl.innerHTML = `<span class="text-success small">✅ ${nombre}: -${formatCurrency(desc)}</span>`;
                    descEl.style.display = '';
                } else {
                    descEl.innerHTML = '';
                    descEl.style.display = 'none';
                }
            }
        }

        async function tpv_cargarDescuentos() {
            try {
                const r = await fetch('/api/descuentos', { credentials:'same-origin' });
                const d = await r.json();
                const lista = d.descuentos || [];
                const sel   = document.getElementById('tpv-descuento-sel');
                if (!sel) return;
                sel.innerHTML = '<option value="">Sin descuento</option>' +
                    lista.map(d => `<option value="${d.id}" data-tipo="${d.tipo}" data-valor="${d.valor}" data-nombre="${d.nombre}">${d.nombre} (${d.tipo==='porcentaje'?d.valor+'%':'$'+d.valor})</option>`).join('');
                sel.onchange = () => {
                    const opt = sel.options[sel.selectedIndex];
                    if (opt.value) tpv_aplicarDescuento(opt.dataset.tipo, parseFloat(opt.dataset.valor), opt.dataset.nombre);
                    else tpv_aplicarDescuento(null,0,'');
                };
            } catch(e) {}
        }

        async function tpv_procesarPago(metodo){
            if(tpvState.ordenActual.length === 0) return;
            
            const hoy = getTodayDateString();
            const fechaInventario = (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            tpvState.ventasDiarias[hoy] = tpvState.ventasDiarias[hoy] ?? [];
            
            const subtotal   = tpvState.ordenActual.reduce((s,i) => s + i.precio*i.cantidad, 0);
            const descuento  = tpv_calcularDescuento(subtotal);
            const totalFinal = Math.max(0, subtotal - descuento);

            const ventas = tpvState.ordenActual.map(item => ({
                id: `sale-${Date.now()}-${Math.random()}`,
                productoId: item.id,
                nombre: item.nombre,
                cantidad: item.cantidad,
                precioUnitario: item.precio,
                total: item.precio * item.cantidad,
                descuento: descuento > 0 ? parseFloat((descuento / tpvState.ordenActual.length).toFixed(4)) : 0,
                fecha: new Date().toISOString(),
                metodoPago: metodo
            }));
            
            tpvState.ventasDiarias[hoy].push(...ventas);
            tpvState.historialVentas.push(...ventas);

            // Resetear descuento
            _descuentoActivo = null;
            const sel = document.getElementById('tpv-descuento-sel');
            if (sel) sel.value = '';
            
            ventas.forEach(v => inv_actualizarStockPorVenta(fechaInventario, v.productoId, v.cantidad));
            
            tpvState.ordenActual = [];
            processPaymentModal.hide();
            tpv_renderizarPedido();
            ventas_renderizarTablaHoy();
            registros_renderizar();
            inv_aplicarGananciaGlobal(fechaInventario);
            await saveState();
            showToast(`${getLang().toast_sale_processed} ${descuento > 0 ? '| Descuento: -'+formatCurrency(descuento) : ''}`, "success");

            // Notificar al servidor (inventario diario) y SSE
            const vendedorId = window.AUTH?.usuario?.usuario_id;
            if (vendedorId) {
                ventas.forEach(v => {
                    fetch('/api/inventario/diario/conteo', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vendedor_id:  vendedorId,
                            producto_id:  v.productoId,
                            cant_final:   (() => {
                                const inv = tpvState.inventarios[hoy] || [];
                                const it  = inv.find(i => i.id === v.productoId);
                                return it ? Math.max(0, (it.cantInicial||0) - (it.vendido||0)) : 0;
                            })()
                        })
                    }).catch(() => {});
                });
            }
        }

        async function tpv_procesarPago(metodo){
            if(tpvState.ordenActual.length === 0) return;
            
            const hoy = getTodayDateString();
            const fechaInventario = (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            tpvState.ventasDiarias[hoy] = tpvState.ventasDiarias[hoy] ?? [];
            
            const ventas = tpvState.ordenActual.map(item => ({
                id: `sale-${Date.now()}-${Math.random()}`,
                productoId: item.id,
                nombre: item.nombre,
                cantidad: item.cantidad,
                precioUnitario: item.precio,
                total: item.precio * item.cantidad,
                fecha: new Date().toISOString(),
                metodoPago: metodo
            }));
            
            tpvState.ventasDiarias[hoy].push(...ventas);
            tpvState.historialVentas.push(...ventas);
            
            ventas.forEach(v => inv_actualizarStockPorVenta(fechaInventario, v.productoId, v.cantidad));
            
            tpvState.ordenActual = [];
            processPaymentModal.hide();
            tpv_renderizarPedido();
            ventas_renderizarTablaHoy();
            registros_renderizar();
            inv_aplicarGananciaGlobal(fechaInventario);
            await saveState();
            showToast(getLang().toast_sale_processed, "success");

            // Actualizar cant_vendida en inventario_diario del servidor (para la tabla admin)
            const vendedorId = window.AUTH?.usuario?.usuario_id;
            if (vendedorId) {
                ventas.forEach(v => {
                    fetch('/api/inventario/diario/conteo', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vendedor_id:  vendedorId,
                            producto_id:  v.productoId,
                            cant_final:   (() => {
                                const inv = tpvState.inventarios[hoy] || [];
                                const it  = inv.find(i => i.id === v.productoId);
                                return it ? Math.max(0, (it.cantInicial||0) - (it.vendido||0)) : 0;
                            })()
                        })
                    }).catch(() => {});
                });
            }
        }
        
        function tpv_startScanner(){
            document.getElementById("qr-scanner-container").classList.remove("d-none");
            html5QrCode = new Html5Qrcode("qr-reader");

            const onScanSuccess = (decodedText) => {
                const producto = tpvState.productos.find(p => p.id === decodedText);
                if (producto) {
                    tpv_agregarAlPedido(producto.id, 1);
                } else {
                    showToast(getLang().toast_unrecognized_code(decodedText), "warning");
                }
            };

            html5QrCode.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: { width: 250, height: 250 } },
                onScanSuccess,
                () => {}
            ).catch(() => showToast(getLang().toast_camera_error, "danger"));
        }

        function tpv_stopScanner(){
            const container = document.getElementById("qr-scanner-container");
            if(html5QrCode?.isScanning){
                html5QrCode.stop().finally(() => container.classList.add("d-none"));
            } else {
                container.classList.add("d-none");
            }
        }

        // --- LÓGICA DE VENTAS Y REGISTROS ---
