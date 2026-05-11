// tpv_gestion_productos.js — CRUD productos, categorías, import/export Excel
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

