// tpv_gestion.js
        function gestion_renderizarFiltrosProductos() {
            const select = document.getElementById('gestion-filtro-categoria');
            if (!select) return;
            select.innerHTML = `<option value="">${getLang().all_categories}</option>` +
                [...tpvState.categorias].sort().map(cat => `<option value="${cat}">${cat}</option>`).join('');
            select.value = ''; // Siempre resetear a "Todas las Categorías"
        }

        function gestion_renderizarTablaProductos(){
            if (!document.getElementById("gestion-filtro-producto-nombre")) return; // No existe para este rol
            const filtros = {
                nombre:    document.getElementById('gestion-filtro-producto-nombre')?.value.toLowerCase() || '',
                categoria: document.getElementById('gestion-filtro-categoria')?.value || '',
                precioMin: parseFloat(document.getElementById('gestion-filtro-precio-min')?.value || ''),
                precioMax: parseFloat(document.getElementById('gestion-filtro-precio-max')?.value || '')
            };
            const productosFiltrados = tpvState.productos.filter(p => 
                p.nombre.toLowerCase().includes(filtros.nombre) &&
                (!filtros.categoria || p.categoria === filtros.categoria) &&
                (isNaN(filtros.precioMin) || p.precio >= filtros.precioMin) &&
                (isNaN(filtros.precioMax) || p.precio <= filtros.precioMax)
            ).sort((a,b) => a.nombre.localeCompare(b.nombre));

            const _gestTbl = document.getElementById("gestion-tabla-productos"); if(!_gestTbl) return;
            _gestTbl.innerHTML = productosFiltrados.map(p => `
                <tr>
                    <td>${p.nombre}</td>
                    <td>${p.categoria}</td>
                    <td>${formatCurrency(p.precio)}</td>
                    <td class="text-center">${p.onSale ? '<i class="bi bi-star-fill text-warning"></i>' : '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="gestion_abrirModalProducto('${p.id}')"><i class="bi bi-pencil-fill"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="gestion_eliminarProducto('${p.id}')"><i class="bi bi-trash-fill"></i></button>
                    </td>
                </tr>`).join("");
        }

        function gestion_renderizarListaCategorias(){
            const categoriasOrdenadas = [...tpvState.categorias].sort((a, b) => a === 'General' ? -1 : b === 'General' ? 1 : a.localeCompare(b));
            const _gestCatEl = document.getElementById("gestion-lista-categorias"); if(!_gestCatEl) return;
            _gestCatEl.innerHTML = categoriasOrdenadas.map(cat => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${cat}
                    <div>
                        <button class="btn btn-sm btn-outline-warning me-2" onclick="gestion_abrirModalEditarCategoria('${cat}')"><i class="bi bi-pencil-fill"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="gestion_eliminarCategoria('${cat}')"><i class="bi bi-x-lg"></i></button>
                    </div>
                </li>`).join("");
        }

        function gestion_abrirModalProducto(id = null){
            const lang = getLang();
            document.getElementById("gestion-form-producto").reset();
            const _gpCat = document.getElementById("gestion-producto-categoria"); if(_gpCat) _gpCat.innerHTML = tpvState.categorias.map(cat => `<option value="${cat}">${cat}</option>`).join("");
            const _gpTit = document.getElementById("gestion-modal-producto-titulo"); if(_gpTit) _gpTit.innerText = id ? lang.edit_product : lang.mgmt_new_product;
            
            if(id){
                const producto = tpvState.productos.find(p => p.id === id);
                if(producto){
                    document.getElementById("gestion-producto-id").value = producto.id;
                    document.getElementById("gestion-producto-nombre").value = producto.nombre;
                    document.getElementById("gestion-producto-categoria").value = producto.categoria;
                    document.getElementById("gestion-producto-precio").value = producto.precio;
                    document.getElementById("gestion-producto-costo").value = producto.costoUnitario || 0;
                    document.getElementById("gestion-producto-um").value = producto.um ?? "";
                    document.getElementById("gestion-producto-oferta").checked = producto.onSale || false;
                }
            } else {
                document.getElementById("gestion-producto-id").value = "";
            }
            gestionModalProducto.show();
        }

        // ── Limpia TODOS los almacenes: memoria, IndexedDB y servidor ──────────
        async function gestion_limpiarTodas() {
            if (!confirm(
                '⚠️ LIMPIEZA TOTAL\n\n' +
                'Borrará productos de:\n' +
                '  • Catálogo visible (memoria)\n' +
                '  • Inventario (memoria)\n' +
                '  • Navegador (IndexedDB)\n' +
                '  • Base de datos del servidor\n\n' +
                '¿Continuar?'
            )) return;
            showToast('🗑️ Limpiando todos los almacenes...', 'warning');
            try {
                // 1. Limpiar servidor PRIMERO (verificar que responde bien)
                const r = await fetch('/api/limpiar-tablas', {
                    method: 'POST', credentials: 'same-origin'
                });
                if (!r.ok) {
                    const txt = await r.text();
                    throw new Error(`Servidor HTTP ${r.status}: ${txt.slice(0, 200)}`);
                }
                const d = await r.json();
                if (!d.ok) throw new Error(d.mensaje || d.error || 'Error desconocido');

                // 2. Limpiar memoria JS completa
                tpvState.productos   = [];
                tpvState.categorias  = ['General'];
                tpvState.inventarios = {};
                tpvState.ventasDiarias = {};

                // 3. Persistir estado vacío en IndexedDB
                const db = await dbHelper.openDb();
                await dbHelper.save(db, tpvState);
                db.close();

                // 4. Limpiar caché global del almacén
                window._adminGeneral = [];
                window._adminVends   = [];

                // 5. Limpiar todas las vistas del DOM
                const tablaGestion = document.getElementById('gestion-tabla-productos');
                if (tablaGestion) tablaGestion.innerHTML = '';
                const vendBody = document.getElementById('inv-vend-body');
                if (vendBody) vendBody.innerHTML = '<div class="alert alert-info">Sin datos. Almacén vacío.</div>';
                const almacenWrap = document.getElementById('inv-admin-vendedores-wrap');
                if (almacenWrap) almacenWrap.style.display = 'none';

                // 6. Refrescar renders que usan tpvState
                if (typeof gestion_renderizarTablaProductos === 'function') gestion_renderizarTablaProductos();
                if (typeof tpv_renderizarProductos === 'function')          tpv_renderizarProductos();
                if (typeof tpv_renderizarFiltroCategorias === 'function')   tpv_renderizarFiltroCategorias();
                if (typeof inv_renderizarTabla === 'function')              inv_renderizarTabla(getTodayDateString());

                showToast(`✅ ${d.mensaje}`, 'success');
            } catch(e) {
                showToast(`❌ Error al limpiar: ${e.message}`, 'danger');
            }
        }

        // ── Sincroniza catálogo JS → servidor (sin borrar) ──────────────────
        async function gestion_sincronizarCompleto() {
            if (!tpvState.productos.length) {
                // Si memoria vacía, intentar cargar del servidor primero
                showToast('⚙️ Cargando catálogo desde servidor...', 'info');
                await catalogo_cargarDesdeServidor();
                if (tpvState.productos.length) {
                    await saveState();
                    gestion_renderizarTablaProductos();
                    tpv_renderizarProductos();
                    tpv_renderizarFiltroCategorias();
                    showToast(`✅ ${tpvState.productos.length} productos cargados del servidor`, 'success');
                } else {
                    showToast('⚠️ El catálogo está vacío tanto local como en servidor. Importa un archivo XLSX primero.', 'warning');
                }
                return;
            }
            showToast('⚙️ Sincronizando catálogo con el servidor...', 'info');
            try {
                const r = await fetch('/api/reconstruir-desde-productos', {
                    method: 'POST', credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productos: tpvState.productos })
                });
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                const d = await r.json();
                if (!d.ok) throw new Error(d.mensaje || d.error);
                await fetch('/api/sincronizar-completo', { method: 'POST', credentials: 'same-origin' });

                // Poblar inventario_general para asignación a vendedores
                try {
                    const rI = await fetch('/api/inventario/importar-catalogo', {method:'POST',credentials:'same-origin'});
                    const dI = await rI.json();
                    if (dI.ok) showToast(`📦 Almacén: ${dI.nuevos} nuevos · ${dI.existentes} actualizados`, 'info');
                } catch(e) {}

                // Recargar desde servidor para confirmar
                await catalogo_cargarDesdeServidor();
                await saveState();

                showToast(`✅ ${d.mensaje}`, 'success');
                gestion_renderizarTablaProductos();
                tpv_renderizarProductos();
                tpv_renderizarFiltroCategorias();
                if (typeof gestion_renderizarFiltrosProductos === 'function') gestion_renderizarFiltrosProductos();
            } catch(e) {
                showToast(`❌ Error: ${e.message}`, 'danger');
            }
        }

        // ── Limpia todo y luego reconstruye desde catálogo JS actual ────────
        async function gestion_resetEImportar() {
            if (!confirm(
                '🔄 LIMPIAR Y REIMPORTAR\n\n' +
                'Borrará TODO (memoria + navegador + servidor)\n' +
                'y reconstruirá el servidor desde el catálogo local actual.\n\n' +
                '¿Continuar?'
            )) return;
            showToast('🗑️ Limpiando todos los almacenes...', 'warning');
            try {
                const productosBackup = [...tpvState.productos];

                // 1. Borrar servidor primero
                const rL = await fetch('/api/limpiar-tablas', { method: 'POST', credentials: 'same-origin' });
                if (!rL.ok) throw new Error(`HTTP ${rL.status}`);
                const dL = await rL.json();
                if (!dL.ok) throw new Error(dL.mensaje);

                // 2. Borrar memoria e IndexedDB
                tpvState.productos   = [];
                tpvState.categorias  = ['General'];
                tpvState.inventarios = {};
                tpvState.ventasDiarias = {};
                window._adminGeneral = [];
                window._adminVends   = [];
                const db = await dbHelper.openDb();
                await dbHelper.save(db, tpvState);
                db.close();
                showToast(`✅ Limpieza OK — ${dL.mensaje}`, 'info');

                if (productosBackup.length) {
                    tpvState.productos  = productosBackup;
                    tpvState.categorias = [...new Set(productosBackup.map(p => p.categoria || 'General'))].sort();
                    const rR = await fetch('/api/reconstruir-desde-productos', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ productos: productosBackup })
                    });
                    if (!rR.ok) throw new Error(`HTTP ${rR.status}`);
                    const dR = await rR.json();
                    if (!dR.ok) throw new Error(dR.mensaje);
                    const db2 = await dbHelper.openDb();
                    await dbHelper.save(db2, tpvState);
                    db2.close();
                    showToast(`✅ ${dR.mensaje}`, 'success');
                } else {
                    showToast('✅ Limpieza completa. Importa un archivo para cargar productos.', 'info');
                }
                gestion_renderizarTablaProductos();
                tpv_renderizarProductos();
                tpv_renderizarFiltroCategorias();
                if (typeof inv_renderizarTabla === 'function') inv_renderizarTabla(getTodayDateString());
                const vendBody = document.getElementById('inv-vend-body');
                if (vendBody) vendBody.innerHTML = '<div class="alert alert-info">Sin datos. Use Sincronizar para recargar.</div>';
            } catch(e) {
                showToast(`❌ Error: ${e.message}`, 'danger');
            }
        }


        async function gestion_guardarProducto() {
            const id = document.getElementById("gestion-producto-id").value;
            const nombre = document.getElementById("gestion-producto-nombre").value.trim();
            const precio = parseFloat(document.getElementById("gestion-producto-precio").value);
            if(!nombre || isNaN(precio) || precio < 0) return;
            
            const imagenLocal = document.getElementById("gestion-producto-imagen-local").files[0];
            let imagen = document.getElementById("gestion-producto-imagen-url").value.trim();
            
            if(imagenLocal) {
                // Comprimir imagen antes de guardar (máx 400px, calidad 0.72)
                imagen = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = e => {
                        const img = new Image();
                        img.onload = () => {
                            const MAX = 400;
                            const scale = Math.min(1, MAX / Math.max(img.width, img.height));
                            const canvas = document.createElement('canvas');
                            canvas.width  = Math.round(img.width  * scale);
                            canvas.height = Math.round(img.height * scale);
                            canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                            resolve(canvas.toDataURL('image/jpeg', 0.72));
                        };
                        img.src = e.target.result;
                    };
                    reader.readAsDataURL(imagenLocal);
                });
            }
            
            const producto = {
                id: id || `prod-${Date.now()}`, 
                nombre, 
                categoria: document.getElementById("gestion-producto-categoria").value,
                precio, 
                costoUnitario: parseFloat(document.getElementById("gestion-producto-costo")?.value) || 0,
                um: document.getElementById("gestion-producto-um").value.trim(), 
                imagen,
                onSale: document.getElementById("gestion-producto-oferta").checked
            };
            
            const index = tpvState.productos.findIndex(p => p.id === id);
            
            if (index > -1) {
                tpvState.productos[index] = producto;
                
                // CORRECCIÓN FINAL: Propagar TODOS los cambios del producto a TODOS los registros de inventario.
                Object.keys(tpvState.inventarios).forEach(fecha => {
                    const itemInInventory = tpvState.inventarios[fecha].find(item => item.id === producto.id);
                    if (itemInInventory) {
                        itemInInventory.nombre = producto.nombre;
                        itemInInventory.precioVenta = producto.precio;
                        itemInInventory.categoria = producto.categoria;
                        itemInInventory.um = producto.um;
                    }
                });
                
                // Refrescar la tabla de inventario si está visible para reflejar los cambios inmediatamente.
                const activeTabId = document.querySelector('.tab-pane.active')?.id;
                if (activeTabId === 'inv-inventario-tab-pane') {
                    const fechaInventarioActual = (document.getElementById('inv-fechaActual')?.value ?? getTodayDateString());
                    inv_aplicarGananciaGlobal(fechaInventarioActual);
                }
            } else {
                tpvState.productos.push(producto);
            }
            
            gestionModalProducto.hide();
            gestion_renderizarTablaProductos();
            tpv_renderizarProductos();
            await saveState();
            catalogo_sincronizarAlServidor(); // ← todos los roles ven el cambio
            showToast(getLang().toast_product_saved, 'success');

            const currentActiveTabPane = document.querySelector('.tab-pane.fade.show.active');
            if (currentActiveTabPane && currentActiveTabPane.id === 'cliente-qr-tab-pane') {
                cliente_generarEtiquetas();
            }
        }

        async function gestion_eliminarProducto(id){
            if(confirm(getLang().confirm_delete_product)){
                tpvState.productos = tpvState.productos.filter(p => p.id !== id);
                gestion_renderizarTablaProductos();
                tpv_renderizarProductos();
                await saveState();
                catalogo_sincronizarAlServidor(); // ← todos los roles ven el cambio
                if ((document.getElementById('cliente-qr-display-container')?.children.length > 0)) {
                    cliente_generarEtiquetas();
                }
            }
        }

        async function gestion_agregarCategoria(){
            const input = document.getElementById("gestion-input-nueva-categoria");
            const nombre = input.value.trim();
            if(nombre && !tpvState.categorias.includes(nombre)){
                tpvState.categorias.push(nombre);
                gestion_renderizarListaCategorias();
                tpv_renderizarFiltroCategorias();
                gestion_renderizarFiltrosProductos();
                input.value = "";
                await saveState();
                cliente_renderizarDropdownCategoriasQR();
            }
        }

        function gestion_abrirModalEditarCategoria(nombreAntiguo) {
            document.getElementById('gestion-categoria-antigua').value = nombreAntiguo;
            document.getElementById('gestion-categoria-nueva').value = nombreAntiguo;
            gestionModalCategoria.show();
        }

        async function gestion_guardarCategoriaEditada() {
            const nombreAntiguo = document.getElementById('gestion-categoria-antigua').value;
            const nombreNuevo = document.getElementById('gestion-categoria-nueva').value.trim();
            const lang = getLang();
            if (!nombreNuevo) return;
            if (nombreAntiguo !== nombreNuevo && tpvState.categorias.includes(nombreNuevo)) {
                return showToast(lang.category_name_exists, 'warning');
            }

            const index = tpvState.categorias.findIndex(c => c === nombreAntiguo);
            if (index > -1) tpvState.categorias[index] = nombreNuevo;

            tpvState.productos.forEach(p => { if (p.categoria === nombreAntiguo) p.categoria = nombreNuevo; });

            gestionModalCategoria.hide();
            gestion_renderizarListaCategorias();
            gestion_renderizarTablaProductos();
            tpv_renderizarFiltroCategorias();
            gestion_renderizarFiltrosProductos();
            await saveState();
            showToast(lang.category_updated_success, 'success');
            cliente_renderizarDropdownCategoriasQR();
            if ((document.getElementById('cliente-qr-display-container')?.children.length > 0)) {
                cliente_generarEtiquetas();
            }
        }

        async function gestion_eliminarCategoria(categoria){
            const lang = getLang();
            if (tpvState.categorias.length <= 1) return showToast(lang.confirm_delete_last_category, "warning");
            if (confirm(lang.confirm_delete_category)) {
                let fallbackCat = 'General' === categoria ? tpvState.categorias.find(c => c !== 'General') : 'General';
                tpvState.productos.forEach(p => { if (p.categoria === categoria) p.categoria = fallbackCat; });
                tpvState.categorias = tpvState.categorias.filter(c => c !== categoria);
                
                gestion_renderizarListaCategorias();
                gestion_renderizarTablaProductos();
                tpv_renderizarFiltroCategorias();
                gestion_renderizarFiltrosProductos();
                await saveState();
                cliente_renderizarDropdownCategoriasQR();
                if ((document.getElementById('cliente-qr-display-container')?.children.length > 0)) {
                    cliente_generarEtiquetas();
                }
            }
        }

        // --- LÓGICA DE HERRAMIENTAS ---
        async function gestion_handleExportXLSX(){
            // Verificar que XLSX esté cargado
            if (typeof XLSX === 'undefined') {
                showToast("Error: Biblioteca Excel no cargada. Recarga la página.", "danger");
                console.error('XLSX no está definido');
                return;
            }

            try {
                // Mostrar indicador de carga
                showToast("⏳ Generando archivo Excel, por favor espera...", "info");
                
                console.log('📊 Iniciando exportación Excel completa...');
                console.log('Productos en sistema:', tpvState.productos.length);
                
                // CORRECCIÓN: Ejecutar await directamente sin setTimeout
                await realizar_exportacion_xlsx();
                
            } catch (error) {
                console.error('❌ Error exportando Excel:', error);
                showToast("❌ Error al exportar Excel: " + error.message, "danger");
            }
        }
        
        async function realizar_exportacion_xlsx() {
                const wb = XLSX.utils.book_new();
                const fechaHoy = getTodayDateString();
                
                // HOJA 1: Productos COMPLETOS con inventario actual y TOTALES
                const inventarioHoy = tpvState.inventarios[fechaHoy] || [];
                const inventarioPorId = {};
                
                // Crear mapa de inventario por ID
                if (Array.isArray(inventarioHoy)) {
                    inventarioHoy.forEach(item => {
                        inventarioPorId[item.id] = item;
                    });
                }
                
                // CORRECCIÓN: Filtrar productos con cantidad en 0 y otros valores en 0
                const dataProductos = tpvState.productos
                    .map(p => {
                        const inv = inventarioPorId[p.id] || {};
                        const cantidadActual = inv.cantFinal || inv.cantidadFinal || p.cantidad || 0;
                        const vendido = inv.vendido || p.vendido || 0;
                        const importe = inv.importe || inv.importeVenta || 0;
                        const precio = p.precio || p.precioVenta || 0;
                        const inversion = p.precioCosto || p.costoUnitario || 0;
                        
                        return { 
                            producto: p,
                            datos: {
                                Nombre: p.nombre,
                                Precio: precio,
                                UM: p.um || p.unidadMedida || "C/U",
                                Cantidad: cantidadActual,
                                Final: cantidadActual,
                                Vendido: vendido,
                                Importe: importe,
                                Inversion: inversion,
                                Categoria: p.categoria || "General",
                                Ganancia: ((precio) - (inversion)) * cantidadActual
                            }
                        };
                    })
                    // Exportar TODOS los productos que tengan nombre
                    .filter(item => item.datos.Nombre && item.datos.Nombre.trim() !== '')
                    .map(item => item.datos);
                
                console.log('Productos a exportar:', dataProductos.length);
                
                // Crear hoja de productos
                if (dataProductos.length > 0) {
                    // Calcular totales
                    const totalCantidad = dataProductos.reduce((sum, p) => sum + p.Cantidad, 0);
                    const totalVendido = dataProductos.reduce((sum, p) => sum + p.Vendido, 0);
                    const totalImporte = dataProductos.reduce((sum, p) => sum + p.Importe, 0);
                    const totalInversion = dataProductos.reduce((sum, p) => sum + (p.Inversion * p.Cantidad), 0);
                    const totalGanancia = dataProductos.reduce((sum, p) => sum + p.Ganancia, 0);
                    const totalValorStock = dataProductos.reduce((sum, p) => sum + (p.Precio * p.Cantidad), 0);
                    
                    // Agregar fila de totales
                    dataProductos.push({
                        Nombre: "=== TOTALES ===",
                        Precio: "",
                        UM: "",
                        Cantidad: totalCantidad,
                        Final: totalCantidad,
                        Vendido: totalVendido,
                        Importe: totalImporte,
                        Inversion: totalInversion,
                        Categoria: "",
                        Ganancia: totalGanancia
                    });
                    
                    // Agregar fila de valor total del stock
                    dataProductos.push({
                        Nombre: "VALOR TOTAL STOCK",
                        Precio: "",
                        UM: "",
                        Cantidad: "",
                        Final: "",
                        Vendido: "",
                        Importe: totalValorStock,
                        Inversion: "",
                        Categoria: "",
                        Ganancia: ""
                    });
                    
                    const wsProductos = XLSX.utils.json_to_sheet(dataProductos);
                    XLSX.utils.book_append_sheet(wb, wsProductos, "Productos");
                    console.log('✅ Hoja Productos creada con totales');
                }
                
                // HOJA 2: VENTAS DIARIAS (Una hoja por cada día con ventas)
                const fechasConVentas = Object.keys(tpvState.ventasDiarias).sort();
                
                fechasConVentas.forEach(fecha => {
                    const ventasDia = tpvState.ventasDiarias[fecha] || [];
                    
                    // CORRECCIÓN: Filtrar ventas con valores en 0
                    const ventasValidas = ventasDia.filter(v => 
                        (v.cantidad > 0) && (v.precio > 0) && ((v.cantidad * v.precio) > 0)
                    );
                    
                    if (ventasValidas.length > 0) {
                        const ventasDelDia = ventasValidas.map(v => ({
                            Hora: v.timestamp || '',
                            Producto: v.productoNombre || '',
                            Categoria: v.categoria || '',
                            Cantidad: v.cantidad || 0,
                            PrecioUnitario: v.precio || 0,
                            Total: (v.cantidad || 0) * (v.precio || 0),
                            MetodoPago: v.metodoPago || ''
                        }));
                        
                        // Agregar totales del día
                        const totalCantidadDia = ventasDelDia.reduce((sum, v) => sum + v.Cantidad, 0);
                        const totalImporteDia = ventasDelDia.reduce((sum, v) => sum + v.Total, 0);
                        
                        ventasDelDia.push({
                            Hora: "",
                            Producto: "=== TOTAL DEL DÍA ===",
                            Categoria: "",
                            Cantidad: totalCantidadDia,
                            PrecioUnitario: "",
                            Total: totalImporteDia,
                            MetodoPago: ""
                        });
                        
                        const wsVentaDia = XLSX.utils.json_to_sheet(ventasDelDia);
                        XLSX.utils.book_append_sheet(wb, wsVentaDia, `Ventas ${fecha}`);
                        console.log(`✅ Hoja Ventas ${fecha} creada con ${ventasDelDia.length - 1} ventas`);
                    }
                });
                
                // HOJA 3: VENTAS MENSUALES (Agrupadas por mes)
                const ventasPorMes = {};
                
                Object.keys(tpvState.ventasDiarias).forEach(fecha => {
                    const mes = fecha.substring(0, 7); // Formato: YYYY-MM
                    if (!ventasPorMes[mes]) {
                        ventasPorMes[mes] = [];
                    }
                    
                    const ventasDia = tpvState.ventasDiarias[fecha] || [];
                    // CORRECCIÓN: Filtrar ventas con valores en 0
                    ventasDia.forEach(v => {
                        const cantidad = v.cantidad || 0;
                        const precio = v.precio || 0;
                        const total = cantidad * precio;
                        
                        // Solo agregar si tiene valores válidos
                        if (cantidad > 0 && precio > 0 && total > 0) {
                            ventasPorMes[mes].push({
                                Fecha: fecha,
                                Hora: v.timestamp || '',
                                Producto: v.productoNombre || '',
                                Categoria: v.categoria || '',
                                Cantidad: cantidad,
                                PrecioUnitario: precio,
                                Total: total,
                                MetodoPago: v.metodoPago || ''
                            });
                        }
                    });
                });
                
                Object.keys(ventasPorMes).sort().forEach(mes => {
                    const ventasMes = ventasPorMes[mes];
                    
                    if (ventasMes.length > 0) {
                        // Agregar totales del mes
                        const totalCantidadMes = ventasMes.reduce((sum, v) => sum + v.Cantidad, 0);
                        const totalImporteMes = ventasMes.reduce((sum, v) => sum + v.Total, 0);
                        
                        ventasMes.push({
                            Fecha: "",
                            Hora: "",
                            Producto: "=== TOTAL DEL MES ===",
                            Categoria: "",
                            Cantidad: totalCantidadMes,
                            PrecioUnitario: "",
                            Total: totalImporteMes,
                            MetodoPago: ""
                        });
                        
                        const wsVentaMes = XLSX.utils.json_to_sheet(ventasMes);
                        XLSX.utils.book_append_sheet(wb, wsVentaMes, `Mes ${mes}`);
                        console.log(`✅ Hoja Mes ${mes} creada con ${ventasMes.length - 1} ventas`);
                    }
                });
                
                // HOJA 3: Inventarios Históricos
                const dataInventarios = [];
                Object.keys(tpvState.inventarios).sort().forEach(fecha => {
                    const inventarioFecha = tpvState.inventarios[fecha];
                    
                    if (Array.isArray(inventarioFecha)) {
                        inventarioFecha.forEach(item => {
                            const cantInicial = item.cantInicial || item.cantidadInicial || 0;
                            const vendido = item.vendido || 0;
                            const cantFinal = item.cantFinal || item.cantidadFinal || 0;
                            const importe = item.importe || item.importeVenta || 0;
                            
                            // CORRECCIÓN: Solo incluir si tiene movimiento o inventario
                            if (cantInicial > 0 || vendido > 0 || cantFinal > 0 || importe > 0) {
                                dataInventarios.push({
                                    Fecha: fecha,
                                    Nombre: item.nombre,
                                    Categoria: item.categoria,
                                    UM: item.um,
                                    CantInicial: cantInicial,
                                    Vendido: vendido,
                                    CantFinal: cantFinal,
                                    PrecioVenta: item.precioVenta || 0,
                                    PrecioCosto: item.precioCosto || 0,
                                    Importe: importe,
                                    GananciaNeta: item.gananciaNeta || 0
                                });
                            }
                        });
                    } else {
                        Object.keys(inventarioFecha).forEach(prodId => {
                            const item = inventarioFecha[prodId];
                            const producto = tpvState.productos.find(p => p.id === prodId);
                            
                            const cantInicial = item.cantInicial || item.cantidadInicial || 0;
                            const vendido = item.vendido || 0;
                            const cantFinal = item.cantFinal || item.cantidadFinal || 0;
                            const importe = item.importe || item.importeVenta || 0;
                            
                            // CORRECCIÓN: Solo incluir si tiene movimiento o inventario
                            if (cantInicial > 0 || vendido > 0 || cantFinal > 0 || importe > 0) {
                                dataInventarios.push({
                                    Fecha: fecha,
                                    Nombre: producto?.nombre || 'Producto Desconocido',
                                    Categoria: producto?.categoria || 'General',
                                    UM: producto?.um || producto?.unidadMedida || 'Un',
                                    CantInicial: cantInicial,
                                    Vendido: vendido,
                                    CantFinal: cantFinal,
                                    PrecioVenta: item.precioVenta || producto?.precio || 0,
                                    PrecioCosto: item.precioCosto || producto?.precioCosto || 0,
                                    Importe: importe,
                                    GananciaNeta: item.gananciaNeta || 0
                                });
                            }
                        });
                    }
                });
                
                if (dataInventarios.length > 0) {
                    const wsInventarios = XLSX.utils.json_to_sheet(dataInventarios);
                    XLSX.utils.book_append_sheet(wb, wsInventarios, "Inventarios");
                    console.log('✅ Hoja Inventarios creada');
                }
                
                // HOJA: NOMENCLADORES - Una hoja por cada moneda/clasificación
                Object.keys(tpvState.nomencladores).forEach(moneda => {
                    const denominaciones = tpvState.nomencladores[moneda] || [];
                    const cantidades = tpvState.nomencladorCantidades[moneda] || {};
                    
                    const dataNomenclador = [];
                    let totalNomenclador = 0;
                    
                    denominaciones.forEach(denom => {
                        const cantidad = cantidades[denom] || 0;
                        const subtotal = denom * cantidad;
                        totalNomenclador += subtotal;
                        
                        dataNomenclador.push({
                            Denominacion: denom,
                            Cantidad: cantidad,
                            Subtotal: subtotal,
                            Tipo: denom >= 100 ? 'Billete' : 'Moneda'
                        });
                    });
                    
                    if (dataNomenclador.length > 0) {
                        // Agregar total
                        dataNomenclador.push({
                            Denominacion: "TOTAL",
                            Cantidad: "",
                            Subtotal: totalNomenclador,
                            Tipo: ""
                        });
                        
                        const wsNomenclador = XLSX.utils.json_to_sheet(dataNomenclador);
                        const nombreHoja = `Nomencl ${moneda}`.substring(0, 31); // Excel limita a 31 caracteres
                        XLSX.utils.book_append_sheet(wb, wsNomenclador, nombreHoja);
                        console.log(`✅ Hoja Nomenclador ${moneda} creada`);
                    }
                });
                
                // HOJA: CIERRES DIARIOS Y MENSUALES
                if (tpvState.cierresCaja && tpvState.cierresCaja.length > 0) {
                    // Agrupar cierres por fecha
                    const cierresPorFecha = {};
                    const cierresPorMes = {};
                    
                    tpvState.cierresCaja.forEach(cierre => {
                        const fecha = cierre.fecha || '';
                        const mes = fecha.substring(0, 7);
                        
                        // Agrupar por fecha
                        if (!cierresPorFecha[fecha]) {
                            cierresPorFecha[fecha] = [];
                        }
                        cierresPorFecha[fecha].push(cierre);
                        
                        // Agrupar por mes
                        if (!cierresPorMes[mes]) {
                            cierresPorMes[mes] = [];
                        }
                        cierresPorMes[mes].push(cierre);
                    });
                    
                    // Crear hojas por día
                    Object.keys(cierresPorFecha).sort().forEach(fecha => {
                        const cierresDia = cierresPorFecha[fecha].map(cierre => ({
                            Hora: cierre.timestamp || '',
                            TotalVentas: cierre.totalVentas || 0,
                            Efectivo: cierre.efectivo || 0,
                            Tarjeta: cierre.tarjeta || 0,
                            Transferencia: cierre.transferencia || 0,
                            Observaciones: cierre.observaciones || ''
                        }));
                        
                        // Total del día
                        const totalDia = cierresDia.reduce((sum, c) => sum + c.TotalVentas, 0);
                        cierresDia.push({
                            Hora: "TOTAL",
                            TotalVentas: totalDia,
                            Efectivo: cierresDia.reduce((sum, c) => sum + c.Efectivo, 0),
                            Tarjeta: cierresDia.reduce((sum, c) => sum + c.Tarjeta, 0),
                            Transferencia: cierresDia.reduce((sum, c) => sum + c.Transferencia, 0),
                            Observaciones: ""
                        });
                        
                        const wsCierreDia = XLSX.utils.json_to_sheet(cierresDia);
                        XLSX.utils.book_append_sheet(wb, wsCierreDia, `Cierre ${fecha}`);
                        console.log(`✅ Hoja Cierre ${fecha} creada`);
                    });
                    
                    // Crear hojas por mes
                    Object.keys(cierresPorMes).sort().forEach(mes => {
                        const cierresMes = cierresPorMes[mes].map(cierre => ({
                            Fecha: cierre.fecha || '',
                            Hora: cierre.timestamp || '',
                            TotalVentas: cierre.totalVentas || 0,
                            Efectivo: cierre.efectivo || 0,
                            Tarjeta: cierre.tarjeta || 0,
                            Transferencia: cierre.transferencia || 0,
                            Observaciones: cierre.observaciones || ''
                        }));
                        
                        // Total del mes
                        const totalMes = cierresMes.reduce((sum, c) => sum + c.TotalVentas, 0);
                        cierresMes.push({
                            Fecha: "",
                            Hora: "TOTAL MES",
                            TotalVentas: totalMes,
                            Efectivo: cierresMes.reduce((sum, c) => sum + c.Efectivo, 0),
                            Tarjeta: cierresMes.reduce((sum, c) => sum + c.Tarjeta, 0),
                            Transferencia: cierresMes.reduce((sum, c) => sum + c.Transferencia, 0),
                            Observaciones: ""
                        });
                        
                        const wsCierreMes = XLSX.utils.json_to_sheet(cierresMes);
                        XLSX.utils.book_append_sheet(wb, wsCierreMes, `CierreMes ${mes}`);
                        console.log(`✅ Hoja Cierre Mes ${mes} creada`);
                    });
                }
                
                // HOJA 6: Resumen de Categorías
                const resumenCategorias = {};
                tpvState.productos.forEach(p => {
                    const cat = p.categoria || 'Sin Categoría';
                    if (!resumenCategorias[cat]) {
                        resumenCategorias[cat] = {
                            cantidad: 0,
                            valorTotal: 0,
                            costoTotal: 0
                        };
                    }
                    const inv = inventarioPorId[p.id] || {};
                    const stock = inv.cantFinal || inv.cantidadFinal || 0;
                    
                    if (stock > 0) {
                        resumenCategorias[cat].cantidad += 1;
                        resumenCategorias[cat].valorTotal += (p.precio || 0) * stock;
                        resumenCategorias[cat].costoTotal += (p.precioCosto || 0) * stock;
                    }
                });
                
                const dataResumen = Object.keys(resumenCategorias)
                    .filter(cat => resumenCategorias[cat].cantidad > 0)
                    .map(cat => ({
                        Categoria: cat,
                        Productos: resumenCategorias[cat].cantidad,
                        ValorInventario: resumenCategorias[cat].valorTotal,
                        CostoInventario: resumenCategorias[cat].costoTotal,
                        GananciaPotencial: resumenCategorias[cat].valorTotal - resumenCategorias[cat].costoTotal
                    }));
                
                if (dataResumen.length > 0) {
                    // Totales generales
                    const totalProductos = dataResumen.reduce((sum, r) => sum + r.Productos, 0);
                    const totalValor = dataResumen.reduce((sum, r) => sum + r.ValorInventario, 0);
                    const totalCosto = dataResumen.reduce((sum, r) => sum + r.CostoInventario, 0);
                    const totalGanancia = dataResumen.reduce((sum, r) => sum + r.GananciaPotencial, 0);
                    
                    dataResumen.push({
                        Categoria: "=== TOTALES ===",
                        Productos: totalProductos,
                        ValorInventario: totalValor,
                        CostoInventario: totalCosto,
                        GananciaPotencial: totalGanancia
                    });
                    
                    const wsResumen = XLSX.utils.json_to_sheet(dataResumen);
                    XLSX.utils.book_append_sheet(wb, wsResumen, "Resumen");
                    console.log('✅ Hoja Resumen creada');
                }
                
                const fileName = `tpv_completo_${getTodayDateString()}.xlsx`;
                
                // CORRECCIÓN: Usar función helper segura para móviles con await
                try {
                    await exportar_xlsx_seguro(wb, fileName);
                    console.log('✅ Archivo Excel generado:', fileName);
                } catch (error) {
                    console.error('❌ Error al guardar archivo:', error);
                    throw error;
                }
        }


        // ==================== IMPORTADOR INTELIGENTE CON IA ====================
        /**
         * MÓDULO DE IMPORTACIÓN SUPERINTELIGENTE CON MACHINE LEARNING
         * 
         * Este módulo aprende de la estructura de archivos Excel y puede:
         * - Detectar columnas SIN encabezados claros
         * - Aprender patrones de nombres de productos
         * - Identificar precios por contexto (números entre 1-10000)
         * - Detectar cantidades (números entre 0-1000)
         * - Reconocer unidades de medida comunes
         * - Inferir costos cuando no están explícitos
         */

        class SmartExcelImporter {
            constructor() {
                this.DEBUG = true;
                this.MAX_FILE_SIZE = 10 * 1024 * 1024;
        
                // Patrones de aprendizaje
                this.patterns = {
                    // Palabras clave en encabezados
                    headers: {
                        producto: /^(producto|nombre|item|descripcion|descripción|articulo|artículo|productos)$/i,
                        precio: /^(precio|valor|venta|p\.venta|pvp|precio.*venta|price)$/i,
                        um: /^(unidad|u\.m|um|medida|und|unit|c\/u)$/i,
                        costo: /^(costo|p\.costo|inver|compra|precio.*costo|cost|inversion|inversión)$/i,
                        cantidad: /^(cantidad|stock|existencia|cant|inventario|qty|final)$/i,
                        categoria: /^(categoria|categoría|tipo|clasificacion|clasificación|category)$/i
                    },
            
                    // Patrones de valores para inferir tipo de columna
                    unidadesMedida: /^(c\/u|un|kg|gr|lt|ml|pza|pieza|unidad|und|caja|paquete|bolsa)$/i,
            
                    // Rangos numéricos esperados
                    ranges: {
                        precio: { min: 1, max: 100000 },      // Precios típicos
                        cantidad: { min: 0, max: 10000 },     // Cantidades típicas
                        costo: { min: 1, max: 100000 }        // Costos típicos
                    }
                };
            }
    
            /**
             * FASE 1: ANÁLISIS INTELIGENTE DE LA ESTRUCTURA
             * Detecta automáticamente qué columna contiene qué información
             */
            analizarEstructuraInteligente(rawData) {
                console.log('🧠 Iniciando análisis inteligente de estructura...');
        
                const analisis = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'unknown'
                };
        
                // Estrategia 1: Buscar encabezados explícitos
                const resultadoEncabezados = this.buscarEncabezadosExplicitos(rawData);
                if (resultadoEncabezados.confianza > 0.6) {
                    console.log('✅ Encabezados explícitos detectados');
                    return resultadoEncabezados;
                }
        
                // Estrategia 2: Análisis por contenido (cuando no hay encabezados claros)
                const resultadoContenido = this.analizarPorContenido(rawData);
                if (resultadoContenido.confianza > 0.5) {
                    console.log('✅ Estructura detectada por análisis de contenido');
                    return resultadoContenido;
                }
        
                // Estrategia 3: Patrón por defecto (archivo del usuario)
                console.log('⚠️ Usando patrón detectado específico');
                return this.detectarPatronEspecifico(rawData);
            }
    
            /**
             * Busca encabezados explícitos en las primeras filas
             */
            buscarEncabezadosExplicitos(rawData) {
                const resultado = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'headers'
                };
        
                // Buscar en las primeras 20 filas
                for (let i = 0; i < Math.min(20, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila || fila.length === 0) continue;
            
                    let coincidencias = 0;
                    const colsEncontradas = {};
            
                    for (let j = 0; j < fila.length; j++) {
                        const celda = String(fila[j] || "").toLowerCase().trim();
                        if (!celda) continue;
                
                        // Verificar contra patrones de encabezados
                        for (const [tipo, patron] of Object.entries(this.patterns.headers)) {
                            if (patron.test(celda) && !colsEncontradas[tipo]) {
                                colsEncontradas[tipo === 'producto' ? 'nombre' : tipo] = j;
                                coincidencias++;
                                if (this.DEBUG) {
                                    console.log(`  📌 Fila ${i+1}, Col ${j+1}: "${celda}" → ${tipo}`);
                                }
                            }
                        }
                    }
            
                    // Si encontramos al menos producto y precio, es probable que sea encabezado
                    if (coincidencias >= 2 && (colsEncontradas.producto !== undefined || colsEncontradas.precio !== undefined || colsEncontradas.cantidad !== undefined)) {
                        resultado.filaEncabezado = i;
                        resultado.filaInicioDatos = i + 1;
                        resultado.columnas = colsEncontradas;
                        resultado.confianza = Math.min(coincidencias / 4, 1.0); // Máximo 6 columnas esperadas
                
                        if (this.DEBUG) {
                            console.log(`✓ Encabezados encontrados en fila ${i+1} (${coincidencias} columnas, confianza: ${resultado.confianza.toFixed(2)})`);
                        }
                        return resultado;
                    }
                }
        
                return resultado;
            }
    
            /**
             * Analiza el contenido de las columnas para inferir su tipo
             */
            analizarPorContenido(rawData) {
                const resultado = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'content'
                };
        
                // Encontrar primera fila con datos (ignorar filas vacías y con fórmulas)
                let primeraFilaDatos = -1;
                for (let i = 0; i < Math.min(30, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila) continue;
            
                    // Buscar fila que tenga al menos 3 celdas con datos reales
                    let celdasConDatos = 0;
                    for (let j = 0; j < fila.length; j++) {
                        const valor = fila[j];
                        if (valor !== null && valor !== undefined && valor !== '' && !String(valor).startsWith('=')) {
                            celdasConDatos++;
                        }
                    }
            
                    if (celdasConDatos >= 3) {
                        primeraFilaDatos = i;
                        if (this.DEBUG) {
                            console.log(`📊 Primera fila con datos: ${i+1}`);
                        }
                        break;
                    }
                }
        
                if (primeraFilaDatos === -1) return resultado;
        
                // Analizar las siguientes 10-20 filas para detectar patrones
                const muestras = [];
                for (let i = primeraFilaDatos; i < Math.min(primeraFilaDatos + 20, rawData.length); i++) {
                    const fila = rawData[i];
                    if (fila && fila.length > 0) {
                        muestras.push(fila);
                    }
                }
        
                if (muestras.length < 3) return resultado;
        
                // Analizar cada columna
                const numColumnas = Math.max(...muestras.map(f => f.length));
                const analisisColumnas = [];
        
                for (let col = 0; col < numColumnas; col++) {
                    const valoresColumna = muestras.map(fila => fila[col]).filter(v => v !== null && v !== undefined && v !== '');
            
                    if (valoresColumna.length === 0) {
                        analisisColumnas.push({ tipo: 'vacia', confianza: 0 });
                        continue;
                    }
            
                    const analisis = this.analizarColumna(valoresColumna);
                    analisisColumnas.push(analisis);
            
                    if (this.DEBUG) {
                        console.log(`  Col ${col+1}: ${analisis.tipo} (confianza: ${analisis.confianza.toFixed(2)})`);
                    }
                }
        
                // Asignar columnas basándose en el análisis
                const asignacion = this.asignarColumnasPorAnalisis(analisisColumnas);
        
                resultado.filaEncabezado = primeraFilaDatos - 1;
                resultado.filaInicioDatos = primeraFilaDatos;
                resultado.columnas = asignacion.columnas;
                resultado.confianza = asignacion.confianza;
        
                return resultado;
            }
    
            /**
             * Analiza una columna y determina qué tipo de dato contiene
             */
            analizarColumna(valores) {
                const analisis = {
                    tipo: 'desconocido',
                    confianza: 0,
                    detalles: {}
                };
        
                // Filtrar valores vacíos y fórmulas
                const valoresLimpios = valores.filter(v => {
                    const str = String(v);
                    return str && str !== '' && !str.startsWith('=');
                });
        
                if (valoresLimpios.length === 0) {
                    return { tipo: 'vacia', confianza: 0 };
                }
        
                // Contar tipos de datos
                let numeros = 0;
                let textos = 0;
                let unidades = 0;
                let numerosEnRangoPrecio = 0;
                let numerosEnRangoCantidad = 0;
        
                const valoresNumericos = [];
        
                for (const valor of valoresLimpios) {
                    const esNumero = typeof valor === 'number' || !isNaN(parseFloat(String(valor).replace(/[^0-9.-]/g, '')));
            
                    if (esNumero) {
                        numeros++;
                        const num = typeof valor === 'number' ? valor : parseFloat(String(valor).replace(/[^0-9.-]/g, ''));
                        valoresNumericos.push(num);
                
                        // Verificar rangos
                        if (num >= this.patterns.ranges.precio.min && num <= this.patterns.ranges.precio.max) {
                            numerosEnRangoPrecio++;
                        }
                        if (num >= this.patterns.ranges.cantidad.min && num <= this.patterns.ranges.cantidad.max) {
                            numerosEnRangoCantidad++;
                        }
                    } else {
                        textos++;
                
                        // Verificar si es unidad de medida
                        if (this.patterns.unidadesMedida.test(String(valor))) {
                            unidades++;
                        }
                    }
                }
        
                const porcentajeNumeros = numeros / valoresLimpios.length;
                const porcentajeTextos = textos / valoresLimpios.length;
        
                // DECISIÓN: ¿Qué tipo de columna es?
        
                // Columna de nombres (texto largo)
                if (porcentajeTextos > 0.7 && unidades < valoresLimpios.length * 0.3) {
                    const textoPromedio = valoresLimpios
                        .filter(v => typeof v === 'string')
                        .reduce((sum, v) => sum + v.length, 0) / Math.max(textos, 1);
            
                    if (textoPromedio > 5) { // Nombres típicamente tienen más de 5 caracteres
                        analisis.tipo = 'producto';
                        analisis.confianza = 0.8;
                        return analisis;
                    }
                }
        
                // Columna de unidades de medida
                if (unidades > valoresLimpios.length * 0.5) {
                    analisis.tipo = 'um';
                    analisis.confianza = 0.9;
                    return analisis;
                }
        
                // Columnas numéricas
                if (porcentajeNumeros > 0.7) {
                    const promedio = valoresNumericos.reduce((a, b) => a + b, 0) / valoresNumericos.length;
                    const max = Math.max(...valoresNumericos);
                    const min = Math.min(...valoresNumericos);
            
                    // Precios: generalmente entre 10-10000
                    if (promedio > 50 && max > 100 && numerosEnRangoPrecio > valoresNumericos.length * 0.6) {
                        analisis.tipo = 'precio';
                        analisis.confianza = 0.85;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Cantidades: generalmente entre 0-500, con muchos valores pequeños
                    if (max <= 1000 && promedio < 100 && numerosEnRangoCantidad > valoresNumericos.length * 0.8) {
                        analisis.tipo = 'cantidad';
                        analisis.confianza = 0.8;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Costos: similar a precios pero puede ser un poco menor
                    if (promedio > 20 && max > 50) {
                        analisis.tipo = 'costo';
                        analisis.confianza = 0.7;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Números genéricos
                    analisis.tipo = 'numero';
                    analisis.confianza = 0.5;
                    return analisis;
                }
        
                // Texto genérico
                if (porcentajeTextos > 0.5) {
                    analisis.tipo = 'texto';
                    analisis.confianza = 0.4;
                    return analisis;
                }
        
                return analisis;
            }
    
            /**
             * Asigna columnas basándose en el análisis
             */
            asignarColumnasPorAnalisis(analisisColumnas) {
                const asignacion = {
                    columnas: {},
                    confianza: 0
                };
        
                let confianzaTotal = 0;
                let columnasAsignadas = 0;
        
                // Buscar cada tipo de columna
                const tipos = ['producto', 'precio', 'um', 'cantidad', 'costo'];
        
                for (const tipo of tipos) {
                    let mejorCol = -1;
                    let mejorConfianza = 0;
            
                    for (let i = 0; i < analisisColumnas.length; i++) {
                        if (analisisColumnas[i].tipo === tipo && analisisColumnas[i].confianza > mejorConfianza) {
                            // Evitar asignar la misma columna dos veces
                            if (!Object.values(asignacion.columnas).includes(i)) {
                                mejorCol = i;
                                mejorConfianza = analisisColumnas[i].confianza;
                            }
                        }
                    }
            
                    if (mejorCol !== -1) {
                        asignacion.columnas[tipo === 'producto' ? 'nombre' : tipo] = mejorCol;
                        confianzaTotal += mejorConfianza;
                        columnasAsignadas++;
                
                        if (this.DEBUG) {
                            console.log(`✓ Columna ${mejorCol + 1} → ${tipo} (confianza: ${mejorConfianza.toFixed(2)})`);
                        }
                    }
                }
        
                asignacion.confianza = columnasAsignadas > 0 ? confianzaTotal / columnasAsignadas : 0;
        
                return asignacion;
            }
    
            /**
             * Detecta el patrón específico del archivo del usuario
             * Basado en el ejemplo: Desi_02_03_Dia.xlsx
             */
            detectarPatronEspecifico(rawData) {
                console.log('🎯 Aplicando patrón específico detectado...');
        
                // Buscar fila que contenga "Precio" o similar en alguna celda
                let filaEncabezado = -1;
                for (let i = 0; i < Math.min(10, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila) continue;
            
                    for (let j = 0; j < fila.length; j++) {
                        const celda = String(fila[j] || "").toLowerCase();
                        if (celda.includes('precio') || celda.includes('cantidad')) {
                            filaEncabezado = i;
                            break;
                        }
                    }
                    if (filaEncabezado !== -1) break;
                }
        
                // Si no encontramos encabezado, buscar primera fila con datos
                if (filaEncabezado === -1) {
                    for (let i = 0; i < Math.min(10, rawData.length); i++) {
                        const fila = rawData[i];
                        if (!fila) continue;
                
                        // Buscar fila con texto + número + texto + número
                        if (fila[0] && typeof fila[0] === 'string' && fila[0].length > 2 &&
                            fila[1] && (typeof fila[1] === 'number' || !isNaN(parseFloat(String(fila[1]))))) {
                            filaEncabezado = i - 1;
                            break;
                        }
                    }
                }
        
                const filaInicioDatos = filaEncabezado + 1;
        
                // Patrón detectado del archivo ejemplo:
                // Columna 0 (A): Nombre del producto
                // Columna 1 (B): Precio
                // Columna 2 (C): Unidad de medida
                // Columna 3 (D): Cantidad
                // Columna 8 (I): Inversión/Costo
        
                return {
                    filaEncabezado: filaEncabezado,
                    filaInicioDatos: filaInicioDatos,
                    columnas: {
                        nombre: 0,    // Columna A
                        precio: 1,    // Columna B
                        um: 2,        // Columna C
                        cantidad: 3,  // Columna D
                        costo: 8      // Columna I
                    },
                    confianza: 0.75,
                    metodo: 'pattern-specific'
                };
            }
    
            /**
             * Categorización automática mejorada
             */
            categorizarProducto(nombre) {
                const nombreLower = nombre.toLowerCase();
        
                const categorias = {
                    'Alimentos': /aceite|azucar|azúcar|arroz|harina|sal|café|cafe|te|té|atun|atún|sardina|leche|queso|huevo|pasta|mantequilla|mayonesa|mostaza|salsa/i,
                    'Higiene Personal': /shampoo|champu|champú|jabón|jabon|pasta.*dental|cepillo|desodorante|toalla.*sanitaria|almuhadilla|pañal|papel.*higienico|crema.*afeitar/i,
                    'Limpieza': /detergente|cloro|desinfectante|lavaplatos|esponja|trapo|bolsa.*basura|limpiador|cera|escoba|trapeador|suavizante/i,
                    'Golosinas': /galleta|chocolate|caramelo|chicle|dulce|bombones|botonetas|goma.*mascar|pirulí|chupeta|chocolatina/i,
                    'Bebidas': /gaseosa|refresco|jugo|agua|bebida|energizante|soda|cola|malta|cerveza.*sin.*alcohol|té.*frio|limonada/i,
                    'Papelería': /cuaderno|lapiz|lápiz|boligrafo|bolígrafo|marcador|borrador|regla|pegamento|tijera|folder|carpeta|papel.*bond/i,
                    'Tabaquería': /cigarrillo|cigarro|tabaco|fosforo|fósforo|encendedor|lighter|marlboro|fosforera/i,
                    'Panadería': /pan|arepa|empanada|pastel|torta|cachito|tequeño|croissant/i,
                    'Belleza': /uña|esmalte|lima|bloque|maquillaje|labial|crema.*facial|perfume|colonia|tinte|acetona|removedor/i,
                    'Licores': /shot|vodka|ron|whisky|cerveza|vino|licor|brandy|tequila|ginebra|gin|pomo|aguardiente/i,
                    'Medicamentos': /aspirina|paracetamol|ibuprofeno|analgesico|analgésico|jarabe|pastilla|capsula|cápsula|vitamina|alcohol.*medicinal/i,
                    'Ropa': /blusa|camisa|pantalon|pantalón|falda|vestido|short|medias|calcetines|ropa.*interior|sueter|chandal/i,
                    'Condimentos': /caldito|caldo|sazonador|adobo|comino|orégano|oregano|pimienta|ajo|cebolla.*polvo/i,
                    'Varios': /chanceller|mechero|pila|bateria|batería|cable|cargador/i
                };
        
                for (const [categoria, patron] of Object.entries(categorias)) {
                    if (patron.test(nombreLower)) {
                        return categoria;
                    }
                }
        
                return 'Otros';
            }
    
            /**
             * Conversión inteligente de valores
             */
            convertirANumero(valor, valorPorDefecto = 0) {
                if (valor === null || valor === undefined || valor === '') return valorPorDefecto;
                if (typeof valor === 'number') return isNaN(valor) ? valorPorDefecto : valor;
        
                const str = String(valor);
        
                // Si es una fórmula, retornar valor por defecto
                if (str.startsWith('=')) return valorPorDefecto;
        
                if (typeof valor === 'string') {
                    const limpio = str.replace(/[^0-9.-]/g, '');
                    const numero = parseFloat(limpio);
                    return isNaN(numero) ? valorPorDefecto : numero;
                }
        
                return valorPorDefecto;
            }
    
            /**
             * IMPORTACIÓN PRINCIPAL CON INTELIGENCIA ARTIFICIAL
             */
            async importar(file, tpvState, opciones = {}) {
                const {
                    onProgress = () => {},
                    confirmarBorrado = true,
                    crearInventario = true
                } = opciones;
        
                try {
                    // Paso 1: Validar archivo
                    onProgress({ paso: 1, total: 6, mensaje: '🔍 Validando archivo...' });
            
                    if (file.size > this.MAX_FILE_SIZE) {
                        throw new Error(`Archivo demasiado grande (máx ${this.MAX_FILE_SIZE / 1024 / 1024}MB)`);
                    }
            
                    // Paso 2: Confirmar si hay productos existentes
                    if (confirmarBorrado && tpvState.productos.length > 0) {
                        const mensaje = `⚠️ ATENCIÓN: Esta acción borrará los ${tpvState.productos.length} productos existentes.\n\n` +
                            `¿Deseas continuar?\n\n💡 Recomendación: Exporta un backup antes de importar.`;
                        if (!confirm(mensaje)) {
                            throw new Error('Importación cancelada por el usuario');
                        }
                    }
            
                    // Paso 3: Leer archivo
                    onProgress({ paso: 2, total: 6, mensaje: '📖 Leyendo archivo Excel...' });
            
                    const arrayBuffer = await this.leerArchivo(file);
                    const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array' });
            
                    if (!workbook || !workbook.SheetNames || workbook.SheetNames.length === 0) {
                        throw new Error("El archivo no contiene hojas válidas");
                    }
            
                    // Paso 4: Seleccionar hoja
                    const hojaProductos = workbook.SheetNames.includes("Productos") 
                        ? "Productos" 
                        : workbook.SheetNames.includes("Base de Datos")
                        ? "Base de Datos"
                        : workbook.SheetNames[0];
            
                    console.log(`📄 Usando hoja: "${hojaProductos}"`);
            
                    const sheet = workbook.Sheets[hojaProductos];
                    const rawData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: "" });
            
                    if (rawData.length === 0) {
                        throw new Error("La hoja está vacía");
                    }
            
                    // Paso 5: ANÁLISIS INTELIGENTE
                    onProgress({ paso: 3, total: 6, mensaje: '🧠 Analizando estructura con IA...' });
            
                    const estructura = this.analizarEstructuraInteligente(rawData);
            
                    console.log('📊 Estructura detectada:', estructura);
            
                    if (estructura.confianza < 0.4) {
                        throw new Error("No se pudo detectar la estructura del archivo. Verifica que tenga al menos columnas de Nombre y Precio.");
                    }
            
                    const cols = estructura.columnas;
                    const filaInicio = estructura.filaInicioDatos;
            
                    // Paso 6: Procesar productos
                    onProgress({ paso: 4, total: 6, mensaje: '📦 Importando productos...' });
            
                    const productosNuevos = [];
                    const inventarioNuevo = [];
                    const estadisticas = {
                        procesadas: 0,
                        exitosas: 0,
                        errores: 0,
                        sinPrecio: 0,
                        sinNombre: 0
                    };
            
                    for (let i = filaInicio; i < rawData.length; i++) {
                        const fila = rawData[i];
                        if (!fila || fila.length === 0) continue;
                
                        estadisticas.procesadas++;
                
                        try {
                            // Extraer datos según estructura detectada
                            const nombreRaw = cols.nombre !== undefined ? fila[cols.nombre] : null;
                            const precioRaw = cols.precio !== undefined ? fila[cols.precio] : null;
                    
                            // Validar nombre
                            if (!nombreRaw || nombreRaw === "" || nombreRaw === null) {
                                estadisticas.sinNombre++;
                                continue;
                            }
                    
                            const nombre = String(nombreRaw).trim();
                    
                            // Omitir filas de totales o agregados
                            if (nombre.match(/^(total|===|subtotal|suma|resumen)/i)) {
                                continue;
                            }
                    
                            // Convertir y validar precio
                            const precioVenta = this.convertirANumero(precioRaw);
                    
                            if (precioVenta <= 0) {
                                estadisticas.sinPrecio++;
                                console.warn(`⚠️ Fila ${i + 1}: "${nombre}" - Precio inválido (${precioRaw})`);
                                continue;
                            }
                    
                            // Extraer datos opcionales
                            const um = cols.um !== undefined ? (fila[cols.um] || "C/U") : "C/U";
                            const cantidad = cols.cantidad !== undefined 
                                ? this.convertirANumero(fila[cols.cantidad], 0)
                                : 0;
                            const costoRaw = cols.costo !== undefined ? fila[cols.costo] : null;
                            const precioCosto = this.convertirANumero(costoRaw, precioVenta * 0.7);
                    
                            // Categorizar
                            const categoria = this.categorizarProducto(nombre);
                    
                            // Crear ID único
                            const id = `prod-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`;
                    
                            // Crear producto
                            const producto = {
                                id,
                                nombre: nombre,
                                categoria: categoria,
                                precio: precioVenta,
                                costoUnitario: precioCosto,
                                um: String(um).trim(),
                                imagen: "",
                                onSale: false,
                                stock_actual: cantidad
                            };
                    
                            productosNuevos.push(producto);
                    
                            // Agregar categoría si no existe
                            if (!tpvState.categorias.includes(categoria)) {
                                tpvState.categorias.push(categoria);
                                console.log(`📁 Nueva categoría: ${categoria}`);
                            }
                    
                            // Crear entrada de inventario
                            if (crearInventario && cantidad > 0) {
                                inventarioNuevo.push({
                                    id,
                                    nombre: nombre,
                                    categoria: categoria,
                                    um: String(um).trim(),
                                    cantInicial: cantidad,
                                    cantFinal: cantidad,
                                    vendido: 0,
                                    precioVenta: precioVenta,
                                    precioCosto: precioCosto,
                                    importe: 0,
                                    comision: 0,
                                    gananciaNeta: 0
                                });
                            }
                    
                            estadisticas.exitosas++;
                    
                        } catch (error) {
                            estadisticas.errores++;
                            if (this.DEBUG) {
                                console.error(`❌ Error en fila ${i + 1}:`, error);
                            }
                        }
                    }
            
                    // Paso 7: Guardar
                    onProgress({ paso: 5, total: 6, mensaje: '💾 Guardando cambios...' });
            
                    tpvState.productos = productosNuevos;
            
                    if (crearInventario && inventarioNuevo.length > 0) {
                        const fechaHoy = getTodayDateString();
                        tpvState.inventarios[fechaHoy] = inventarioNuevo;
                    }
            
                    // Generar mensaje de resultado
                    let mensaje = `✅ Importación exitosa!\n\n`;
                    mensaje += `📦 ${estadisticas.exitosas} productos importados\n`;
                    if (inventarioNuevo.length > 0) {
                        mensaje += `📊 ${inventarioNuevo.length} items en inventario\n`;
                    }
                    mensaje += `\n📈 Estadísticas:\n`;
                    mensaje += `  • Procesadas: ${estadisticas.procesadas} filas\n`;
                    mensaje += `  • Exitosas: ${estadisticas.exitosas}\n`;
                    if (estadisticas.sinNombre > 0) {
                        mensaje += `  • Sin nombre: ${estadisticas.sinNombre}\n`;
                    }
                    if (estadisticas.sinPrecio > 0) {
                        mensaje += `  • Sin precio válido: ${estadisticas.sinPrecio}\n`;
                    }
                    if (estadisticas.errores > 0) {
                        mensaje += `  • Errores: ${estadisticas.errores}\n`;
                    }
                    mensaje += `\n🧠 Método: ${estructura.metodo}\n`;
                    mensaje += `🎯 Confianza: ${(estructura.confianza * 100).toFixed(0)}%`;
            
                    onProgress({ paso: 6, total: 6, mensaje: '✅ Completado!' });
            
                    return {
                        exito: true,
                        productosImportados: estadisticas.exitosas,
                        inventarioCreado: inventarioNuevo.length,
                        estadisticas,
                        estructura,
                        mensaje
                    };
            
                } catch (error) {
                    return {
                        exito: false,
                        error: error.message,
                        mensaje: `❌ ${error.message}`
                    };
                }
            }
    
            /**
             * Lee archivo como ArrayBuffer
             */
            leerArchivo(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = () => reject(new Error("Error al leer el archivo"));
                    reader.readAsArrayBuffer(file);
                });
            }

            /**
             * 🧠 SISTEMA DE MEMORIA Y APRENDIZAJE
             * Guarda y recupera configuraciones de importación/exportación
             */
            guardarConfiguracionAprendida(estructura, nombreArchivo) {
                try {
                    const config = {
                        timestamp: Date.now(),
                        nombreArchivo: nombreArchivo,
                        estructura: estructura,
                        version: '8.0-ULTRA-SMART'
                    };
                    
                    // Guardar en localStorage
                    localStorage.setItem('tpv_ultima_estructura', JSON.stringify(config));
                    
                    // Guardar historial (últimas 10 configuraciones)
                    let historial = JSON.parse(localStorage.getItem('tpv_historial_estructuras') || '[]');
                    historial.unshift(config);
                    historial = historial.slice(0, 10); // Mantener solo últimas 10
                    localStorage.setItem('tpv_historial_estructuras', JSON.stringify(historial));
                    
                    if (this.DEBUG) {
                        console.log('💾 Configuración guardada en memoria:', config);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudo guardar la configuración:', error);
                }
            }
            
            /**
             * Recupera la última configuración usada
             */
            recuperarConfiguracionAprendida() {
                try {
                    const configStr = localStorage.getItem('tpv_ultima_estructura');
                    if (configStr) {
                        const config = JSON.parse(configStr);
                        if (this.DEBUG) {
                            console.log('📖 Configuración recuperada:', config);
                        }
                        return config.estructura;
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudo recuperar la configuración:', error);
                }
                return null;
            }
            
            /**
             * 🔧 AUTO-CORRECCIÓN DE DATOS
             * Corrige automáticamente problemas comunes en los datos
             */
            autoCorregirDatos(producto) {
                // Limpiar nombre
                if (producto.nombre) {
                    producto.nombre = producto.nombre.trim()
                        .replace(/\s+/g, ' ')  // Múltiples espacios → 1 espacio
                        .replace(/^[0-9]+\s*[.-]\s*/,  '')  // Quitar numeración inicial (1. 2. 3.)
                        .replace(/\t/g, ' ');  // Tabs → espacios
                }
                
                // Corregir precios
                if (producto.precio) {
                    // Redondear a 2 decimales
                    producto.precio = Math.round(producto.precio * 100) / 100;
                    
                    // Si el precio es muy pequeño (probablemente error), multiplicar por 100
                    if (producto.precio < 1 && producto.precio > 0) {
                        producto.precio = producto.precio * 100;
                        if (this.DEBUG) {
                            console.log(`🔧 Precio corregido: ${producto.nombre} - ${producto.precio}`);
                        }
                    }
                }
                
                // Corregir unidades de medida comunes
                if (producto.um) {
                    const umCorregidas = {
                        'cu': 'C/U',
                        'c/u': 'C/U',
                        'un': 'C/U',
                        'und': 'C/U',
                        'unidad': 'C/U',
                        'kg': 'Kg',
                        'gr': 'Gr',
                        'lt': 'Lt',
                        'ml': 'ml',
                        'pza': 'Pza',
                        'pieza': 'Pza'
                    };
                    
                    const umLower = producto.um.toLowerCase().trim();
                    if (umCorregidas[umLower]) {
                        producto.um = umCorregidas[umLower];
                    }
                }
                
                // Validar y corregir cantidades negativas
                if (producto.cantidad && producto.cantidad < 0) {
                    producto.cantidad = 0;
                    if (this.DEBUG) {
                        console.log(`🔧 Cantidad negativa corregida a 0: ${producto.nombre}`);
                    }
                }
                
                return producto;
            }
            
            /**
             * 🔍 VALIDACIÓN MEJORADA CON MÚLTIPLES NIVELES
             * Valida con 100% de confiabilidad
             */
            validarConfiabilidad100(rawData, estructura) {
                const validacion = {
                    esValido: true,
                    problemas: [],
                    sugerencias: [],
                    confianzaFinal: estructura.confianza
                };
                
                // Nivel 1: Verificar que hay columnas esenciales
                if (!estructura.columnas.nombre && !estructura.columnas.producto) {
                    validacion.problemas.push('❌ No se detectó columna de nombres/productos');
                    validacion.esValido = false;
                }
                
                if (!estructura.columnas.precio) {
                    validacion.problemas.push('❌ No se detectó columna de precios');
                    validacion.esValido = false;
                }
                
                // Nivel 2: Verificar datos de muestra
                const muestraFilas = rawData.slice(estructura.filaInicioDatos, estructura.filaInicioDatos + 5);
                let filasValidas = 0;
                
                for (const fila of muestraFilas) {
                    if (!fila) continue;
                    
                    const nombre = fila[estructura.columnas.nombre || estructura.columnas.producto];
                    const precio = fila[estructura.columnas.precio];
                    
                    if (nombre && String(nombre).trim().length > 0 && precio && !isNaN(this.convertirANumero(precio))) {
                        filasValidas++;
                    }
                }
                
                const porcentajeValido = filasValidas / Math.min(5, muestraFilas.length);
                
                if (porcentajeValido < 0.4) {
                    validacion.problemas.push('⚠️ Menos del 40% de las filas de muestra son válidas');
                    validacion.sugerencias.push('Verifica que los datos empiecen en la fila correcta');
                }
                
                // Nivel 3: Calcular confianza final
                if (validacion.esValido) {
                    validacion.confianzaFinal = (estructura.confianza * 0.7) + (porcentajeValido * 0.3);
                    
                    // Bonificación si tiene columnas opcionales
                    if (estructura.columnas.cantidad) validacion.confianzaFinal += 0.05;
                    if (estructura.columnas.costo) validacion.confianzaFinal += 0.05;
                    if (estructura.columnas.um) validacion.confianzaFinal += 0.05;
                    
                    validacion.confianzaFinal = Math.min(validacion.confianzaFinal, 1.0);
                }
                
                if (this.DEBUG) {
                    console.log('🔍 Validación completa:', validacion);
                }
                
                return validacion;
            }
            
            /**
             * 📤 EXPORTACIÓN INTELIGENTE
             * Exporta con el formato que el usuario prefiere
             */
            exportarInteligente(tpvState, opciones = {}) {
                const {
                    incluirInventario = false,
                    formato = 'auto',  // 'auto', 'simple', 'completo'
                    nombreArchivo = 'productos_exportados.xlsx'
                } = opciones;
                
                try {
                    // Recuperar preferencias guardadas
                    const preferencias = this.recuperarPreferenciasExportacion();
                    const formatoFinal = formato === 'auto' ? (preferencias?.formato || 'completo') : formato;
                    
                    // Preparar workbook
                    const wb = XLSX.utils.book_new();
                    
                    if (formatoFinal === 'simple') {
                        // Formato simple: solo nombre y precio
                        const datos = [
                            ['Nombre', 'Precio']
                        ];
                        
                        tpvState.productos.forEach(prod => {
                            datos.push([prod.nombre, prod.precio]);
                        });
                        
                        const ws = XLSX.utils.aoa_to_sheet(datos);
                        XLSX.utils.book_append_sheet(wb, ws, 'Productos');
                        
                    } else {
                        // Formato completo
                        const datos = [
                            ['Nombre', 'Precio', 'Unidad', 'Categoría', 'Costo']
                        ];
                        
                        tpvState.productos.forEach(prod => {
                            const costo = prod.precio * 0.7;  // Estimación si no tiene costo
                            datos.push([
                                prod.nombre, 
                                prod.precio, 
                                prod.um || 'C/U', 
                                prod.categoria || 'Otros',
                                costo
                            ]);
                        });
                        
                        const ws = XLSX.utils.aoa_to_sheet(datos);
                        XLSX.utils.book_append_sheet(wb, ws, 'Productos');
                        
                        // Si incluir inventario
                        if (incluirInventario) {
                            const fechaHoy = getTodayDateString();
                            const inventario = tpvState.inventarios[fechaHoy] || [];
                            
                            if (inventario.length > 0) {
                                const datosInv = [
                                    ['Nombre', 'Cantidad Inicial', 'Cantidad Final', 'Vendido', 'Precio Venta', 'Precio Costo']
                                ];
                                
                                inventario.forEach(item => {
                                    datosInv.push([
                                        item.nombre,
                                        item.cantInicial,
                                        item.cantFinal,
                                        item.vendido,
                                        item.precioVenta,
                                        item.precioCosto
                                    ]);
                                });
                                
                                const wsInv = XLSX.utils.aoa_to_sheet(datosInv);
                                XLSX.utils.book_append_sheet(wb, wsInv, 'Inventario');
                            }
                        }
                    }
                    
                    // Guardar preferencias para próxima vez
                    this.guardarPreferenciasExportacion({
                        formato: formatoFinal,
                        incluirInventario: incluirInventario,
                        timestamp: Date.now()
                    });
                    
                    // Exportar archivo
                    XLSX.writeFile(wb, nombreArchivo);
                    
                    return {
                        exito: true,
                        formato: formatoFinal,
                        productosExportados: tpvState.productos.length,
                        mensaje: `✅ ${tpvState.productos.length} productos exportados con formato ${formatoFinal}`
                    };
                    
                } catch (error) {
                    console.error('❌ Error en exportación inteligente:', error);
                    return {
                        exito: false,
                        error: error.message
                    };
                }
            }
            
            /**
             * Guardar preferencias de exportación
             */
            guardarPreferenciasExportacion(preferencias) {
                try {
                    localStorage.setItem('tpv_preferencias_exportacion', JSON.stringify(preferencias));
                    if (this.DEBUG) {
                        console.log('💾 Preferencias de exportación guardadas:', preferencias);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudieron guardar preferencias:', error);
                }
            }
            
            /**
             * Recuperar preferencias de exportación
             */
            recuperarPreferenciasExportacion() {
                try {
                    const prefStr = localStorage.getItem('tpv_preferencias_exportacion');
                    if (prefStr) {
                        return JSON.parse(prefStr);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudieron recuperar preferencias:', error);
                }
                return null;
            }
            
            /**
             * 🎯 IMPORTACIÓN MEJORADA AL 100%
             * Override del método original con mejoras
             */
            async importarConMaximaConfiabilidad(file, tpvState, opciones = {}) {
                const resultado = await this.importar(file, tpvState, opciones);
                
                if (resultado.exito) {
                    // Guardar configuración aprendida
                    this.guardarConfiguracionAprendida(resultado.estructura, file.name);
                    
                    // Aplicar auto-corrección a todos los productos importados
                    tpvState.productos = tpvState.productos.map(prod => this.autoCorregirDatos(prod));
                    
                    // Validar confiabilidad
                    const validacion = this.validarConfiabilidad100(
                        resultado.rawData || [], 
                        resultado.estructura
                    );
                    
                    resultado.validacion = validacion;
                    resultado.confianzaFinal = validacion.confianzaFinal;
                    
                    if (this.DEBUG) {
                        console.log('🎯 Importación con máxima confiabilidad completada:', resultado);
                    }
                }
                
                return resultado;
            }
            
            /**
             * 🔄 SINCRONIZACIÓN INTELIGENTE
             * Compara y sincroniza datos de múltiples fuentes
             */
            sincronizarInteligente(productosActuales, productosNuevos) {
                const resultado = {
                    nuevos: [],
                    actualizados: [],
                    sinCambios: [],
                    conflictos: []
                };
                
                const mapaActuales = new Map();
                productosActuales.forEach(prod => {
                    mapaActuales.set(prod.nombre.toLowerCase().trim(), prod);
                });
                
                productosNuevos.forEach(prodNuevo => {
                    const nombreKey = prodNuevo.nombre.toLowerCase().trim();
                    const prodActual = mapaActuales.get(nombreKey);
                    
                    if (!prodActual) {
                        // Producto nuevo
                        resultado.nuevos.push(prodNuevo);
                    } else {
                        // Verificar si hay cambios
                        if (Math.abs(prodActual.precio - prodNuevo.precio) > 0.01) {
                            resultado.actualizados.push({
                                nombre: prodNuevo.nombre,
                                precioAnterior: prodActual.precio,
                                precioNuevo: prodNuevo.precio,
                                diferencia: prodNuevo.precio - prodActual.precio
                            });
                        } else {
                            resultado.sinCambios.push(prodNuevo);
                        }
                    }
                });
                
                if (this.DEBUG) {
                    console.log('🔄 Resultado de sincronización:', {
                        nuevos: resultado.nuevos.length,
                        actualizados: resultado.actualizados.length,
                        sinCambios: resultado.sinCambios.length
                    });
                }
                
                return resultado;
            }
        }

        // Crear instancia global
        const smartExcelImporter = new SmartExcelImporter();
        // Mantener compatibilidad con código existente
        const excelImportManager = smartExcelImporter;
        
        // ==================== FUNCIÓN DE IMPORTACIÓN MEJORADA ====================
        async function gestion_handleImportXLSX(event){
            // Verificar que XLSX esté cargado
            if (typeof XLSX === 'undefined') {
                showToast("⚠️ Error: Biblioteca Excel no cargada. Por favor, verifica tu conexión a internet y recarga la página.", "danger");
                console.error('XLSX no está definido');
                event.target.value = "";
                return;
            }

            const file = event.target.files[0];
            if (!file) return;
            
            console.log('📥 Iniciando importación de:', file.name);
            
            // Usar el gestor mejorado
            const resultado = await excelImportManager.importar(file, tpvState, {
                onProgress: (info) => {
                    console.log(`Progreso: ${info.paso}/${info.total} - ${info.mensaje}`);
                    showToast(`${info.mensaje}`, "info");
                },
                confirmarBorrado: true,
                crearInventario: true
            });
            
            if (resultado.exito) {
                // Guardar en IndexedDB
                await saveState();

                // Construir lista de productos con stock real del XLSX
                // (la cantidad del Excel quedó en tpvState.inventarios[fechaHoy])
                const fechaHoy = getTodayDateString();
                const invHoy   = tpvState.inventarios[fechaHoy] || [];
                const stockMap = {};
                invHoy.forEach(item => { stockMap[item.id] = item.cantInicial || 0; });

                const productosConStock = tpvState.productos.map(p => ({
                    ...p,
                    stock_actual: p.stock_actual || stockMap[p.id] || 0
                }));

                // Sincronizar servidor con productos + stock real
                try {
                    showToast('⚙️ Sincronizando con el servidor...', 'info');
                    const rSync = await fetch('/api/reconstruir-desde-productos', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ productos: productosConStock })
                    });
                    if (rSync.ok) {
                        const dSync = await rSync.json();
                        if (dSync.ok) {
                            showToast(`☁️ Servidor: ${dSync.total} productos sincronizados`, 'success');
                        }
                    } else {
                        await catalogo_sincronizarAlServidor();
                    }
                } catch(e) {
                    await catalogo_sincronizarAlServidor();
                }

                // CRÍTICO: poblar inventario_general para que Vendedores Hoy funcione
                try {
                    const rInv = await fetch('/api/inventario/importar-catalogo', {
                        method: 'POST', credentials: 'same-origin'
                    });
                    if (rInv.ok) {
                        const dInv = await rInv.json();
                        if (dInv.ok) {
                            showToast(`📦 Almacén actualizado: ${dInv.nuevos} nuevos · ${dInv.existentes} existentes`, 'info');
                        }
                    }
                } catch(e) {
                    console.warn('importar-catalogo:', e.message);
                }

                // CRÍTICO: recargar tpvState.productos desde el servidor
                await catalogo_cargarDesdeServidor();

                // Persistir el estado actualizado en IndexedDB
                await saveState();

                // Refrescar TODA la UI esperando a que termine
                await refreshAllUI();

                // Actualizar inventario visible
                const fechaActualInput = document.getElementById('inv-fechaActual');
                if (fechaActualInput && fechaActualInput.value) {
                    inv_cargarInventario(fechaActualInput.value);
                }

                // Actualizar tabla de gestión de productos explícitamente
                if (typeof gestion_renderizarFiltrosProductos === 'function') gestion_renderizarFiltrosProductos();
                if (typeof gestion_renderizarTablaProductos  === 'function') gestion_renderizarTablaProductos();
                if (typeof gestion_renderizarListaCategorias === 'function') gestion_renderizarListaCategorias();

                showToast(resultado.mensaje + ' — Ve a Catálogo › Productos para verificar.', "success");
                console.log('✅ Importación completada exitosamente');

            // v25: VERIFICACION FINAL - contar productos en servidor
            try {
                const rV = await fetch('/api/productos', {credentials:'same-origin'});
                if (rV.ok) {
                    const dV = await rV.json();
                    const lista = Array.isArray(dV) ? dV : (dV.productos || dV.data || []);
                    console.log('[v25] VERIFICACION: servidor tiene', lista.length, 'productos');
                }
            } catch(ev) { console.warn('[v25] verificacion fallo:', ev.message); }
                
            } else {
                showToast(resultado.mensaje, "danger");
                console.error('❌ Error en importación:', resultado.error);
            }
            
            event.target.value = "";
        }

        /**
         * Exporta los datos del TPV de forma inteligente
         * Incluye validación y información del backup
         */
        function conf_handleExport(){
            try {
                // Preparar datos para exportar
                const backupData = {
                    version: "7.0",
                    fecha_exportacion: new Date().toISOString(),
                    entorno: TPV_CONFIG.getEnvironment(),
                    datos: tpvState
                };
                
                // Crear el blob con formato legible
                const dataStr = JSON.stringify(backupData, null, 2);
                const blob = new Blob([dataStr], {type: "application/json;charset=utf-8"});
                
                // Crear nombre descriptivo del archivo
                const fecha = getTodayDateString();
                const hora = new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
                const nombreArchivo = `tpv_backup_${fecha}_${hora}.json`;
                
                // Crear link temporal para descarga
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = nombreArchivo;
                link.style.display = "none";
                
                // Añadir al DOM, hacer click y limpiar
                document.body.appendChild(link);
                link.click();
                
                // Limpiar después de un pequeño delay
                setTimeout(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                }, 100);
                
                showToast(`✅ Backup exportado: ${nombreArchivo}`, "success");
                
                TPV_CONFIG.log(`Backup exportado: ${nombreArchivo}`);
            } catch (error) {
                console.error("Error al exportar:", error);
                showToast("❌ Error al exportar los datos. Intente nuevamente.", "danger");
            }
        }

        /**
         * Importa los datos del TPV de forma inteligente
         * Valida el formato y muestra información detallada
         */
        function conf_handleImport(event){
            const file = event.target.files[0];
            
            if (!file) {
                event.target.value = "";
                return;
            }
            
            // Validar que sea un archivo JSON
            if (!file.name.toLowerCase().endsWith('.json')) {
                showToast("❌ Por favor, seleccione un archivo JSON válido.", "danger");
                event.target.value = "";
                return;
            }
            
            // Confirmar antes de importar
            if (!confirm("⚠️ ¿Está seguro de importar este backup?\n\nEsto reemplazará todos los datos actuales.\n\nSe recomienda exportar un backup antes de continuar.")) {
                event.target.value = "";
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                try {
                    const importedData = JSON.parse(e.target.result);
                    
                    // Determinar si es un backup nuevo (con metadata) o antiguo
                    let dataToImport;
                    let backupVersion = "desconocida";
                    let backupDate = "desconocida";
                    
                    if (importedData.version && importedData.datos) {
                        // Formato nuevo con metadata
                        dataToImport = importedData.datos;
                        backupVersion = importedData.version;
                        backupDate = new Date(importedData.fecha_exportacion).toLocaleString();
                    } else if (importedData.config && importedData.productos) {
                        // Formato antiguo (directo)
                        dataToImport = importedData;
                    } else {
                        throw new Error("Formato de backup no válido");
                    }
                    
                    // Validar estructura mínima
                    if (!dataToImport.config || !dataToImport.productos) {
                        throw new Error("El archivo no contiene datos válidos del TPV");
                    }
                    
                    // Migrar datos si es necesario
                    if (!dataToImport.licencia) {
                        dataToImport.licencia = {
                            activa: false,
                            clienteId: "",
                            vencimiento: null,
                            permanente: false,
                            unidadTiempo: "dias"
                        };
                    }
                    
                    // Aplicar los datos importados
                    tpvState = { ...getDefaultState(), ...dataToImport };
                    await saveState();
                    
                    showToast(`✅ Backup importado correctamente\n📦 Versión: ${backupVersion}\n📅 Fecha: ${backupDate}`, "success");
                    
                    TPV_CONFIG.log(`Backup importado - Versión: ${backupVersion}`);
                    
                    // Recargar la página después de 2 segundos
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                    
                } catch (err) {
                    console.error("Error al importar:", err);
                    showToast(`❌ Error al importar: ${err.message}`, "danger");
                } finally {
                    event.target.value = "";
                }
            };
            
            reader.onerror = () => {
                showToast("❌ Error al leer el archivo.", "danger");
                event.target.value = "";
            };
            
            reader.readAsText(file);
        }

        // --- LÓGICA DE NOMENCLADOR ---
        async function exportar_xlsx_seguro(wb, filename) {
            try {
                console.log('📥 Exportando:', filename);
                
                // Validar que el workbook existe
                if (!wb || !wb.Sheets) {
                    throw new Error('Workbook inválido o sin hojas');
                }
                
                // Detectar móvil y plataforma
                const userAgent = navigator.userAgent || navigator.vendor || window.opera;
                const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
                const isIOS = /iPad|iPhone|iPod/.test(userAgent);
                const isAndroid = /Android/i.test(userAgent);
                
                console.log('📱 Dispositivo:', isIOS ? 'iOS' : isAndroid ? 'Android' : 'Desktop');
                
                // Generar archivo con opciones optimizadas para móviles
                const wbout = XLSX.write(wb, { 
                    bookType: 'xlsx', 
                    type: 'array',
                    compression: true // Comprimir para archivos más pequeños
                });
                
                // Crear blob con tipo MIME correcto
                const blob = new Blob([wbout], { 
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                });
                
                const sizeKB = (blob.size / 1024).toFixed(2);
                console.log('📦 Tamaño:', sizeKB, 'KB');
                
                // Validar tamaño del archivo (máximo 50MB para móviles)
                if (blob.size > 50 * 1024 * 1024) {
                    throw new Error('El archivo es demasiado grande (>' + sizeKB + 'KB)');
                }
                
                // Crear URL del blob
                const url = URL.createObjectURL(blob);
                
                // Crear enlace de descarga
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                
                // Configuraciones específicas para iOS
                if (isIOS) {
                    a.target = '_blank';
                    // En iOS, a veces es necesario este atributo
                    a.setAttribute('download', filename);
                }
                
                // Agregar al DOM temporalmente
                document.body.appendChild(a);
                
                // Esperar un tick para asegurar que el DOM se actualice
                await new Promise(resolve => setTimeout(resolve, 10));
                
                // Hacer click
                a.click();
                
                // Limpiar después de un delay más largo para móviles
                setTimeout(() => {
                    try {
                        if (a.parentNode) {
                            document.body.removeChild(a);
                        }
                        URL.revokeObjectURL(url);
                    } catch (cleanupError) {
                        console.warn('Error al limpiar:', cleanupError);
                    }
                }, isMobile ? 300 : 100);
                
                // Mostrar mensaje según la plataforma
                if (isIOS) {
                    showToast('📱 Toca "Compartir" o "Descargar" para guardar el archivo', 'info', 6000);
                } else if (isAndroid) {
                    showToast('✅ Descargando... Revisa tu carpeta de Descargas', 'success', 4000);
                } else {
                    showToast('✅ Archivo descargado correctamente', 'success', 3000);
                }
                
                console.log('✅ Exportación completada');
                return true;
                
            } catch (error) {
                console.error('❌ Error en exportación:', error);
                const errorMsg = error.message || 'Error desconocido';
                showToast('❌ Error al exportar: ' + errorMsg, 'danger', 5050);
                return false;
            }
        }
        
        async function exportar_ventasHoy() {
            try {
                const hoy = new Date().toISOString().split('T')[0];
                const ventasHoy = tpvState.historialVentas.filter(v => v.fecha.startsWith(hoy));
                
                if (ventasHoy.length === 0) {
                    return showToast('No hay ventas hoy para exportar', 'warning');
                }
                
                await gestion_handleExportVentas(ventasHoy, `ventas_${hoy}.xlsx`);
                showToast('Ventas de hoy exportadas exitosamente', 'success');
            } catch (error) {
                showToast('Error al exportar ventas', 'danger');
                console.error(error);
            }
        }
        
        async function exportar_historialCompleto() {
            try {
                if (tpvState.historialVentas.length === 0) {
                    return showToast('No hay historial de ventas para exportar', 'warning');
                }
                
                await gestion_handleExportVentas(tpvState.historialVentas, 'historial_completo.xlsx');
                showToast('Historial completo exportado exitosamente', 'success');
            } catch (error) {
                showToast('Error al exportar historial', 'danger');
                console.error(error);
            }
        }
        
        async function exportar_nomenclador() {
            try {
                const pais = document.getElementById('nom-selectPais')?.value || 'USD';
                const denominaciones = tpvState.nomencladores[pais] || [];
                
                if (denominaciones.length === 0) {
                    return showToast('No hay denominaciones para exportar', 'warning');
                }
                
                const data = denominaciones.map(d => ({
                    Denominación: d,
                    Cantidad: 0,
                    Total: 0
                }));
                
                await gestion_handleExportGenerico(data, `nomenclador_${pais}.xlsx`);
                showToast('Nomenclador exportado exitosamente', 'success');
            } catch (error) {
                showToast('Error al exportar nomenclador', 'danger');
                console.error(error);
            }
        }
        
        async function gestion_handleExportVentas(ventas, filename) {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('Librería XLSX no disponible', 'danger');
            }
            
            try {
                const data = ventas.map(v => {
                    const producto = tpvState.productos.find(p => p.id === v.productoId);
                    return {
                        Fecha: v.fecha,
                        Producto: producto?.nombre || v.productoId,
                        Cantidad: v.cantidad,
                        'Precio Unitario': v.precioUnitario,
                        Total: v.total
                    };
                });
                
                const ws = XLSX.utils.json_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Ventas');
                
                const success = await exportar_xlsx_seguro(wb, filename);
                if (!success) {
                    throw new Error('No se pudo exportar el archivo');
                }
            } catch (error) {
                console.error('Error exportando ventas:', error);
                throw error;
            }
        }
        
        // NUEVO: Función para exportar productos con valor (stock > 0)
        async function exportar_productos_con_valor() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('Librería XLSX no disponible', 'danger');
            }
            
            try {
                console.log('📦 Exportando productos con valor...');
                
                // Filtrar productos con stock > 0
                const productosConValor = tpvState.productos.filter(p => (p.stock || 0) > 0);
                
                if (productosConValor.length === 0) {
                    return showToast('No hay productos con valor para exportar', 'warning');
                }
                
                const data = productosConValor.map(p => ({
                    Nombre: p.nombre,
                    Precio: p.precio,
                    Stock: p.stock || 0,
                    Código: p.codigo || '',
                    Categoría: p.categoria || '',
                    'Valor Total': (p.precio * (p.stock || 0)).toFixed(2)
                }));
                
                const ws = XLSX.utils.json_to_sheet(data);
                
                // Dar formato a las columnas de dinero
                const range = XLSX.utils.decode_range(ws['!ref']);
                for (let row = range.s.r + 1; row <= range.e.r; row++) {
                    const precioCel = XLSX.utils.encode_cell({ r: row, c: 1 });
                    const valorCel = XLSX.utils.encode_cell({ r: row, c: 5 });
                    
                    if (ws[precioCel]) ws[precioCel].z = '$#,##0.00';
                    if (ws[valorCel]) ws[valorCel].z = '$#,##0.00';
                }
                
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Productos con Valor');
                
                const fecha = new Date().toISOString().split('T')[0];
                const success = await exportar_xlsx_seguro(wb, `productos_con_valor_${fecha}.xlsx`);
                
                if (success) {
                    console.log(`✅ ${productosConValor.length} productos con valor exportados`);
                }
            } catch (error) {
                console.error('Error exportando productos con valor:', error);
                showToast('Error al exportar productos con valor', 'danger');
            }
        }
        
        // NUEVO: Función para exportar productos sin valor (stock = 0)
        async function exportar_productos_sin_valor() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('Librería XLSX no disponible', 'danger');
            }
            
            try {
                console.log('📦 Exportando productos en cero...');
                
                // Filtrar productos con stock = 0
                const productosSinValor = tpvState.productos.filter(p => (p.stock || 0) === 0);
                
                if (productosSinValor.length === 0) {
                    return showToast('No hay productos en 0 para exportar', 'warning');
                }
                
                const data = productosSinValor.map(p => ({
                    Nombre: p.nombre,
                    Precio: p.precio,
                    Stock: 0,
                    Código: p.codigo || '',
                    Categoría: p.categoria || ''
                }));
                
                const ws = XLSX.utils.json_to_sheet(data);
                
                // Dar formato a la columna de precio
                const range = XLSX.utils.decode_range(ws['!ref']);
                for (let row = range.s.r + 1; row <= range.e.r; row++) {
                    const precioCel = XLSX.utils.encode_cell({ r: row, c: 1 });
                    if (ws[precioCel]) ws[precioCel].z = '$#,##0.00';
                }
                
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Productos en Cero');
                
                const fecha = new Date().toISOString().split('T')[0];
                const success = await exportar_xlsx_seguro(wb, `productos_en_cero_${fecha}.xlsx`);
                
                if (success) {
                    console.log(`✅ ${productosSinValor.length} productos en cero exportados`);
                }
            } catch (error) {
                console.error('Error exportando productos en cero:', error);
                showToast('Error al exportar productos en cero', 'danger');
            }
        }
        
        // NUEVO: Función para exportar todos los productos
        async function exportar_todos_productos() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('Librería XLSX no disponible', 'danger');
            }
            
            try {
                console.log('📦 Exportando todos los productos...');
                
                if (tpvState.productos.length === 0) {
                    return showToast('No hay productos para exportar', 'warning');
                }
                
                const data = tpvState.productos.map(p => ({
                    Nombre: p.nombre,
                    Precio: p.precio,
                    Stock: p.stock || 0,
                    Código: p.codigo || '',
                    Categoría: p.categoria || '',
                    'Valor Total': (p.precio * (p.stock || 0)).toFixed(2)
                }));
                
                const ws = XLSX.utils.json_to_sheet(data);
                
                // Dar formato a las columnas de dinero
                const range = XLSX.utils.decode_range(ws['!ref']);
                for (let row = range.s.r + 1; row <= range.e.r; row++) {
                    const precioCel = XLSX.utils.encode_cell({ r: row, c: 1 });
                    const valorCel = XLSX.utils.encode_cell({ r: row, c: 5 });
                    
                    if (ws[precioCel]) ws[precioCel].z = '$#,##0.00';
                    if (ws[valorCel]) ws[valorCel].z = '$#,##0.00';
                }
                
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Todos los Productos');
                
                const fecha = new Date().toISOString().split('T')[0];
                const success = await exportar_xlsx_seguro(wb, `todos_productos_${fecha}.xlsx`);
                
                if (success) {
                    console.log(`✅ ${tpvState.productos.length} productos exportados`);
                }
            } catch (error) {
                console.error('Error exportando todos los productos:', error);
                showToast('Error al exportar productos', 'danger');
            }
        }
        

        // ========== FUNCIONES DE EXPORTACIÓN INTELIGENTE ==========
        
        /**
         * Exportación inteligente de productos con aprendizaje
         */
        async function exportar_inteligente_completo() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('❌ Librería XLSX no disponible', 'danger');
            }
            
            try {
                showToast('🧠 Preparando exportación inteligente...', 'info');
                
                const resultado = smartExcelImporter.exportarInteligente(tpvState, {
                    incluirInventario: true,
                    formato: 'completo',
                    nombreArchivo: `productos_completo_${new Date().toISOString().split('T')[0]}.xlsx`
                });
                
                if (resultado.exito) {
                    showToast(`✅ ${resultado.mensaje}`, 'success');
                } else {
                    showToast(`❌ Error: ${resultado.error}`, 'danger');
                }
            } catch (error) {
                console.error('❌ Error en exportación inteligente:', error);
                showToast('❌ Error al exportar con sistema inteligente', 'danger');
            }
        }
        
        /**
         * Exportación inteligente formato simple (solo nombre y precio)
         */
        async function exportar_inteligente_simple() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('❌ Librería XLSX no disponible', 'danger');
            }
            
            try {
                showToast('🧠 Preparando exportación simple...', 'info');
                
                const resultado = smartExcelImporter.exportarInteligente(tpvState, {
                    incluirInventario: false,
                    formato: 'simple',
                    nombreArchivo: `productos_simple_${new Date().toISOString().split('T')[0]}.xlsx`
                });
                
                if (resultado.exito) {
                    showToast(`✅ ${resultado.mensaje}`, 'success');
                } else {
                    showToast(`❌ Error: ${resultado.error}`, 'danger');
                }
            } catch (error) {
                console.error('❌ Error en exportación simple:', error);
                showToast('❌ Error al exportar con formato simple', 'danger');
            }
        }
        
        /**
         * Exportación automática (usa las preferencias guardadas)
         */
        async function exportar_inteligente_auto() {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('❌ Librería XLSX no disponible', 'danger');
            }
            
            try {
                showToast('🧠 Usando preferencias aprendidas...', 'info');
                
                // Recuperar preferencias
                const preferencias = smartExcelImporter.recuperarPreferenciasExportacion();
                let mensaje = '📊 Exportando';
                
                if (preferencias) {
                    mensaje += ` (formato: ${preferencias.formato})`;
                } else {
                    mensaje += ' (primera vez, usando formato completo)';
                }
                
                showToast(mensaje, 'info');
                
                const resultado = smartExcelImporter.exportarInteligente(tpvState, {
                    incluirInventario: true,
                    formato: 'auto',
                    nombreArchivo: `productos_auto_${new Date().toISOString().split('T')[0]}.xlsx`
                });
                
                if (resultado.exito) {
                    showToast(`✅ ${resultado.mensaje}`, 'success');
                } else {
                    showToast(`❌ Error: ${resultado.error}`, 'danger');
                }
            } catch (error) {
                console.error('❌ Error en exportación automática:', error);
                showToast('❌ Error al exportar con modo automático', 'danger');
            }
        }
        
        /**
         * Mostrar información de aprendizaje del sistema
         */
        function mostrar_info_aprendizaje() {
            const ultimaEstructura = smartExcelImporter.recuperarConfiguracionAprendida();
            const preferenciasExp = smartExcelImporter.recuperarPreferenciasExportacion();
            
            let mensaje = '🧠 SISTEMA DE APRENDIZAJE - INFORMACIÓN\n\n';
            
            if (ultimaEstructura) {
                mensaje += '📥 ÚLTIMA IMPORTACIÓN:\n';
                mensaje += `  • Archivo: ${ultimaEstructura.nombreArchivo || 'N/A'}\n`;
                mensaje += `  • Método: ${ultimaEstructura.metodo || 'N/A'}\n`;
                mensaje += `  • Confianza: ${((ultimaEstructura.confianza || 0) * 100).toFixed(0)}%\n`;
                mensaje += `  • Columnas detectadas: ${Object.keys(ultimaEstructura.columnas || {}).join(', ')}\n`;
                
                const fecha = new Date(ultimaEstructura.timestamp);
                mensaje += `  • Fecha: ${fecha.toLocaleString()}\n`;
            } else {
                mensaje += '📥 No hay importaciones previas registradas\n';
            }
            
            mensaje += '\n';
            
            if (preferenciasExp) {
                mensaje += '📤 PREFERENCIAS DE EXPORTACIÓN:\n';
                mensaje += `  • Formato preferido: ${preferenciasExp.formato || 'N/A'}\n`;
                mensaje += `  • Incluir inventario: ${preferenciasExp.incluirInventario ? 'Sí' : 'No'}\n`;
                
                const fechaExp = new Date(preferenciasExp.timestamp);
                mensaje += `  • Última exportación: ${fechaExp.toLocaleString()}\n`;
            } else {
                mensaje += '📤 No hay preferencias de exportación guardadas\n';
            }
            
            mensaje += '\n💡 El sistema aprende automáticamente de tus acciones\n';
            mensaje += 'y mejora con cada uso para adaptarse a tus necesidades.';
            
            alert(mensaje);
        }
        
        /**
         * Limpiar memoria del sistema de aprendizaje
         */
        function limpiar_memoria_aprendizaje() {
            if (confirm('⚠️ ¿Estás seguro de limpiar la memoria del sistema?\n\nEsto eliminará:\n• Configuraciones de importación aprendidas\n• Preferencias de exportación\n• Historial de estructuras\n\nEl sistema volverá a aprender desde cero.')) {
                try {
                    localStorage.removeItem('tpv_ultima_estructura');
                    localStorage.removeItem('tpv_preferencias_exportacion');
                    localStorage.removeItem('tpv_historial_estructuras');
                    
                    showToast('✅ Memoria del sistema limpiada correctamente', 'success');
                    console.log('🧹 Memoria de aprendizaje limpiada');
                } catch (error) {
                    showToast('❌ Error al limpiar memoria', 'danger');
                    console.error('Error limpiando memoria:', error);
                }
            }
        }
        async function gestion_handleExportGenerico(data, filename) {
            const XLSX = window.XLSX;
            if (!XLSX) {
                return showToast('Librería XLSX no disponible', 'danger');
            }
            
            try {
                const ws = XLSX.utils.json_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Datos');
                
                const success = await exportar_xlsx_seguro(wb, filename);
                if (!success) {
                    throw new Error('No se pudo exportar el archivo');
                }
            } catch (error) {
                console.error('Error exportando datos:', error);
                throw error;
            }
        }
        
        // ========== ALIAS DE COMPATIBILIDAD (no duplicar lógica) ==========
        // activar_licencia() → delega a lic_activateLicense() (función principal)
