// ════════════════════════════════════════════════════════════════
// app3/06_gestion.js — Gestión de productos y categorías + exportación XLSX
// Extraído de app_3.js (líneas 1674–2571) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
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
            if (!(await tpvConfirm(
                '⚠️ LIMPIEZA TOTAL\n\n' +
                'Borrará productos de:\n' +
                '  • Catálogo visible (memoria)\n' +
                '  • Inventario (memoria)\n' +
                '  • Navegador (IndexedDB)\n' +
                '  • Base de datos del servidor\n\n' +
                '¿Continuar?'
            ))) return;
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
            if (!(await tpvConfirm(
                '🔄 LIMPIAR Y REIMPORTAR\n\n' +
                'Borrará TODO (memoria + navegador + servidor)\n' +
                'y reconstruirá el servidor desde el catálogo local actual.\n\n' +
                '¿Continuar?'
            ))) return;
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

            // Sincronizar producto al servidor via TPV_API
            if (window.TPV_API) {
                const esActualizacion = index > -1;
                const apiProducto = {
                    id: producto.id,
                    nombre: producto.nombre,
                    categoria: producto.categoria,
                    precio: producto.precio,
                    costo_unitario: producto.costoUnitario,
                    um: producto.um,
                    imagen: producto.imagen,
                    on_sale: producto.onSale
                };
                if (esActualizacion) {
                    TPV_API.catalogo.importarExcel([apiProducto]).then(result => {
                        if (result && result.ok) console.log('✅ Producto actualizado via API:', producto.nombre);
                    }).catch(e => console.warn('⚠️ Producto no sincronizado:', e.message));
                } else {
                    TPV_API.catalogo.importarExcel([apiProducto]).then(result => {
                        if (result && result.ok) console.log('✅ Producto creado via API:', producto.nombre);
                    }).catch(e => console.warn('⚠️ Producto no sincronizado:', e.message));
                }
            }

            const currentActiveTabPane = document.querySelector('.tab-pane.fade.show.active');
            if (currentActiveTabPane && currentActiveTabPane.id === 'cliente-qr-tab-pane') {
                cliente_generarEtiquetas();
            }
        }

        async function gestion_eliminarProducto(id){
            if((await tpvConfirm(getLang().confirm_delete_product))){
                tpvState.productos = tpvState.productos.filter(p => p.id !== id);
                gestion_renderizarTablaProductos();
                tpv_renderizarProductos();
                await saveState();
                catalogo_sincronizarAlServidor(); // ← todos los roles ven el cambio

                // Sincronizar eliminación al servidor via TPV_API
                if (window.TPV_API) {
                    TPV_API.catalogo.importarExcel(tpvState.productos.map(p => ({
                        id: p.id, nombre: p.nombre, categoria: p.categoria,
                        precio: p.precio, costo_unitario: p.costoUnitario,
                        um: p.um, imagen: p.imagen, on_sale: p.onSale
                    }))).then(result => {
                        if (result && result.ok) console.log('✅ Catálogo sincronizado tras eliminación via API');
                    }).catch(e => console.warn('⚠️ Eliminación no sincronizada:', e.message));
                }

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
            if ((await tpvConfirm(lang.confirm_delete_category))) {
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


