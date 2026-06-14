// ════════════════════════════════════════════════════════════════
// app3/02_ui_core.js — Inicialización de UI, helpers, etiquetas/QR de cliente, tabs, toasts, idioma y tema
// Extraído de app_3.js (líneas 470–858) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
async function initializeUI() {
            addToCartModal = new bootstrap.Modal('#addToCartModal');
            processPaymentModal = new bootstrap.Modal('#processPaymentModal');
            editSaleModal = new bootstrap.Modal('#editSaleModal');
            gestionModalProducto = new bootstrap.Modal('#gestion-modal-producto');
            invModalStock = new bootstrap.Modal('#inv-modal-stock');
            gestionModalCategoria = new bootstrap.Modal('#gestion-modal-categoria');
            
            document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => tab.addEventListener('shown.bs.tab', handleTabChange));
            document.getElementById('conf-language-selector')?.addEventListener('change', (e) => conf_setLanguage(e.target.value));
            document.getElementById('conf-theme-toggle')?.addEventListener('change', (e) => conf_setTheme(e.target.checked ? 'dark' : 'light'));
            
            await refreshAllUI();
        }

        async function refreshAllUI() {
            const { config } = tpvState;
            document.getElementById('conf-language-selector') && (document.getElementById('conf-language-selector').value = config.lang);
            conf_setTheme(config.theme);
            document.getElementById('conf-theme-toggle') && (document.getElementById('conf-theme-toggle').checked = (config.theme === 'dark'));
            document.getElementById('inv-globalProfitPercent') && (document.getElementById('inv-globalProfitPercent').value = config.globalProfitPercent);
            if (typeof _actualizarBotonesLang === 'function') _actualizarBotonesLang(config.lang || 'es');
            conf_setLanguage(config.lang).catch(function(){});

            // Siempre recargar catálogo del servidor (fuente de verdad)
            await catalogo_cargarDesdeServidor();

            tpv_renderizarProductos();
            tpv_renderizarFiltroCategorias();
            tpv_renderizarPedido();
            gestion_renderizarFiltrosProductos();
            gestion_renderizarTablaProductos();
            gestion_renderizarListaCategorias();
            ventas_renderizarTablaHoy();
            registros_renderizar();
            document.getElementById('nom-selectPais') && nom_cargarDenominaciones(document.getElementById('nom-selectPais').value);
            lic_checkLicense();
            cliente_renderizarDropdownCategoriasQR(); 
            
            // Inicializar nuevas pestañas
            actualizar_lista_backups();
            mostrar_info_licencia();
            actualizar_logs();
            
            const _invFechaEl = document.getElementById('inv-fechaActual'); if (_invFechaEl) _invFechaEl.value = getTodayDateString();
            inv_cargarInventario(getTodayDateString());
        }

        // --- HELPERS ---
        const getLang = () => {
            // Verificación segura: si tpvState o config no existen, usar español por defecto
            if (!tpvState || !tpvState.config || !tpvState.config.lang) {
                return i18n.es;
            }
            return i18n[tpvState.config.lang] ?? i18n.es;
        };
        const formatCurrency = (amount) => `$${Number(amount ?? 0).toFixed(2)}`;
        const getTodayDateString = () => new Date().toISOString().split('T')[0];

        // --- LÓGICA DE ETIQUETAS DE PRODUCTO (QR) ---

        function cliente_renderizarDropdownCategoriasQR() {
            const categorySelector = document.getElementById('cliente-qr-category-selector');
            if (!categorySelector) return;

            const lang = getLang();
            let optionsHTML = `<option value="all">${lang.all_categories}</option>`;
            const categoriasOrdenadas = [...tpvState.categorias].sort((a, b) => a === 'General' ? -1 : b === 'General' ? 1 : a.localeCompare(b));
            optionsHTML += categoriasOrdenadas.map(c => `<option value="${c}">${c}</option>`).join('');
            categorySelector.innerHTML = optionsHTML;
        }
        
        function cliente_crearTarjetaEtiquetaProducto(product, containerElement, lang) {
            const qrSvgId = `qr-container-${product.id}`;
            const cardId = `label-card-${product.id}`;
            const isSelected = clienteQRSeleccionados.some(p => p.id === product.id);

            const cardHtml = `
                <div id="${cardId}" class="product-label-card p-2 ${isSelected ? 'selected-for-grouping' : ''}" onclick="cliente_toggleProductoQR('${product.id}')">
                    <div class="flex-grow-1">
                        <h6>${product.nombre}</h6>
                        <p class="fw-bold mb-2">${formatCurrency(product.precio)}</p>
                        <div class="d-flex flex-column align-items-center my-2">
                            <div id="${qrSvgId}" class="p-1" style="background-color: white;"></div>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-secondary mt-1 w-100" onclick="event.stopPropagation(); gestion_abrirModalProducto('${product.id}')" data-i18n="btn_edit_product_label">${lang.btn_edit_product_label}</button>
                    </div>
                </div>
            `;
            containerElement.insertAdjacentHTML('beforeend', cardHtml);
            
            const qrElement = containerElement.querySelector(`#${qrSvgId}`);
            try {
                new QRCode(qrElement, {
                    text: product.id,
                    width: 100,
                    height: 100,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.M 
                });
            } catch (e) {
                console.error(`Error generando QR para ${product.id}:`, e);
                qrElement.innerHTML = `<div class="code-error-indicator"><i class="bi bi-exclamation-triangle-fill"></i><small>Error QR</small></div>`;
            }
        }
        
        async function cliente_generarEtiquetas() {
            cliente_limpiarSeleccion(); 
            const displayContainer = document.getElementById('cliente-qr-display-container');
            const selectedCategory = document.getElementById('cliente-qr-category-selector')?.value || 'all';
            const lang = getLang();
            displayContainer.innerHTML = '';

            const productsToDisplay = (selectedCategory === 'all')
                ? [...tpvState.productos]
                : tpvState.productos.filter(p => p.categoria === selectedCategory);

            productsToDisplay.sort((a, b) => a.nombre.localeCompare(b.nombre));

            if (productsToDisplay.length === 0) {
                displayContainer.innerHTML = `<p class="text-center text-muted col-12">${lang.no_products_in_category}</p>`;
            } else {
                productsToDisplay.forEach(p => cliente_crearTarjetaEtiquetaProducto(p, displayContainer, lang));
            }
            const _qrUpd = document.getElementById('cliente-qr-last-updated'); if(_qrUpd) _qrUpd.innerText = new Date().toLocaleString();
        }

        // --- LÓGICA DE AGRUPACIÓN DE PRODUCTOS PARA QR ---

        function cliente_toggleProductoQR(id) {
            const index = clienteQRSeleccionados.findIndex(p => p.id === id);
            const cardElement = document.getElementById(`label-card-${id}`);

            if (index > -1) {
                clienteQRSeleccionados.splice(index, 1);
                cardElement?.classList.remove('selected-for-grouping');
            } else {
                const product = tpvState.productos.find(p => p.id === id);
                if (product) {
                    clienteQRSeleccionados.push({ id: product.id, nombre: product.nombre, precio: product.precio });
                    cardElement?.classList.add('selected-for-grouping');
                }
            }
            cliente_renderListaSeleccionados();
        }

        function cliente_renderListaSeleccionados() {
            const cont = document.getElementById('cliente-qr-lista-seleccionados');
            const lang = getLang();
            cont.innerHTML = '';

            if (clienteQRSeleccionados.length === 0) {
                cont.innerHTML = `<p class="text-muted small">${lang.no_products_selected_for_group}</p>`;
                return;
            }
            
            const ul = document.createElement('ul');
            ul.className = 'list-group list-group-flush';
            clienteQRSeleccionados.forEach(p => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center small p-1';
                li.textContent = `${p.nombre} - ${formatCurrency(p.precio)}`;
                const btn = document.createElement('button');
                btn.className = 'btn btn-sm btn-outline-danger p-0 px-1';
                btn.innerHTML = '×';
                btn.onclick = (e) => {
                    e.stopPropagation(); 
                    cliente_toggleProductoQR(p.id);
                };
                li.appendChild(btn);
                ul.appendChild(li);
            });
            cont.appendChild(ul);
        }
        
        function cliente_generarQRGrupo() {
            const displayContainer = document.getElementById('cliente-qr-grupo-display');
            displayContainer.innerHTML = '';
            const lang = getLang();

            if (clienteQRSeleccionados.length === 0) {
                showToast(lang.no_products_selected_for_group, "warning");
                return;
            }
            
            const totalWidth = 30; 
            
            const listTitle = lang.customer_catalog_group_qr_title;
            const productList = clienteQRSeleccionados.map(p => {
                const priceStr = formatCurrency(p.precio);
                const nameMaxLength = totalWidth - priceStr.length - 2; 
                let name = p.nombre;
                if (name.length > nameMaxLength) {
                    name = name.substring(0, nameMaxLength - 3) + '...';
                }
                const dots = '.'.repeat(totalWidth - name.length - priceStr.length);
                return `${name}${dots}${priceStr}`;
            }).join('\n');
            
            const data = `${listTitle}\n${'-'.repeat(totalWidth)}\n${productList}`;

            const titleElement = document.createElement('h6');
            titleElement.className = 'mt-3 small fw-bold';
            titleElement.setAttribute('data-i18n', 'customer_catalog_group_qr_title_ui');
            titleElement.innerText = lang.customer_catalog_group_qr_title_ui;
            displayContainer.appendChild(titleElement);
            
            const qrContainer = document.createElement('div');
            qrContainer.className = 'p-2 d-inline-block';
            qrContainer.style.backgroundColor = 'white';
            displayContainer.appendChild(qrContainer);

            new QRCode(qrContainer, {
                text: data,
                width: 180,
                height: 180,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.L
            });
        }

        function cliente_limpiarSeleccion() {
            document.querySelectorAll('.product-label-card.selected-for-grouping').forEach(el => {
                el.classList.remove('selected-for-grouping');
            });
            clienteQRSeleccionados = [];
            cliente_renderListaSeleccionados();
            const _qrGrp = document.getElementById('cliente-qr-grupo-display'); if(_qrGrp) _qrGrp.innerHTML = ''; 
        }

        function handleTabChange(event) {
            const targetId = event.target.getAttribute('data-bs-target');
            document.querySelectorAll('.dropdown-item').forEach(item => item.classList.remove('active'));
            const dropdownItem = document.querySelector(`.dropdown-item[data-bs-target="${targetId}"]`);
            if (dropdownItem) dropdownItem.classList.add('active');

            const refreshMap = {
                '#ventas-hoy-tab-pane': ventas_renderizarTablaHoy,
                '#registros-tab-pane': registros_renderizar,
                '#gestion-productos-tab-pane': async () => {
                    await catalogo_cargarDesdeServidor();
                    gestion_renderizarFiltrosProductos();
                    // Limpiar filtros de precio por si quedaron valores anteriores
                    const pMin = document.getElementById('gestion-filtro-precio-min');
                    const pMax = document.getElementById('gestion-filtro-precio-max');
                    if (pMin) pMin.value = '';
                    if (pMax) pMax.value = '';
                    gestion_renderizarTablaProductos();
                },
                '#dashboard-tab-pane': () => {
                    if (typeof dashboard_cargar === 'function') dashboard_cargar();
                },
                '#herramientas-tab-pane': (e) => {
                    if (typeof descuentos_cargarLista   === 'function') descuentos_cargarLista();
                    if (typeof actualizar_lista_backups === 'function') actualizar_lista_backups();
                    const tid = e?.target?.id || document.querySelector('.dropdown-item.active')?.id;
                    const smap = {'importar-exportar-tab':'seccion-importar-excel','copias-seguridad-tab':'seccion-copias-seguridad','herramientas-tab':'seccion-mantenimiento'};
                    const sec = smap[tid];
                    if (sec) setTimeout(()=>document.getElementById(sec)?.scrollIntoView({behavior:'smooth',block:'start'}),200);
                },
                '#gestion-categorias-tab-pane': gestion_renderizarListaCategorias,
                '#tpv-caja-tab-pane': () => { tpv_renderizarProductos(); tpv_renderizarFiltroCategorias(); },
                '#cliente-qr-tab-pane': () => {
                    cliente_renderizarDropdownCategoriasQR();
                    cliente_generarEtiquetas();
                },
                '#inv-inventario-tab-pane': () => {
                    const rol = window.AUTH?.usuario?.rol;
                    if (['administrador','desarrollador'].includes(rol)) {
                        if (typeof _setup_admin_inventario === 'function') _setup_admin_inventario();
                        // Siempre recargar datos frescos al entrar al tab
                        const activeBtn = document.querySelector('#inv-admin-btns .btn-primary, #inv-admin-btns .btn-success, #inv-admin-btns .btn-warning');
                        const btnId = activeBtn?.id;
                        if (btnId === 'inv-btn-vendedores') {
                            _admin_invVista('vendedores');
                        } else if (btnId === 'inv-btn-gastos') {
                            _admin_invVista('gastos');
                        } else {
                            // Almacén general — siempre recargar desde servidor
                            window._adminGeneral = [];
                            window._adminVends   = [];
                            _admin_invVista('almacen');
                            // Forzar recarga del almacén desde la API
                            if (typeof _admin_cargarVendedores === 'function') {
                                _admin_invVista('vendedores');
                                setTimeout(() => _admin_invVista('almacen'), 50);
                            }
                        }
                    }
                }
            };
            refreshMap[targetId]?.(event);
        }

        function showToast(message, type = 'info') { 
            const container = document.querySelector(".toast-container");
            const toastId = `toast-${Date.now()}`;
            const toastHTML = `<div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex"><div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
            container.insertAdjacentHTML("beforeend", toastHTML);
            const toastEl = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
            toast.show();
            toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
        }

        // --- LÓGICA DE CONFIGURACIÓN ---
        async function conf_setLanguage(lang) {
            tpvState.config.lang = lang;
            document.documentElement.lang = lang;
            const translations = getLang();
            
            try {
                document.querySelectorAll('[data-i18n]').forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    const translation = translations[key];
                    
                    if (typeof translation === 'function') {
                        if (key === 'license_trial') {
                           el.innerText = translation(lic_getRemainingDays());
                        }
                    } else if (translation !== undefined) {
                        el.innerText = translation;
                    }
                });

                document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                    const key = el.getAttribute('data-i18n-placeholder');
                    if (translations[key] !== undefined) {
                        el.placeholder = translations[key];
                    }
                });
            } catch (error) {
                console.error("Error al aplicar traducciones:", error);
            }

            // Actualizar el nombre del TPV después de cambiar idioma
            conf_updateTPVName();

            await saveState();
            cliente_renderizarDropdownCategoriasQR();
            if ((document.getElementById('cliente-qr-display-container')?.children.length > 0)) {
                cliente_generarEtiquetas();
            }
        }


        async function conf_setTheme(theme){
            tpvState.config.theme = theme;
            document.body.classList.toggle("dark-mode", theme === "dark");
            await saveState();
            const _qrCont = document.getElementById('cliente-qr-display-container');
            if (_qrCont && _qrCont.children.length > 0) {
                cliente_generarEtiquetas();
            }
        }

        // --- TPV (Catálogo y Orden) ---
        // Obtiene el stock actual de un producto desde el inventario de hoy
        function tpv_getStock(productoId) {
            const hoy = getTodayDateString();
            const _ir = tpvState.inventarios?.[hoy] || []; const inv = Array.isArray(_ir) ? _ir : Object.values(_ir);
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

                // ── Helper para detectar emojis en campo imagen ──
        function _isEmoji(str) {
            if (!str || typeof str !== 'string') return false;
            const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F000}-\u{1FFFF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/u;
            return emojiRegex.test(str) || (/^.{1,4}$/.test(str) && /[^\w\s.\/:\-\\]/.test(str));
        }

