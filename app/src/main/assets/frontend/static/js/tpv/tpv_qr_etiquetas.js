// tpv_qr_etiquetas.js — Generación QR y etiquetas para clientes
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

