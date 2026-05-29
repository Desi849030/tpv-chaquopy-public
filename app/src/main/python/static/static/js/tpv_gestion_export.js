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


