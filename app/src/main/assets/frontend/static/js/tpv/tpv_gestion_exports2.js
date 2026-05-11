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
