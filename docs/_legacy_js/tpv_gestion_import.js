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

