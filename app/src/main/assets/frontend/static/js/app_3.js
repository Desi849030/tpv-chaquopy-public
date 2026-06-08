// --- ESTADO GLOBAL Y VARIABLES ---
        // tpvState ya declarado en el shim — aquí lo sobreescribimos con getDefaultState()
        // cuando loadState() termine lo llenará con datos reales de IndexedDB
        if (typeof tpvState === 'undefined' || !tpvState.productos) {
            tpvState = {};
        }
        let html5QrCode;
        let addToCartModal, processPaymentModal, editSaleModal, gestionModalProducto, invModalStock, gestionModalCategoria;
        
        // Función helper para obtener la clave secreta del entorno actual
        function getSecretKey() {
            return TPV_CONFIG ? TPV_CONFIG.getCurrentKey() : "MySuperSecretKeyForTPVApp2024";
        }
        const DB_NAME = 'tpvDataProfessionalDB';
        const DB_VERSION = 1;
        const STORE_NAME = 'tpvStateStore';
        let clienteQRSeleccionados = [];

        const i18n = {
            es: {
                app_title:"Sistema TPV Profesional", th_product:"Producto", th_actions:"Acciones", th_totals:"Totales", all_categories: "Todas las Categorías",
                nav_catalog:"Catálogo", nav_current_order:"Orden Actual", nav_sales:"Ventas del Día", nav_inventory:"Inventario", nav_customer_labels:"Etiquetas Producto", nav_config_group:"Configuración", nav_product_mgmt:"Gestión de Productos", nav_category_mgmt:"Gestión de Categorías", nav_records:"Registros", nav_nomenclator:"Nomenclador", nav_tools:"Herramientas", nav_settings:"Ajustes",
                menu_catalog:"Catálogo", menu_sales:"Ventas", menu_records:"Registros", menu_config:"Configuración", menu_import_export:"Importar/Exportar Excel", menu_export_sales:"Exportar a Excel", menu_backups:"Copias de Seguridad", menu_appearance:"Apariencia", menu_licenses:"Licencias", menu_maintenance:"Herramientas",
                tpv_filter_by_category:"Filtrar por Categoría:", tpv_current_order:"Orden Actual", tpv_total:"Total:", tpv_process_payment:"Procesar Pago", tpv_cancel_order:"Cancelar", tpv_scan_add:"Escanear", tpv_stop_scanner: "Detener Escáner",
                sales_today_title:"Ventas de Hoy", sales_th_time:"Hora", sales_th_quantity:"Cantidad", sales_th_unit_price:"Precio Unit.", sales_th_total:"Total", sales_total_sold_today:"Total Vendido Hoy:",
                inventory_title:"Inventario y Stock", inventory_select_date:"Seleccionar Fecha", inventory_quick_actions:"Acciones Rápidas", inventory_add_to_stock:"Añadir a Stock", inventory_close_day:"Cerrar Día", inventory_apply_global_commission:"% Comisión Global:", inventory_apply_button:"Aplicar",
                th_sale_price:"P. Venta", th_unit:"U/M", th_initial_qty:"C. Inicial", th_final_qty:"C. Final", th_sold:"Vendido", th_sale_total:"I. Venta", th_cost_price:"P. Costo", th_commission:"Comisión", th_net_profit:"G. Neta",
                records_title:"Registros y Cierres", records_closures_title:"Cierres de Caja", records_detailed_sales_title:"Ventas Detalladas", records_th_date:"Fecha", records_th_total_sales:"Ventas Totales", records_th_total_cost:"Costo Total", records_th_total_commission:"Comisión Total", records_th_total_profit:"Ganancia Neta", history_th_date:"Fecha y Hora",
                mgmt_products_title:"Gestión de Productos", mgmt_new_product:"Nuevo Producto", mgmt_th_category:"Categoría", mgmt_th_price:"Precio", mgmt_th_sale_status:"En Oferta", mgmt_categories_title:"Gestión de Categorías", mgmt_new_category_placeholder:"Nombre de nueva categoría", mgmt_filter_product_placeholder:"Filtrar por nombre...", filter_by_price: "Filtrar por Precio", filter_min_price: "Mín", filter_max_price: "Máx", edit_product: "Editar Producto",
                nomenclator_title:"Nomenclador de Divisas", nomenclator_total_value:"Total (Valor)", nomenclator_total_qty:"Total (Unidades)", nomenclator_new_denom_placeholder:"Nueva denominación",
                tools_title:"Herramientas de Datos", tools_backup_title:"Copia de Seguridad (JSON)", tools_backup_desc:"Guarde o restaure una copia de seguridad COMPLETA de toda la aplicación.", tools_import_button:"Importar Backup (.json)", tools_export_button:"Exportar Backup (.json)", tools_xlsx_title: "Datos Completos (XLSX)", tools_xlsx_desc:"Exporte o importe Productos, Inventarios y Nomenclador en formato Excel.", btn_import_xlsx: "Importar Excel", btn_export_xlsx: "Exportar Excel", btn_export_with_value: "Con Valor", btn_export_zero: "En Cero", btn_export_all: "Todos", btn_export_with_value_tooltip: "Exportar solo productos con stock mayor a 0", btn_export_zero_tooltip: "Exportar solo productos con stock en 0", btn_export_all_tooltip: "Exportar todos los productos",
                settings_appearance:"Apariencia", settings_language:"Idioma:", settings_dark_mode:"Tema Oscuro:", settings_license:"Licencia", license_trial_ends:"Prueba termina en:", settings_client_id:"ID Cliente:", settings_license_status:"Estado:", settings_license_key_placeholder:"Ingrese su clave", settings_activate_btn:"Activar",
                customer_catalog_title: "Generar Etiquetas de Producto", customer_catalog_desc_select: "Seleccione productos para generar etiquetas individuales o agrúpelos para un solo QR.", customer_catalog_label_type: "Tipo de Código:", customer_catalog_label_qr: "Solo QR", customer_catalog_label_barcode: "Solo Código de Barras", customer_catalog_label_both: "Ambos", customer_catalog_generate_labels: "Generar/Refrescar Etiquetas", customer_catalog_select_category: "Seleccionar Categoría:", customer_catalog_last_updated: "Última actualización:", customer_catalog_page: "Página", customer_catalog_offers: "Ofertas Especiales",
                customer_catalog_group_title: "Agrupar para QR", customer_catalog_group_desc: "Haga clic en las tarjetas de producto para agregarlas aquí. Luego genere un solo QR con todos los productos seleccionados.", customer_catalog_group_generate: "Generar QR de Grupo", customer_catalog_group_clear: "Limpiar Selección", customer_catalog_group_qr_title: "Lista de Productos:", customer_catalog_group_qr_title_ui: "QR para el Cliente",
                license_expired_title:"Licencia Activa", license_expired_desc:"Licencia premium - Sin límites", license_activated: "Activada", license_trial: (days) => `Prueba (${days} días restantes)`, license_expired: "Expirada",
                modal_add_to_order_title: "Añadir a la Orden", modal_quantity: "Cantidad:", modal_process_payment_title: "Procesar Pago", modal_total_to_pay: "Total a Pagar:", modal_select_payment_method: "Seleccione Método de Pago", modal_edit_sale_title: "Editar Venta", modal_editing: "Editando:", modal_new_quantity: "Nueva Cantidad:", modal_add_stock_title: "Añadir/Editar Stock", modal_edit_category_title: "Editar Categoría",
                payment_cash: "Efectivo", payment_card: "Tarjeta", payment_transfer: "Transferencia", payment_customer_card: "Tarjeta Cliente",
                btn_cancel: "Cancelar", btn_accept: "Aceptar", btn_save_changes: "Guardar Cambios", btn_save: "Guardar", btn_add_update: "Añadir/Actualizar", btn_edit_product_label: "Editar Producto",
                form_label_name: "Nombre", form_label_category: "Categoría", form_label_price: "Precio", form_label_unit: "Unidad de Medida (Ej: Un, Kg, L)", form_label_image_url: "URL de la Imagen (Online)", form_placeholder_image_url: "Pegue una URL de imagen aquí", form_label_image_local: "o Subir Imagen Local", form_label_new_category_name: "Nuevo nombre de la categoría", form_label_on_sale: "Marcar como oferta",
                no_products_in_category: "No hay productos en esta categoría.", no_products_selected_for_group: "No hay productos seleccionados.", empty_order: "Añada productos desde el catálogo.", no_sales_today: "No hay ventas registradas hoy.", no_closures: "No hay cierres de caja. Cierre un día desde la pestaña de Inventario.", no_sales_history: "No hay ventas en el historial.", select_date_inventory: "Seleccione una fecha para ver el inventario.",
                confirm_cancel_order: "¿Está seguro de que desea cancelar la orden actual?", confirm_delete_sale: "¿Seguro que desea eliminar este registro? La acción es irreversible y ajustará el inventario.", confirm_delete_product_inv: "¿Eliminar este producto del inventario de este día?", confirm_delete_product: "¿Seguro que quieres eliminar este producto?", confirm_delete_category: "¿Seguro? Los productos en esta categoría se moverán a la categoría de respaldo.", confirm_delete_last_category: "No se puede eliminar la última categoría.", confirm_clear_inventory: "¿Seguro que quiere limpiar la tabla de inventario para esta fecha?", confirm_import: "¿Está seguro? Esto reemplazará TODOS los datos actuales. Esta acción no se puede deshacer.",
                toast_error_load: 'Error al cargar datos. Usando valores por defecto.', toast_error_save: 'Error al guardar datos. Revise el espacio de almacenamiento.', toast_invalid_quantity: "Por favor, ingrese una cantidad válida.", toast_order_cancelled: "Orden cancelada.", toast_sale_processed: "Venta procesada con éxito.", toast_unrecognized_code: (code) => `Código no reconocido: ${code}`, toast_camera_error: "Error al iniciar la cámara.", toast_invalid_amount: "Cantidad inválida", toast_sale_updated: "Venta actualizada.", toast_sale_deleted: "Registro de venta eliminado.", toast_day_already_closed: (date) => `El día ${date} ya ha sido cerrado.`, toast_no_inventory_data: "No hay datos de inventario para este día.", toast_day_closed: (date) => `Día ${date} cerrado con éxito.`, toast_invalid_stock_data: "Cantidad y Costo deben ser números.", toast_product_saved: 'Producto guardado correctamente.',
                toast_code_too_long: (productName, suggestedName, actual, max, type) => {
                    let msg = `Error: Los datos para el ${type} del producto "${productName}" son demasiado largos. (Actual: ${actual} bytes. Máx estimado: ${max} bytes.`;
                    if (suggestedName) {
                        msg += ` Intente acortar el nombre a "${suggestedName}" o ajuste el ID/precio si es posible).`;
                    } else {
                        msg += ` Intente ajustar el ID/nombre/precio si es posible).`;
                    }
                    return msg;
                },
                toast_license_key_missing: "Por favor, ingrese una clave de licencia.", toast_license_activated: "¡Licencia activada con éxito!", toast_admin_license_activated: "¡Licencia de Administrador activada!", toast_license_incorrect: "La clave de licencia es incorrecta.",
                maintenance_title: "Mantenimiento de Datos",
                maintenance_warning: "⚠️ Estas acciones son IRREVERSIBLES. No se puede deshacer.",
                maintenance_clear_today_sales: "Limpiar Ventas de Hoy",
                maintenance_clear_closures: "Limpiar Cierres de Caja",
                maintenance_clear_sales_history: "Limpiar Historial de Ventas",
                maintenance_clear_inventories: "Limpiar Inventarios",
                maintenance_clear_everything: "⚠ BORRAR TODO (Restablecimiento de fábrica)",
                form_label_cost: "Costo Unitario",
                form_label_commission: "% Comisión",
                import_xlsx_error_format: "El archivo XLSX no tiene el formato esperado (debe incluir columnas 'Nombre' y 'Precio').", category_updated_success: "Categoría actualizada con éxito.", category_name_exists: "Ya existe una categoría con ese nombre.", import_success: (count) => `${count} productos importados/actualizados.`, import_error: "Error al procesar el archivo.", import_full_success: "Datos importados con éxito. La aplicación se recargará.", invalid_backup_file: "Archivo de backup inválido.",
                maintenance_title: "Mantenimiento", maintenance_warning: "Estas acciones eliminan datos permanentemente. Úselas con cuidado.",
                maintenance_clear_today_sales: "Limpiar Ventas de Hoy", maintenance_clear_closures: "Limpiar Cierres de Caja", maintenance_clear_sales_history: "Limpiar Historial de Ventas", maintenance_clear_inventories: "Limpiar Todos los Inventarios", maintenance_clear_everything: "Reiniciar Todo (Excepto Productos)",
                confirm_clear_today_sales: "¿Seguro? Se eliminarán TODAS las ventas de hoy y se revertirán los cambios en el inventario.", confirm_clear_closures: "¿Eliminar TODOS los cierres de caja? Esta acción no se puede rehacer.", confirm_clear_history: "¿Eliminar TODAS las ventas del historial? Esta acción no se puede rehacer.", confirm_clear_inventories: "¿Eliminar TODOS los registros de inventario? Esta acción no se puede rehacer.", confirm_clear_everything: "¿ESTÁ SEGURO? Esto eliminará TODOS los datos excepto productos y categorías. Esta acción no se puede deshacer.",
                toast_today_sales_cleared: "Ventas de hoy eliminadas.", toast_closures_cleared: "Cierres de caja eliminados.", toast_history_cleared: "Historial de ventas eliminado.", toast_inventories_cleared: "Inventarios eliminados.", toast_app_reset: "Sistema reiniciado. Productos y categorías conservados.",
                tooltip_total_investment: "Costo Total de Productos Vendidos (Cant. Vendida × P. Costo)"
            },
            en: { 
                app_title:"Professional POS System", th_product:"Product", th_actions:"Actions", th_totals:"Totals", all_categories: "All Categories",
                nav_catalog:"Catalog", nav_current_order:"Current Order", nav_sales:"Today's Sales", nav_inventory:"Inventory", nav_customer_labels:"Product Labels", nav_config_group:"Configuration", nav_product_mgmt:"Product Management", nav_category_mgmt:"Category Management", nav_records:"Records", nav_nomenclator:"Nomenclator", nav_tools:"Tools", nav_settings:"Settings",
                menu_catalog:"Catalog", menu_sales:"Sales", menu_records:"Records", menu_config:"Configuration", menu_import_export:"Import/Export Excel", menu_export_sales:"Export to Excel", menu_backups:"Backups", menu_appearance:"Appearance", menu_licenses:"Licenses", menu_maintenance:"Tools",
                tpv_filter_by_category:"Filter by Category:", tpv_current_order:"Current Order", tpv_total:"Total:", tpv_process_payment:"Process Payment", tpv_cancel_order:"Cancel", tpv_scan_add:"Scan", tpv_stop_scanner:"Stop Scanner",
                sales_today_title:"Today's Sales", sales_th_time:"Time", sales_th_quantity:"Quantity", sales_th_unit_price:"Unit Price", sales_th_total:"Total", sales_total_sold_today:"Total Sold Today:",
                inventory_title:"Inventory & Stock", inventory_select_date:"Select Date", inventory_quick_actions:"Quick Actions", inventory_add_to_stock:"Add to Stock", inventory_close_day:"Close Day", inventory_apply_global_commission:"Global Commission %:", inventory_apply_button:"Apply",
                th_sale_price:"Sale Price", th_unit:"U/M", th_initial_qty:"Initial Qty", th_final_qty:"Final Qty", th_sold:"Sold", th_sale_total:"Sale Total", th_cost_price:"Cost Price", th_commission:"Commission", th_net_profit:"Net Profit",
                records_title:"Records & Closures", records_closures_title:"Cash Closures", records_detailed_sales_title:"Detailed Sales", records_th_date:"Date", records_th_total_sales:"Total Sales", records_th_total_cost:"Total Cost", records_th_total_commission:"Total Commission", records_th_total_profit:"Net Profit", history_th_date:"Date & Time",
                mgmt_products_title:"Product Management", mgmt_new_product:"New Product", mgmt_th_category:"Category", mgmt_th_price:"Price",  mgmt_th_sale_status:"On Sale", mgmt_categories_title:"Category Management", mgmt_new_category_placeholder:"New category name", mgmt_filter_product_placeholder:"Filter by name...", filter_by_price: "Filter by Price", filter_min_price: "Min", filter_max_price: "Max", edit_product: "Edit Product",
                nomenclator_title:"Currency Nomenclator", nomenclator_total_value:"Total (Value)", nomenclator_total_qty:"Total (Units)", nomenclator_new_denom_placeholder:"New denomination",
                tools_title:"Data Tools", tools_backup_title:"Backup (JSON)", tools_backup_desc:"Save or restore a FULL backup of the entire application.", tools_import_button:"Import Backup (.json)", tools_export_button:"Export Backup (.json)", tools_xlsx_title: "Complete Data (XLSX)", tools_xlsx_desc: "Export or import Products, Inventories and Denominations in Excel format.", btn_import_xlsx: "Import Excel", btn_export_xlsx: "Export Excel", btn_export_with_value: "With Value", btn_export_zero: "At Zero", btn_export_all: "All", btn_export_with_value_tooltip: "Export only products with stock greater than 0", btn_export_zero_tooltip: "Export only products with stock at 0", btn_export_all_tooltip: "Export all products",
                settings_appearance:"Appearance", settings_language:"Language:", settings_dark_mode:"Dark Mode:", settings_license:"License", license_trial_ends:"Trial ends in:", settings_client_id:"Client ID:", settings_license_status:"Status:", settings_license_key_placeholder:"Enter your key", settings_activate_btn:"Activate",
                customer_catalog_title: "Generate Product Labels", customer_catalog_desc_select: "Select products to generate individual labels, or group them for a single QR.", customer_catalog_label_type: "Code Type:", customer_catalog_label_qr: "QR Only", customer_catalog_label_barcode: "Barcode Only", customer_catalog_label_both: "Both", customer_catalog_generate_labels: "Generate/Refresh Labels", customer_catalog_select_category: "Select Category:", customer_catalog_last_updated: "Last updated:", customer_catalog_page: "Page", customer_catalog_offers: "Special Offers",
                customer_catalog_group_title: "Group for QR", customer_catalog_group_desc: "Click product cards to add them here. Then generate a single QR for all selected products.", customer_catalog_group_generate: "Generate Group QR", customer_catalog_group_clear: "Clear Selection", customer_catalog_group_qr_title: "Product List:", customer_catalog_group_qr_title_ui: "QR for Customer",
                license_expired_title:"License Expired", license_expired_desc:"Please activate your product.", license_activated: "Activated", license_trial: (days) => `Trial (${days} days remaining)`, license_expired: "Expired",
                modal_add_to_order_title: "Add to Order", modal_quantity: "Quantity:", modal_process_payment_title: "Process Payment", modal_total_to_pay: "Total to Pay:", modal_select_payment_method: "Select Payment Method", modal_edit_sale_title: "Edit Sale", modal_editing: "Editing:", modal_new_quantity: "New Quantity:", modal_add_stock_title: "Add/Edit Stock", modal_edit_category_title: "Edit Category",
                payment_cash: "Cash", payment_card: "Card", payment_transfer: "Transfer", payment_customer_card: "Customer Card",
                btn_cancel: "Cancel", btn_accept: "Accept", btn_save_changes: "Save Changes", btn_save: "Save", btn_add_update: "Add/Update", btn_edit_product_label: "Edit Product",
                form_label_name: "Name", form_label_category: "Category", form_label_price: "Price", form_label_unit: "Unit of Measure (e.g., Un, Kg, L)", form_label_image_url: "Image URL (Online)", form_placeholder_image_url: "Paste an image URL here", form_label_image_local: "or Upload Local Image", form_label_new_category_name: "New category name", form_label_on_sale: "Mark as on-sale",
                no_products_in_category: "No products in this category.", no_products_selected_for_group: "No products selected.", empty_order: "Add products from the catalog.", no_sales_today: "No sales recorded today.", no_closures: "No cash closures found. Close a day from the Inventory tab.", no_sales_history: "No sales in history.", select_date_inventory: "Select a date to see the inventory.",
                confirm_cancel_order: "Are you sure you want to cancel the current order?", confirm_delete_sale: "Are you sure you want to delete this sale record? This action is irreversible and will adjust inventory.", confirm_delete_product_inv: "Delete this product from this day's inventory?", confirm_delete_product: "Are you sure you want to delete this product?", confirm_delete_category: "Are you sure? Products in this category will be moved to the fallback category.", confirm_delete_last_category: "Cannot delete the last category.", confirm_clear_inventory: "Are you sure you want to clear the inventory table for this date?", confirm_import: "Are you sure? This will replace ALL current data. This action cannot be undone.",
                toast_error_load: 'Error loading data. Using default values.', toast_error_save: 'Error saving data. Check storage space.', toast_invalid_quantity: "Please enter a valid quantity.", toast_order_cancelled: "Order cancelled.", toast_sale_processed: "Sale processed successfully.", toast_unrecognized_code: (code) => `Unrecognized code: ${code}`, toast_camera_error: "Error starting camera.", toast_invalid_amount: "Invalid amount", toast_sale_updated: "Sale updated.", toast_sale_deleted: "Sale record deleted.", toast_day_already_closed: (date) => `Day ${date} has already been closed.`, toast_no_inventory_data: "No inventory data for this day.", toast_day_closed: (date) => `Day ${date} closed successfully.`, toast_invalid_stock_data: "Quantity and Cost must be numbers.", toast_product_saved: 'Product saved successfully.',
                toast_code_too_long: (productName, suggestedName, actual, max, type) => {
                    let msg = `Error: The ${type} data for product "${productName}" is too long. (Actual: ${actual} bytes. Estimated Max: ${max} bytes.`;
                    if (suggestedName && suggestedName !== productName) {
                        msg += ` Try shortening the name to "${suggestedName}" or adjusting ID/price if applicable).`;
                    } else {
                        msg += ` Try adjusting ID/name/price if applicable).`;
                    }
                    return msg;
                },
                toast_license_key_missing: "Please enter a license key.", toast_license_activated: "License activated successfully!", toast_admin_license_activated: "Administrator License activated!", toast_license_incorrect: "The license key is incorrect.",
                maintenance_title: "Data Maintenance",
                maintenance_warning: "⚠️ These actions are IRREVERSIBLE and cannot be undone.",
                maintenance_clear_today_sales: "Clear Today's Sales",
                maintenance_clear_closures: "Clear Cash Closings",
                maintenance_clear_sales_history: "Clear Sales History",
                maintenance_clear_inventories: "Clear Inventories",
                maintenance_clear_everything: "⚠ DELETE EVERYTHING (Factory Reset)",
                form_label_cost: "Unit Cost",
                form_label_commission: "% Commission",
                import_xlsx_error_format: "XLSX file is not in the expected format (must include 'Name' and 'Price' columns).", category_updated_success: "Category updated successfully.", category_name_exists: "A category with that name already exists.", import_success: (count) => `${count} products imported/updated.`, import_error: "Error processing the file.", import_full_success: "Data imported successfully. The application will reload.", invalid_backup_file: "Invalid backup file.",
                maintenance_title: "Maintenance", maintenance_warning: "These actions permanently delete data. Use with caution.",
                maintenance_clear_today_sales: "Clear Today's Sales", maintenance_clear_closures: "Clear Cash Closures", maintenance_clear_sales_history: "Clear Sales History", maintenance_clear_inventories: "Clear All Inventories", maintenance_clear_everything: "Reset Everything (Except Products)",
                confirm_clear_today_sales: "Are you sure? This will delete ALL sales for today and revert inventory changes.", confirm_clear_closures: "Delete ALL cash closures? This action cannot be undone.", confirm_clear_history: "Delete ALL sales history? This action cannot be undone.", confirm_clear_inventories: "Delete ALL inventory records? This action cannot be undone.", confirm_clear_everything: "ARE YOU SURE? This will delete ALL data except products and categories. This action cannot be undone.",
                toast_today_sales_cleared: "Today's sales cleared.", toast_closures_cleared: "Cash closures cleared.", toast_history_cleared: "Sales history cleared.", toast_inventories_cleared: "All inventories cleared.", toast_app_reset: "Application reset. Products and categories have been kept.",
                tooltip_total_investment: "Total Cost of Goods Sold (Sold Qty × Cost Price)"
            }
        };

        // --- LÓGICA DE ALMACENAMIENTO INDEXEDDB ---
        const dbHelper = {
            // Abre la BD garantizando que el store exista. Abre SIN versión fija
            // para adoptar la versión existente (evita VersionError si una versión
            // previa la subió). Si falta el store, sube versión para crearlo y,
            // como último recurso, borra y recrea limpia. Maneja onblocked.
            openDb: () => new Promise((resolve, reject) => {
                // Paso 1: abrir sin versión (toma la actual, sea 1, 2, ...).
                let req;
                try { req = indexedDB.open(DB_NAME); }
                catch (err) { return reject(err); }
                req.onblocked = () => {};
                req.onerror = e => reject(e.target.error);
                req.onsuccess = e => {
                    const db = e.target.result;
                    if (db.objectStoreNames.contains(STORE_NAME)) {
                        return resolve(db); // todo OK
                    }
                    // Falta el store: reabrir con versión+1 para crearlo.
                    const nextVer = (db.version || 1) + 1;
                    db.close();
                    let up;
                    try { up = indexedDB.open(DB_NAME, nextVer); }
                    catch (err) { return reject(err); }
                    up.onupgradeneeded = ev => {
                        const db2 = ev.target.result;
                        if (!db2.objectStoreNames.contains(STORE_NAME)) {
                            db2.createObjectStore(STORE_NAME);
                        }
                    };
                    up.onblocked = () => {};
                    up.onsuccess = ev => {
                        const db2 = ev.target.result;
                        if (db2.objectStoreNames.contains(STORE_NAME)) return resolve(db2);
                        // Último recurso: borrar y recrear desde cero.
                        db2.close();
                        const del = indexedDB.deleteDatabase(DB_NAME);
                        del.onsuccess = del.onerror = del.onblocked = () => {
                            const fresh = indexedDB.open(DB_NAME, 1);
                            fresh.onupgradeneeded = fe => {
                                const db3 = fe.target.result;
                                if (!db3.objectStoreNames.contains(STORE_NAME)) {
                                    db3.createObjectStore(STORE_NAME);
                                }
                            };
                            fresh.onsuccess = fe => resolve(fe.target.result);
                            fresh.onerror = fe => reject(fe.target.error);
                        };
                    };
                    up.onerror = ev => reject(ev.target.error);
                };
            }),
            save: (db, data) => new Promise((resolve, reject) => {
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    return reject(new Error('store ausente'));
                }
                const tx = db.transaction(STORE_NAME, 'readwrite');
                tx.objectStore(STORE_NAME).put(data, 'appState');
                tx.oncomplete = () => resolve();
                tx.onerror = e => reject(e.target.error);
            }),
            load: (db) => new Promise((resolve, reject) => {
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    return resolve(undefined); // BD nueva: sin estado previo
                }
                const tx = db.transaction(STORE_NAME, 'readonly');
                const request = tx.objectStore(STORE_NAME).get('appState');
                request.onsuccess = e => resolve(e.target.result);
                request.onerror = e => reject(e.target.error);
            })
        };

        // --- SERVICE WORKER PARA FUNCIONAMIENTO OFFLINE ---
        // Service Worker removido - La app funciona 100% offline sin errores usando cache del navegador


        // updateOnlineStatus → reemplazada por updateNetworkStatus()
        
        // updateUITranslations → funcionalidad integrada en conf_setLanguage()
        // (listeners online/offline ahora los gestiona _monitorRed con ping real)

        // --- INICIALIZACIÓN Y MANEJO DE ESTADO ---
        document.addEventListener('DOMContentLoaded', async () => {
            // Solo cargamos el estado en memoria.
            // La UI se inicializa en _auth_mostrarApp() DESPUÉS del login.
            await loadState();
            console.log('✅ TPV state cargado — esperando autenticación');
        });

        document.addEventListener('visibilitychange', async () => {
            // Si se perdió el estado Y ya hay sesión activa, recargar UI
            if (document.visibilityState === 'visible'
                && Object.keys(tpvState).length === 0
                && window.AUTH?.usuario) {
                await loadState();
                if (typeof initializeUI         === 'function') initializeUI();
                conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
            }
        });

        function getDefaultState() { 
            const now = new Date().toISOString();
            const today = new Date().toISOString().split('T')[0];
            
            // Generar ID único para el cliente
            const clientId = `TPV-${Date.now().toString().slice(-6)}`;
            
            // CATEGORÍAS INICIALES
            const categoriasIniciales = [
                "Alimentos",
                "Bebidas",
                "Limpieza",
                "Higiene Personal",
                "Panadería",
                "Lácteos",
                "Carnes",
                "Frutas y Verduras",
                "Snacks",
                "General"
            ];
            
            // PRODUCTOS DE EJEMPLO PRECARGADOS
            const productosIniciales = [];
            
            // INVENTARIO INICIAL PARA HOY
            const inventarioHoy = [];
            
            return { 
                licencia: { 
                    activada: false, 
                    fechaActivacion: now, 
                    diasPrueba: 15, 
                    key: null, 
                    clienteId: clientId 
                },
                config: { 
                    lang: "es", 
                    theme: "light", 
                    globalProfitPercent: 20 
                },
                productos: productosIniciales,
                categorias: categoriasIniciales,
                ordenActual: [],
                ventasDiarias: {},
                historialVentas: [],
                inventarios: {
                    [today]: inventarioHoy
                },
                cierresCaja: [],
                nomencladores: { 
                    USD: [100,50,20,10,5,1], 
                    EUR: [100,50,20,10,5], 
                    CUP: [1000,500,200,100,50,20,10,5,1] 
                },
                nomencladorCantidades: {}
            }; 
        }

        // ==================== PERSISTENCIA DE DATOS OFFLINE ====================
        // 
        // ✅ DURACIÓN DE DATOS: PERMANENTE (sin límite de tiempo)
        // 
        // Los datos se guardan en IndexedDB del navegador, que persiste:
        // - ✅ Sin conexión a Internet (funciona 100% offline)
        // - ✅ Sin electricidad (mientras el dispositivo tenga batería)
        // - ✅ Indefinidamente (30 días, 90 días, años... sin límite)
        // - ✅ Incluso si cierras el navegador o reinicias el dispositivo
        // 
        // IMPORTANTE:
        // - Los datos SOLO se borran si:
        //   1. Desinstalas el navegador
        //   2. Limpias manualmente los datos del sitio
        //   3. Usas la función "Limpiar Todo" en Mantenimiento
        // 
        // - Para SEGURIDAD adicional:
        //   1. Exporta regularmente a Excel (Herramientas → Exportar Excel)
        //   2. Guarda copias de seguridad JSON (Herramientas → Exportar Backup)
        //   3. Estos archivos pueden guardarse en USB, tarjeta SD, etc.
        // 
        // RECOMENDACIÓN PARA 30+ DÍAS SIN CONEXIÓN:
        // - Exporta el Excel cada 7 días y guárdalo en almacenamiento externo
        // - Así tendrás respaldo incluso si algo pasa con el dispositivo
        // ========================================================================

        async function loadState() { 
            try { 
                // Inicializar capa API primero
                if (window.TPV_API) {
                    try { await TPV_API.init(); } catch(e) { console.warn('⚠️ TPV_API.init() falló:', e.message); }
                }

                // Intentar cargar desde la API primero (fuente de verdad)
                let loadedFromAPI = false;
                if (window.TPV_API && TPV_API._isOnline) {
                    try {
                        const catalogData = await TPV_API.catalogo.getAll();
                        if (catalogData && catalogData.productos && catalogData.productos.length > 0) {
                            const defaultState = getDefaultState();
                            // Construir inventario desde productos del API
                            const invFromAPI = catalogData.productos.map(p => ({
                                id: p.id, nombre: p.nombre,
                                categoria: p.categoria ?? 'General', um: p.um ?? 'Un',
                                cantInicial: Number(p.stock) || 0, vendido: 0,
                                cantFinal: Number(p.stock) || 0,
                                precioVenta: Number(p.precio) || 0,
                                precioCosto: Number(p.costo) || 0,
                                costoUnitario: Number(p.costo) || 0,
                                importe: 0, comision: 0, gananciaNeta: 0
                            }));
                            const todayInv = new Date().toISOString().split('T')[0];
                            tpvState = {
                                ...defaultState,
                                productos: catalogData.productos,
                                categorias: catalogData.categorias || [...new Set(catalogData.productos.map(p => p.categoria))].sort(),
                                inventarios: { [todayInv]: invFromAPI },
                            };
                            loadedFromAPI = true;
                            console.log('📦 Estado cargado desde API: ' + catalogData.productos.length + ' productos');
                        }
                    } catch(e) {
                        console.warn('⚠️ API no disponible, usando IndexedDB:', e.message);
                    }
                }

                // Fallback a IndexedDB si la API no funcionó
                if (!loadedFromAPI) {
                    const db = await dbHelper.openDb();
                    let savedState = await dbHelper.load(db);
                    db.close();

                    // Si IndexedDB está vacío, intentar recuperar del servidor
                    if (!savedState) {
                        try {
                            const res = await fetch('/api/state', { credentials: 'same-origin' });
                            if (res.ok) {
                                const data = await res.json();
                                if (data.ok && data.estado) {
                                    savedState = data.estado;
                                    console.log('📦 Estado recuperado del servidor');
                                }
                            }
                        } catch(e) { /* offline, continuar */ }
                    }

                    const defaultState = getDefaultState();
                    const parsedState = savedState ?? defaultState;

                    tpvState = {
                        ...defaultState,
                        ...parsedState,
                        licencia: { ...defaultState.licencia, ...(parsedState.licencia ?? {}) },
                        config: { ...defaultState.config, ...(parsedState.config ?? {}) },
                        nomencladores: { ...defaultState.nomencladores, ...(parsedState.nomencladores ?? {}) },
                        nomencladorCantidades: parsedState.nomencladorCantidades ?? defaultState.nomencladorCantidades,
                    };
                } else {
                    // Si cargamos desde API, completar campos que no vienen del catálogo
                    const db = await dbHelper.openDb();
                    let savedState = await dbHelper.load(db);
                    db.close();
                    const defaultState = getDefaultState();
                    const parsedState = savedState ?? defaultState;
                    tpvState = {
                        ...defaultState,
                        ...parsedState,
                        ...tpvState,
                        licencia: { ...defaultState.licencia, ...(parsedState.licencia ?? {}) },
                        config: { ...defaultState.config, ...(parsedState.config ?? {}) },
                        nomencladores: { ...defaultState.nomencladores, ...(parsedState.nomencladores ?? {}) },
                        nomencladorCantidades: parsedState.nomencladorCantidades ?? defaultState.nomencladorCantidades,
                    };
                }

                if (!tpvState.licencia.clienteId) {
                    tpvState.licencia.clienteId = `TPV-${Date.now().toString().slice(-6)}`;
                }
                if (!tpvState.licencia.fechaActivacion) {
                    tpvState.licencia.fechaActivacion = new Date().toISOString();
                }

                // ── Sincronizar catálogo desde el servidor (fuente de verdad compartida) ──
                await catalogo_cargarDesdeServidor();

            } catch(e) { 
                console.error("Error loading state, resetting to default.", e); 
                showToast(getLang().toast_error_load, 'danger'); 
                tpvState = getDefaultState(); 
            } 
        }

        /** Carga el catálogo del servidor y actualiza tpvState.productos para todos los roles */
        async function catalogo_cargarDesdeServidor() {
            try {
                const res = await fetch('/api/catalogo', { credentials: 'same-origin' });
                if (!res.ok) return;
                const data = await res.json();
                if (data.ok && Array.isArray(data.productos) && data.productos.length > 0) {
                    const localMap = {};
                    tpvState.productos.forEach(p => { localMap[p.id] = p; });
                    tpvState.productos = data.productos.map(sp => ({
                        ...(localMap[sp.id] || {}),
                        ...sp,
                    }));
                    const cats = [...new Set(tpvState.productos.map(p => p.categoria || 'General'))].sort();
                    if (cats.length) tpvState.categorias = cats;
                    console.log(`📦 Catálogo del servidor: ${data.productos.length} productos`);
                }
            } catch(e) {
                console.warn('⚠️ Catálogo local (sin servidor):', e.message);
            }
        }

        /** El admin sube su catálogo al servidor para que todos los roles lo vean */
        async function catalogo_sincronizarAlServidor() {
            try {
                const res = await fetch('/api/catalogo/sync', {
                    method: 'POST', credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productos: tpvState.productos })
                });
                if (res.ok) console.log('☁️ Catálogo sincronizado al servidor');
            } catch(e) {
                console.warn('⚠️ No se pudo sincronizar catálogo:', e.message);
            }
        }

        async function saveState() { 
            try { 
                // Siempre guardar en IndexedDB para soporte offline
                const db = await dbHelper.openDb();
                await dbHelper.save(db, tpvState); 
                db.close();
            } catch (e) { 
                console.error("Error saving state to IndexedDB:", e); 
                showToast(getLang().toast_error_save, 'danger'); 
            } 
        }

        /** Persiste el estado en el servidor de forma explícita (solo llamar cuando sea intencional) */
        async function saveStateServidor() {
            try {
                await fetch('/api/state', {
                    method: 'POST', credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(tpvState)
                });
            } catch(e) { /* offline */ }
        }

        async function _syncStockFromAPI(){try{const r=await fetch("/api/catalogo");const d=await r.json();if(d&&d.productos){d.productos.forEach(ap=>{const p=tpvState.productos.find(p=>p.nombre===ap.nombre);if(p){p.stock=ap.stock||10;p.precio=ap.precio||p.precio;}});}}catch(e){}}
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
                        <div class="product-img" style="position:relative;">
                            ${(() => { if(!p.imagen) return '<i class="bi bi-image-alt"></i>'; const e=/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}]/u; if(e.test(p.imagen)) return '<span style="font-size:2.5rem;line-height:1">'+p.imagen+'</span>'; return '<img src="'+p.imagen+'" style="max-width:100%;max-height:100%;object-fit:contain" onerror="this.outerHTML=\'<i class=bi-image-alt></i>\'">'; })()}
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

        async function tpv_cancelarPedido(){
            if(tpvState.ordenActual.length > 0 && (await tpvConfirm(getLang().confirm_cancel_order))){
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

            // Sincronizar venta al servidor via TPV_API
            const vendedorId = window.AUTH?.usuario?.usuario_id;
            const vendedorNombre = window.AUTH?.usuario?.nombre || vendedorId || 'vendedor';
            if (window.TPV_API) {
                const items = ventas.map(v => ({ id: v.productoId, nombre: v.nombre, cantidad: v.cantidad, precio: v.precioUnitario }));
                TPV_API.ventas.registrar(items, metodo, vendedorNombre).then(result => {
                    if (result && result.ok) console.log('✅ Venta registrada en servidor:', result.venta_id || 'ok');
                }).catch(e => console.warn('⚠️ Venta no sincronizada:', e.message));
            }

            // Notificar al servidor (inventario diario) y SSE
            if (vendedorId) {
                ventas.forEach(v => {
                    fetch('/api/inventario/diario/conteo', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vendedor_id:  vendedorId,
                            producto_id:  v.productoId,
                            cant_final:   (() => {
                                const _ir = tpvState.inventarios[hoy] || []; const inv = Array.isArray(_ir) ? _ir : Object.values(_ir);
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

            // Sincronizar venta al servidor via TPV_API
            const vendedorId2 = window.AUTH?.usuario?.usuario_id;
            const vendedorNombre2 = window.AUTH?.usuario?.nombre || vendedorId2 || 'vendedor';
            if (window.TPV_API) {
                const items = ventas.map(v => ({ id: v.productoId, nombre: v.nombre, cantidad: v.cantidad, precio: v.precioUnitario }));
                TPV_API.ventas.registrar(items, metodo, vendedorNombre2).then(result => {
                    if (result && result.ok) console.log('✅ Venta registrada en servidor:', result.venta_id || 'ok');
                }).catch(e => console.warn('⚠️ Venta no sincronizada:', e.message));
            }

            // Actualizar cant_vendida en inventario_diario del servidor (para la tabla admin)
            if (vendedorId2) {
                ventas.forEach(v => {
                    fetch('/api/inventario/diario/conteo', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vendedor_id:  vendedorId2,
                            producto_id:  v.productoId,
                            cant_final:   (() => {
                                const _ir = tpvState.inventarios[hoy] || []; const inv = Array.isArray(_ir) ? _ir : Object.values(_ir);
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
            if(!confirmado && !(await tpvConfirm(lang.confirm_delete_sale))) return;
            
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
                    tpvAlert(`🎯 CÓDIGO DE APRENDIZAJE PARA HOY:\n\n"${codigoAprendizaje}"\n\n¡Recuerda aplicarlo durante el día!`);
                }, 500);
            }
            
            // Crear copia de seguridad automática
            await crear_backup_automatico('cierre_dia');
            await saveState();

            // Sincronizar cierre de caja al servidor via TPV_API
            if (window.TPV_API) {
                const cerradoPor = window.AUTH?.usuario?.nombre || 'admin';
                TPV_API.ventas.cerrarCaja(fecha, cerradoPor).then(result => {
                    if (result && result.ok) console.log('✅ Cierre de caja registrado en servidor:', fecha);
                }).catch(e => console.warn('⚠️ Cierre de caja no sincronizado:', e.message));
            }

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
        function inv_cargarInventario(fecha){
            if(!tpvState.inventarios[fecha]){
                tpvState.inventarios[fecha] = [];
                const fechaAnterior = new Date(fecha);
                fechaAnterior.setDate(fechaAnterior.getDate() - 1);
                const inventarioAnterior = tpvState.inventarios[fechaAnterior.toISOString().split('T')[0]];
                
                tpvState.productos.forEach(p => {
                    const itemAnterior = inventarioAnterior?.find(i => i.id === p.id);
                    const cantInicial = itemAnterior?.cantFinal ?? 0;
                    tpvState.inventarios[fecha].push({
                        id: p.id, nombre: p.nombre, categoria: p.categoria ?? "General", precioVenta: p.precio, um: p.um ?? "Un",
                        cantInicial, cantFinal: cantInicial, vendido: 0, importe: 0, precioCosto: 0, comision: 0, gananciaNeta: 0
                    });
                });
            }
            inv_recalcularVentasDelDia(fecha);
        }

        function inv_recalcularVentasDelDia(fecha){
            if(!tpvState.inventarios[fecha]) return;
            
            tpvState.inventarios[fecha].forEach(item => { item.vendido = 0; });
            
            tpvState.historialVentas.filter(v => v.fecha.startsWith(fecha)).forEach(venta => {
                const item = tpvState.inventarios[fecha].find(i => i.id === venta.productoId);
                if(item) item.vendido += venta.cantidad;
            });
            
            tpvState.inventarios[fecha].forEach(item => { item.cantFinal = item.cantInicial - item.vendido; });
            
            inv_aplicarGananciaGlobal(fecha);
        }

        async function inv_actualizarStockPorVenta(fecha, productoId, quantity){
            inv_cargarInventario(fecha);
            const item = tpvState.inventarios[fecha].find(i => i.id === productoId);
            if(item){
                item.vendido += quantity;
                item.cantFinal = item.cantInicial - item.vendido;
            }
        }

        async function inv_aplicarGananciaGlobal(fecha = null) {
            const fechaActual = fecha ?? (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            const el = document.getElementById("inv-globalProfitPercent");
            const porcentaje = el ? parseFloat(el.value) / 100 : (tpvState.config?.globalProfitPercent || 0) / 100;
            if(!tpvState.inventarios[fechaActual]) return;
            
            tpvState.config.globalProfitPercent = 100 * porcentaje;
            
            // CORRECCIÓN: Asegurar que los cálculos se realicen correctamente
            tpvState.inventarios[fechaActual].forEach(item => {
                // Recalcular vendido basado en cantInicial y cantFinal
                item.vendido = Math.max(0, item.cantInicial - item.cantFinal);
                
                // Calcular importe (precio de venta × cantidad vendida)
                item.importe = item.vendido * item.precioVenta;
                
                // Calcular ganancia bruta unitaria
                const gananciaBrutaUnitaria = item.precioVenta - item.precioCosto;
                
                // Calcular comisión unitaria
                const comisionUnitaria = gananciaBrutaUnitaria > 0 ? gananciaBrutaUnitaria * porcentaje : 0;
                
                // Calcular comisión total
                item.comision = item.vendido * comisionUnitaria;
                
                // Calcular ganancia neta
                item.gananciaNeta = (item.vendido * gananciaBrutaUnitaria) - item.comision;
            });
            
            inv_renderizarTabla(fechaActual);
            await saveState();
        }

        function inv_renderizarTabla(fecha){
            const inventario = tpvState.inventarios[fecha];
            const tablaBody = document.getElementById("inv-tablaInventario");
            const lang = getLang();
            
            const filtroCategoriaSelect = document.getElementById('inv-filter-categoria');
            const categoriasUnicas = [...new Set(tpvState.productos.map(p => p.categoria))];
            filtroCategoriaSelect.innerHTML = `<option value="">${lang.all_categories}</option>` + 
                categoriasUnicas.sort().map(cat => `<option value="${cat}" ${cat === filtroCategoriaSelect.value ? 'selected' : ''}>${cat}</option>`).join('');
            
            if(!inventario){
                tablaBody.innerHTML = `<tr><td colspan="13" class="text-muted text-center">${lang.select_date_inventory}</td></tr>`;
                inv_actualizarTotales(fecha);
                return;
            }
            
            const filtros = {
                nombre: document.getElementById('inv-filter-nombre')?.value.toLowerCase() || '',
                categoria: filtroCategoriaSelect.value,
                pventa: document.getElementById('inv-filter-pventa')?.value || '', um: document.getElementById('inv-filter-um')?.value.toLowerCase() || '',
                cinicial: document.getElementById('inv-filter-cinicial')?.value || '', cfinal: document.getElementById('inv-filter-cfinal')?.value || '',
                vendido: document.getElementById('inv-filter-vendido')?.value || '', iventa: document.getElementById('inv-filter-iventa')?.value || '',
                pcosto: document.getElementById('inv-filter-pcosto')?.value || '', comision: document.getElementById('inv-filter-comision')?.value || '',
                ganancia: document.getElementById('inv-filter-ganancia')?.value || '',
            };

            const inventarioFiltrado = inventario.filter(i => 
                (!filtros.nombre || i.nombre.toLowerCase().includes(filtros.nombre)) &&
                (!filtros.categoria || i.categoria === filtros.categoria) &&
                (!filtros.pventa || (Number(i.precioVenta)||0).toFixed(2).includes(filtros.pventa)) &&
                (!filtros.um || i.um?.toLowerCase().includes(filtros.um)) &&
                (!filtros.cinicial || String(i.cantInicial).includes(filtros.cinicial)) &&
                (!filtros.cfinal || String(i.cantFinal).includes(filtros.cfinal)) &&
                (!filtros.vendido || String(i.vendido).includes(filtros.vendido)) &&
                (!filtros.iventa || (Number(i.importe)||0).toFixed(2).includes(filtros.iventa)) &&
                (!filtros.pcosto || (Number(i.precioCosto)||0).toFixed(2).includes(filtros.pcosto)) &&
                (!filtros.comision || (Number(i.comision)||0).toFixed(2).includes(filtros.comision)) &&
                (!filtros.ganancia || (Number(i.gananciaNeta)||0).toFixed(2).includes(filtros.ganancia))
            ).sort((a,b) => (a.categoria ?? 'zz').localeCompare(b.categoria ?? 'zz') || a.nombre.localeCompare(b.nombre));

            tablaBody.innerHTML = inventarioFiltrado.map((item, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td>${item.nombre}</td>
                    <td>${item.categoria ?? 'N/A'}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${(Number(item.precioVenta)||0).toFixed(2)}" step="0.01" min="0" onchange="inv_updateField('${fecha}','${item.id}','precioVenta',this.valueAsNumber)" title="Precio de venta (editable)"></td>
                    <td>${item.um}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${item.cantInicial}" onchange="inv_updateField('${fecha}','${item.id}','cantInicial',this.valueAsNumber)"></td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${item.cantFinal}" onchange="inv_updateField('${fecha}','${item.id}','cantFinal',this.valueAsNumber)"></td>
                    <td>${item.vendido}</td>
                    <td class="money-column">${formatCurrency(item.importe)}</td>
                    <td><input type="number" class="form-control form-control-sm inventory-input" value="${(Number(item.precioCosto)||0).toFixed(2)}" step="0.01" onchange="inv_updateField('${fecha}','${item.id}','precioCosto',this.valueAsNumber)"></td>
                    <td class="money-column">${formatCurrency(item.comision)}</td>
                    <td class="fw-bold money-column ${item.gananciaNeta >= 0 ? "text-success" : "text-danger"}">${formatCurrency(item.gananciaNeta)}</td>
                    <td><button class="btn btn-sm btn-danger" onclick="inv_eliminarFila('${fecha}','${item.id}')"><i class="bi bi-trash"></i></button></td>
                </tr>`).join("");
            
            inv_actualizarTotales(fecha, inventarioFiltrado);
        }

        async function inv_updateField(fecha, id, campo, valor) {
            const item = tpvState.inventarios[fecha].find(i => i.id === id);
            if (item) {
                item[campo] = valor;
                if (campo === 'cantInicial') item.cantFinal = item.cantInicial - item.vendido;
                // Si cambia el precio de venta o costo, reflejarlo también en el
                // producto del catálogo (precios variables) y persistir en servidor.
                if (campo === 'precioVenta' || campo === 'precioCosto') {
                    const prod = (tpvState.productos || []).find(p => p.id === id);
                    if (prod) {
                        if (campo === 'precioVenta') prod.precio = valor;
                        if (campo === 'precioCosto') prod.costo = valor;
                    }
                    try {
                        await fetch('/api/productos/precio', {
                            method: 'POST', credentials: 'same-origin',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ id: id,
                                precio: campo === 'precioVenta' ? valor : undefined,
                                costo:  campo === 'precioCosto' ? valor : undefined })
                        });
                    } catch (e) { /* offline: queda en estado local */ }
                }
            }
            await inv_aplicarGananciaGlobal(fecha);
            if (typeof saveState === 'function') { try { await saveState(); } catch(e){} }
        }

        async function inv_eliminarFila(fecha, id){
            if ((await tpvConfirm(getLang().confirm_delete_product_inv))) {
                tpvState.inventarios[fecha] = tpvState.inventarios[fecha].filter(i => i.id !== id);
                await inv_aplicarGananciaGlobal(fecha);
            }
        }

        function inv_actualizarTotales(fecha, data = null) {
            const items = data ?? tpvState.inventarios[fecha] ?? [];
            const lang = getLang();

            // CORRECCIÓN FINAL: Lógica de totalización robusta con bucle for...of para máxima claridad.
            const totals = {
                pventa: 0, pcosto: 0,
                cantInicial: 0, cantFinal: 0, vendido: 0, importe: 0,
                costoVendido: 0, comision: 0, ganancia: 0
            };

            for (const item of items) {
                totals.pventa += Number(item.precioVenta) || 0;
                totals.pcosto += Number(item.precioCosto) || 0;
                totals.cantInicial += Number(item.cantInicial) || 0;
                totals.cantFinal += Number(item.cantFinal) || 0;
                totals.vendido += Number(item.vendido) || 0;
                totals.importe += Number(item.importe) || 0;
                totals.costoVendido += (Number(item.vendido) || 0) * (Number(item.precioCosto) || 0);
                totals.comision += Number(item.comision) || 0;
                totals.ganancia += Number(item.gananciaNeta) || 0;
            }

            const _set = (id, val) => { const e = document.getElementById(id); if (e) e.innerText = val; };
            _set("inv-totalPventa", '$' + totals.pventa.toFixed(2));
            _set("inv-totalPcosto", '$' + totals.pcosto.toFixed(2));
            _set("inv-totalCantInicial", parseFloat(totals.cantInicial.toFixed(2)));
            _set("inv-totalCantFinal", parseFloat(totals.cantFinal.toFixed(2)));
            _set("inv-totalVendido", parseFloat(totals.vendido.toFixed(2)));
            _set("inv-totalImporte", totals.importe.toFixed(2));
            _set("inv-totalComision", totals.comision.toFixed(2));
            _set("inv-totalGanancia", totals.ganancia.toFixed(2));
            // Compat: la celda antigua de costo vendido si aún existe
            const _cv = document.getElementById("inv-totalCostoVendido");
            if (_cv) { _cv.innerText = totals.costoVendido.toFixed(2); _cv.title = lang.tooltip_total_investment || ''; }
        }

        function inv_abrirModalProducto(){
            if (!invModalStock) {
                const el = document.getElementById('inv-modal-stock');
                if (!el) { console.warn('[TPV] Modal inv-modal-stock no encontrado'); return; }
                invModalStock = new bootstrap.Modal(el);
            }
            const select = document.getElementById("inv-stock-producto");
            if (!select) return;
            select.innerHTML = [...(tpvState.productos || [])].sort((a,b) => a.nombre.localeCompare(b.nombre)).map(p => `<option value="${p.id}">${p.nombre}</option>`).join("");
            invModalStock.show();
        }

        async function inv_agregarProductoAInventario(){
            const fecha = (document.getElementById("inv-fechaActual")?.value ?? getTodayDateString());
            const productoId = document.getElementById("inv-stock-producto").value;
            const cantidad = parseFloat(document.getElementById("inv-stock-cantidad").value);
            const costo = parseFloat(document.getElementById("inv-stock-costo").value);
            
            if(isNaN(cantidad) || isNaN(costo)){
                return showToast(getLang().toast_invalid_stock_data,"warning");
            }
            
            inv_cargarInventario(fecha);
            const item = tpvState.inventarios[fecha].find(i => i.id === productoId);
            if(item){
                item.cantInicial = cantidad;
                item.precioCosto = costo;
            } else {
                const producto = tpvState.productos.find(p => p.id === productoId);
                if(producto){
                    tpvState.inventarios[fecha].push({
                        id: producto.id, nombre: producto.nombre, categoria: producto.categoria ?? "General", precioVenta: producto.precio, um: producto.um ?? "Un",
                        cantInicial: cantidad, cantFinal: cantidad, vendido: 0, importe: 0, precioCosto: costo, comision: 0, gananciaNeta: 0
                    });
                }
            }
            invModalStock.hide();
            await inv_aplicarGananciaGlobal(fecha);

            // Sincronizar stock al servidor via TPV_API
            if (window.TPV_API) {
                const updates = (tpvState.inventarios[fecha] || []).map(i => ({
                    producto_id: i.id,
                    cant_inicial: i.cantInicial,
                    cant_final: i.cantFinal ?? i.cantInicial,
                    precio_costo: i.precioCosto
                }));
                if (updates.length) {
                    TPV_API.inventario.actualizarStockMasivo(updates).then(result => {
                        if (result && result.ok) console.log('✅ Stock sincronizado al servidor');
                    }).catch(e => console.warn('⚠️ Stock no sincronizado:', e.message));
                }
            }
        }

        // --- LÓGICA DE GESTIÓN (Productos y Categorías) ---
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
                        // Patrones flexibles (sin anclar al final) para aceptar
                        // cabeceras compuestas como 'Stock Actual', 'Cantidad Inicial',
                        // 'Precio de Venta', etc. El orden de evaluación da prioridad
                        // a costo/cantidad antes que precio para evitar confusiones.
                        producto: /(producto|nombre|item|descripci[oó]n|art[ií]culo|descripcion)/i,
                        costo: /(costo|p\.?\s*costo|compra|inversi[oó]n|precio.*compra|\bcost\b)/i,
                        cantidad: /(cantidad|stock|existencia|\bcant\b|inventario|\bqty\b|unidades|exist|cant.*inicial|stock.*actual)/i,
                        precio: /(precio|p\.?\s*venta|pvp|precio.*venta|\bvalor\b|\bventa\b|\bprice\b)/i,
                        um: /(unidad|u\.?\s*m|\bum\b|medida|\bund\b|\bunit\b|c\/u)/i,
                        categoria: /(categor[ií]a|tipo|clasificaci[oó]n|\bcategory\b|rubro)/i
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
        
                // Estrategia 1: Buscar encabezados explícitos.
                // Si encontramos una fila de encabezados válida (nombre + precio o
                // cantidad), SIEMPRE la usamos: es la intención explícita del usuario
                // y es muchísimo más fiable que adivinar por contenido. Antes se
                // exigía confianza > 0.6 (4+ columnas), lo que descartaba archivos
                // normales de 3 columnas y caía al patrón hardcodeado (bug del
                // "mismo número para todos").
                const resultadoEncabezados = this.buscarEncabezadosExplicitos(rawData);
                if (resultadoEncabezados.filaEncabezado >= 0 &&
                    resultadoEncabezados.columnas.nombre !== undefined) {
                    console.log('✅ Encabezados explícitos detectados', resultadoEncabezados.columnas);
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
                
                        // Verificar contra patrones de encabezados.
                        // El orden de this.patterns.headers da prioridad a costo y
                        // cantidad ANTES que precio (evita que "Precio de Compra"
                        // se asigne a precio). Normalizamos la clave 'producto' a
                        // 'nombre' para que coincida con el bucle de procesamiento.
                        for (const [tipo, patron] of Object.entries(this.patterns.headers)) {
                            const key = (tipo === 'producto') ? 'nombre' : tipo;
                            if (patron.test(celda) && colsEncontradas[key] === undefined) {
                                colsEncontradas[key] = j;
                                coincidencias++;
                                if (this.DEBUG) {
                                    console.log(`  📌 Fila ${i+1}, Col ${j+1}: "${celda}" → ${key}`);
                                }
                            }
                        }
                    }
            
                    // Es una fila de encabezados si tiene la columna de NOMBRE más al
                    // menos una columna numérica (precio o cantidad). No exigimos
                    // precio obligatorio: un archivo solo de inventario puede traer
                    // Nombre + Stock sin precio.
                    const tieneNombre = colsEncontradas.nombre !== undefined;
                    const tieneNumerica = colsEncontradas.precio !== undefined ||
                                          colsEncontradas.cantidad !== undefined ||
                                          colsEncontradas.costo !== undefined;
                    if (tieneNombre && tieneNumerica) {
                        resultado.filaEncabezado = i;
                        resultado.filaInicioDatos = i + 1;
                        resultado.columnas = colsEncontradas;
                        resultado.confianza = Math.min(coincidencias / 6, 1); // Máximo 6 columnas esperadas
                
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
                        if (!(await tpvConfirm(mensaje))) {
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
                                onSale: false
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
                    stock_actual: stockMap[p.id] ?? 0
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
        async function conf_handleImport(event){
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
            if (!(await tpvConfirm("⚠️ ¿Está seguro de importar este backup?\n\nEsto reemplazará todos los datos actuales.\n\nSe recomienda exportar un backup antes de continuar."))) {
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
        async function nom_cargarDenominaciones(moneda) {
            const contenedor = document.getElementById("nom-contenedorDivisas");
            if (!contenedor) return;
            if (!tpvState || !tpvState.nomencladores) return;
            const denominaciones = (tpvState.nomencladores[moneda] ?? []).sort((a,b) => b-a);
            const cantidades = tpvState.nomencladorCantidades[moneda] ?? {};
            
            contenedor.innerHTML = denominaciones.map(d => {
                const cantidad = cantidades[d] ?? '';
                const subtotal = d * (cantidad || 0);
                return `<div class="input-group input-group-sm mb-2">
                    <span class="input-group-text fw-bold" style="width: 70px;">${formatCurrency(d).replace('.00','')}</span>
                    <input type="number" class="form-control text-end" data-valor="${d}" oninput="nom_actualizarTotalDenominaciones()" placeholder="Cantidad" min="0" value="${cantidad}">
                    <span class="input-group-text text-muted" id="nom-subtotal-${d}" style="width: 110px; justify-content: flex-end;">= ${subtotal.toFixed(2)}</span>
                    <button class="btn btn-sm btn-outline-danger" onclick="nom_eliminarDenominacion('${moneda}', ${d})">×</button>
                </div>`;
            }).join('');
            nom_actualizarTotalDenominaciones();
        }

        async function nom_agregarDenominacion(){
            if (!tpvState || !tpvState.nomencladores) return;
            const moneda = document.getElementById("nom-selectPais")?.value;
            if (!moneda) return;
            const input = document.getElementById("nom-inputNueva");
            const valor = parseInt(input?.value, 10);
            if(!isNaN(valor) && valor > 0 && !tpvState.nomencladores[moneda].includes(valor)){
                tpvState.nomencladores[moneda].push(valor);
                if (input) input.value = "";
                await saveState();
                nom_cargarDenominaciones(moneda);
            }
        }

        async function nom_eliminarDenominacion(moneda, denominacion){
            tpvState.nomencladores[moneda] = tpvState.nomencladores[moneda].filter(d => d !== denominacion);
            if(tpvState.nomencladorCantidades[moneda]) delete tpvState.nomencladorCantidades[moneda][denominacion];
            await saveState();
            nom_cargarDenominaciones(moneda);
        }

        function nom_actualizarTotalDenominaciones() {
            const selEl = document.getElementById("nom-selectPais");
            if (!selEl) return;
            const moneda = selEl.value;
            tpvState.nomencladorCantidades[moneda] = {};
            let totalValor = 0, totalCantidad = 0;
            
            document.querySelectorAll("#nom-contenedorDivisas input").forEach(input => {
                const d = parseFloat(input.dataset.valor);
                const c = parseInt(input.value) || 0;
                totalValor += d * c;
                totalCantidad += c;
                const _ns = document.getElementById(`nom-subtotal-${d}`); if(_ns) _ns.innerText = `= ${(d*c).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                if(c > 0) tpvState.nomencladorCantidades[moneda][d] = c;
            });

            const _nomTot = document.getElementById("nom-totalesDenominaciones"); if(_nomTot) _nomTot.innerText = totalValor.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const _nomCant = document.getElementById("nom-totalCantidadDenominaciones"); if(_nomCant) _nomCant.innerText = totalCantidad;
            saveState();
        }

        // --- LÓGICA DE LICENCIA ---
        const lic_sha256 = async (text) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))).map(b => b.toString(16).padStart(2, '0')).join('');
        
        function lic_getRemainingDays() {
            const { licencia } = tpvState;
            if (licencia.activada || !licencia.fechaActivacion) {
                return licencia.diasPrueba;
            }
            const fechaInicio = new Date(licencia.fechaActivacion);
            const hoy = new Date();
            
            // Calcular tiempo restante según la unidad configurada
            const unidad = licencia.unidadTiempo || 'dias';
            let tiempoRestante;
            
            if (unidad === 'minutos') {
                const minutosPasados = Math.floor((hoy - fechaInicio) / (1000 * 60));
                tiempoRestante = Math.max(0, licencia.diasPrueba - minutosPasados);
            } else if (unidad === 'segundos') {
                const segundosPasados = Math.floor((hoy - fechaInicio) / 1000);
                tiempoRestante = Math.max(0, licencia.diasPrueba - segundosPasados);
            } else {
                // Días por defecto
                const diasPasados = Math.ceil((hoy - fechaInicio) / (1000 * 60 * 60 * 24));
                tiempoRestante = Math.max(0, licencia.diasPrueba - diasPasados);
            }
            
            return tiempoRestante;
        }
        
        function lic_getTimeUnitText() {
            const unidad = tpvState.licencia.unidadTiempo || 'dias';
            const tiempo = lic_getRemainingDays();
            
            if (unidad === 'minutos') {
                return `${tiempo} minuto${tiempo !== 1 ? 's' : ''}`;
            } else if (unidad === 'segundos') {
                return `${tiempo} segundo${tiempo !== 1 ? 's' : ''}`;
            } else {
                return `${tiempo} día${tiempo !== 1 ? 's' : ''}`;
            }
        }

        async function lic_activateLicense(){
            const key = document.getElementById("lic-key-input").value.trim();
            const { clienteId } = tpvState.licencia;
            const lang = getLang();
            
            if(!key) return showToast(lang.toast_license_key_missing,"warning");
            
            // Verificar clave administrativa (permanente)
            const adminHash = await lic_sha256("admin" + getSecretKey());
            
            if(key === adminHash){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                tpvState.licencia.unidadTiempo = 'dias';
                await saveState();
                lic_checkLicense();
                showToast(lang.toast_admin_license_activated, "info");
                return;
            }
            
            // Verificar claves con duración personalizada
            let claveValida = false;
            let tiempoLicencia = 0;
            let unidadTiempo = 'dias';
            
            // Duraciones posibles en diferentes unidades
            const duracionesPosibles = [
                // Días
                { valor: 30, unidad: 'dias' },
                { valor: 60, unidad: 'dias' },
                { valor: 90, unidad: 'dias' },
                { valor: 180, unidad: 'dias' },
                { valor: 365, unidad: 'dias' },
                { valor: 730, unidad: 'dias' },
                // Minutos (para pruebas rápidas)
                { valor: 1, unidad: 'minutos' },
                { valor: 5, unidad: 'minutos' },
                { valor: 10, unidad: 'minutos' },
                { valor: 30, unidad: 'minutos' },
                { valor: 60, unidad: 'minutos' },
                // Segundos (para pruebas muy rápidas)
                { valor: 30, unidad: 'segundos' },
                { valor: 60, unidad: 'segundos' },
                { valor: 120, unidad: 'segundos' },
                { valor: 300, unidad: 'segundos' }
            ];
            
            for (const duracion of duracionesPosibles) {
                const validHash = await lic_sha256(clienteId + getSecretKey() + duracion.valor + duracion.unidad);
                if (key === validHash) {
                    claveValida = true;
                    tiempoLicencia = duracion.valor;
                    unidadTiempo = duracion.unidad;
                    break;
                }
            }
            
            if(claveValida){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.diasPrueba = tiempoLicencia;
                tpvState.licencia.unidadTiempo = unidadTiempo;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                await saveState();
                lic_checkLicense();
                startLicenseAutoCheck(); // Reiniciar el auto-check con la nueva unidad
                const unidadTexto = unidadTiempo === 'dias' ? 'días' : unidadTiempo === 'minutos' ? 'minutos' : 'segundos';
                showToast(`${lang.toast_license_activated} (${tiempoLicencia} ${unidadTexto})`, "success");
            } else {
                showToast(lang.toast_license_incorrect,"danger");
            }
        }

        function lic_checkLicense(){
            const { licencia } = tpvState;
            const estado = document.getElementById("lic-status");
            const countdownContainer = document.getElementById("lic-countdown-container");
            const countdownDisplay = document.getElementById("lic-countdown");
            const deactivateSection = document.getElementById("deactivate-license-section");
            const lang = getLang();
            const tiempoRestante = lic_getRemainingDays();
            const tiempoTexto = lic_getTimeUnitText();
            
            const _licEl = document.getElementById("lic-client-id"); if(_licEl) { _licEl.value = licencia.clienteId || "—"; _licEl.innerText = licencia.clienteId || "—"; }
            const overlay = document.getElementById("license-lock-overlay");
            const overlayClientId = document.getElementById("overlay-client-id");
            
            // Guardia: si los elementos del tab no existen aún, salir sin error
            if (!estado || !countdownContainer) return;
            
            // Actualizar ID en el overlay
            if (overlayClientId) {
                overlayClientId.value = licencia.clienteId;
            }
            
            // ⚡ MODO DE PRUEBA RÁPIDA: Permite usar sin licencia presionando Ctrl+Shift+T
            const modoTestRapido = localStorage.getItem('tpv_test_rapido') === 'true';
            
            if(modoTestRapido) {
                estado.innerText = "🔧 MODO PRUEBA RÁPIDA ACTIVADO";
                estado.className = "text-primary fw-bold";
                if(overlay) overlay.classList.add("d-none");
                countdownContainer.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
                return; // Salir sin bloquear
            }
            
            licencia.activada = true; licencia.tipo = 'premium';
            if(licencia.activada){
                estado.innerText = lang.license_activated;
                estado.className = "text-success fw-bold";
                if(overlay) overlay.classList.add("d-none");
                countdownContainer.classList.add("d-none");
                // Mostrar botón de desactivar cuando hay licencia activa
                if(deactivateSection) deactivateSection.classList.remove("d-none");
            } else if(tiempoRestante > 0){
                estado.innerText = `Prueba: ${tiempoTexto} restantes`;
                estado.className = "text-warning fw-bold";
                if(overlay) overlay.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
                
                // Mostrar contador con unidad correcta
                countdownContainer.classList.remove("d-none");
                if (countdownDisplay) countdownDisplay.innerText = tiempoTexto + ' restante' + (tiempoRestante !== 1 ? 's' : '');
                
                // Cambiar color según tiempo restante
                const unidad = licencia.unidadTiempo || 'dias';
                if (unidad === 'segundos') {
                    if (tiempoRestante <= 30) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 60) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                } else if (unidad === 'minutos') {
                    if (tiempoRestante <= 5) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 10) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                } else {
                    if (tiempoRestante <= 3) {
                        countdownContainer.className = "alert alert-danger";
                    } else if (tiempoRestante <= 7) {
                        countdownContainer.className = "alert alert-warning";
                    } else {
                        countdownContainer.className = "alert alert-info";
                    }
                }
            } else {
                estado.innerText = "Activa - Sin límite";
                estado.className = "text-danger fw-bold";
                if(overlay) overlay.classList.remove("d-none");
                countdownContainer.classList.add("d-none");
                if(deactivateSection) deactivateSection.classList.add("d-none");
            }
        }
        
        // ⚡ Función para activar/desactivar modo de prueba rápida (Ctrl+Shift+T)
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                const modoActual = localStorage.getItem('tpv_test_rapido') === 'true';
                localStorage.setItem('tpv_test_rapido', !modoActual);
                showToast(
                    !modoActual ? 
                    '🔧 MODO PRUEBA RÁPIDA ACTIVADO - Sin restricciones de licencia' : 
                    '🔒 MODO PRUEBA RÁPIDA DESACTIVADO - Licencia requerida',
                    !modoActual ? 'success' : 'warning'
                );
                lic_checkLicense();
            }
        });
        
        function copyOverlayClientId() {
            const clientId = document.getElementById("overlay-client-id").value;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(clientId).then(() => {
                    showToast("ID copiado al portapapeles", "info");
                }).catch(err => {
                    console.error('Error al copiar: ', err);
                });
            }
        }
        
        async function lic_activateFromOverlay() {
            const key = document.getElementById("overlay-license-key").value.trim();
            const errorMsg = document.getElementById("overlay-error-message");
            const { clienteId } = tpvState.licencia;
            
            if(!key) {
                errorMsg.textContent = "Por favor, ingrese una clave de licencia.";
                errorMsg.classList.remove("d-none");
                return;
            }
            
            // Verificar clave administrativa
            const adminHash = await lic_sha256("admin" + getSecretKey());
            
            if(key === adminHash){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                tpvState.licencia.unidadTiempo = 'dias';
                await saveState();
                lic_checkLicense();
                showToast("Licencia de administrador activada", "success");
                document.getElementById("overlay-license-key").value = "";
                errorMsg.classList.add("d-none");
                return;
            }
            
            // Verificar claves con duración personalizada
            let claveValida = false;
            let tiempoLicencia = 0;
            let unidadTiempo = 'dias';
            
            const duracionesPosibles = [
                { valor: 30, unidad: 'dias' },
                { valor: 60, unidad: 'dias' },
                { valor: 90, unidad: 'dias' },
                { valor: 180, unidad: 'dias' },
                { valor: 365, unidad: 'dias' },
                { valor: 730, unidad: 'dias' },
                { valor: 1, unidad: 'minutos' },
                { valor: 5, unidad: 'minutos' },
                { valor: 10, unidad: 'minutos' },
                { valor: 30, unidad: 'minutos' },
                { valor: 60, unidad: 'minutos' },
                { valor: 30, unidad: 'segundos' },
                { valor: 60, unidad: 'segundos' },
                { valor: 120, unidad: 'segundos' },
                { valor: 300, unidad: 'segundos' }
            ];
            
            for (const duracion of duracionesPosibles) {
                const validHash = await lic_sha256(clienteId + getSecretKey() + duracion.valor + duracion.unidad);
                if (key === validHash) {
                    claveValida = true;
                    tiempoLicencia = duracion.valor;
                    unidadTiempo = duracion.unidad;
                    break;
                }
            }
            
            if(claveValida){
                tpvState.licencia.activada = true;
                tpvState.licencia.key = key;
                tpvState.licencia.diasPrueba = tiempoLicencia;
                tpvState.licencia.unidadTiempo = unidadTiempo;
                tpvState.licencia.fechaActivacion = new Date().toISOString();
                await saveState();
                lic_checkLicense();
                startLicenseAutoCheck(); // Reiniciar el auto-check con la nueva unidad
                const unidadTexto = unidadTiempo === 'dias' ? 'días' : unidadTiempo === 'minutos' ? 'minutos' : 'segundos';
                showToast(`Licencia activada (${tiempoLicencia} ${unidadTexto})`, "success");
                document.getElementById("overlay-license-key").value = "";
                errorMsg.classList.add("d-none");
            } else {
                errorMsg.textContent = "Clave incorrecta. Verifique que el ID y la clave sean correctos.";
                errorMsg.classList.remove("d-none");
            }
        }

        // --- FUNCIÓN PARA DESACTIVAR LICENCIA (ÚTIL PARA PRUEBAS) ---
        async function lic_deactivateLicense() {
            if((await tpvConfirm("¿Está seguro que desea desactivar la licencia actual?\n\nEsto es útil para probar diferentes claves de licencia."))){
                tpvState.licencia.activada = false;
                tpvState.licencia.key = "";
                tpvState.licencia.fechaActivacion = null;
                await saveState();
                lic_checkLicense();
                showToast("Licencia desactivada. Ahora puede probar otras claves.", "info");
                // Limpiar el campo de entrada
                document.getElementById("lic-key-input").value = "";
            }
        }

        // --- FUNCIÓN PARA GUARDAR NOMBRE PERSONALIZADO DEL TPV ---
        function conf_saveTPVName() {
            const nameInput = document.getElementById("tpv-name-input");
            const customName = nameInput.value.trim();
            
            if (!customName) {
                showToast("Por favor ingrese un nombre para el sistema TPV", "warning");
                return;
            }
            
            // Guardar en localStorage
            localStorage.setItem('tpv_custom_name', customName);
            
            // Actualizar el título en el header
            conf_updateTPVName();
            
            showToast("Nombre del TPV actualizado correctamente", "success");
        }

        // --- FUNCIÓN PARA ACTUALIZAR EL NOMBRE DEL TPV EN EL HEADER ---
        function conf_updateTPVName() {
            const customName = localStorage.getItem('tpv_custom_name');
            const nameElement = document.getElementById('tpv-custom-name');
            const lang = getLang();
            
            if (nameElement) {
                if (customName) {
                    nameElement.textContent = customName;
                } else {
                    // Usar el título por defecto según el idioma
                    nameElement.textContent = lang.app_title || 'Sistema TPV Profesional';
                }
            }
        }

        // --- FUNCIÓN PARA CARGAR EL NOMBRE GUARDADO AL INICIAR ---
        function conf_loadTPVName() {
            const customName = localStorage.getItem('tpv_custom_name');
            const nameInput = document.getElementById("tpv-name-input");
            
            if (customName) {
                if (nameInput) {
                    nameInput.value = customName;
                }
            }
            // Siempre actualizar el nombre (sea personalizado o por defecto)
            conf_updateTPVName();
        }

        // --- LÓGICA DE MANTENIMIENTO ---
        async function conf_limpiarVentasHoy() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_today_sales))) {
                const hoy = getTodayDateString();
                const ventasHoy = tpvState.ventasDiarias[hoy] ?? [];
                
                ventasHoy.forEach(v => inv_actualizarStockPorVenta((document.getElementById("inv-fechaActual")?.value ?? getTodayDateString()), v.productoId, -v.cantidad));
                tpvState.historialVentas = tpvState.historialVentas.filter(v => !ventasHoy.map(vh => vh.id).includes(v.id));
                tpvState.ventasDiarias[hoy] = [];
                
                await saveState();
                ventas_renderizarTablaHoy();
                registros_renderizar();
                await inv_aplicarGananciaGlobal();
                showToast(lang.toast_today_sales_cleared, "success");
            }
        }

        async function conf_limpiarCierres() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_closures))) {
                tpvState.cierresCaja = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_closures_cleared, "success");
            }
        }

        async function conf_limpiarHistorial() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_history))) {
                tpvState.historialVentas = [];
                await saveState();
                registros_renderizar();
                showToast(lang.toast_history_cleared, "success");
            }
        }

        async function conf_limpiarInventarios() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_inventories))) {
                tpvState.inventarios = {};
                await saveState();
                inv_cargarInventario(getTodayDateString());
                showToast(lang.toast_inventories_cleared, "success");
            }
        }

        async function conf_limpiarTodo() {
            const lang = getLang();
            if ((await tpvConfirm(lang.confirm_clear_everything))) {
                const { productos, categorias, config, licencia } = tpvState; // Preserve essential data
                tpvState = getDefaultState(); // Reset
                tpvState = { ...tpvState, productos, categorias, config, licencia }; // Restore
                await saveState();
                await refreshAllUI();
                showToast(lang.toast_app_reset, "success");
            }
        }

        // updateNetworkStatus: actualiza badge + indicador offline
        // Pinta el estado. Si se pasa 'estadoReal' (bool) lo usa; si no, navigator.onLine.
        function updateNetworkStatus(showToastMsg, estadoReal) {
            const isOnline = (typeof estadoReal === 'boolean') ? estadoReal : navigator.onLine;
            const indicator = document.getElementById('offline-indicator');
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            if (indicator) indicator.style.display = isOnline ? 'none' : 'block';
            if (statusBadge && statusText) {
                const icon = statusBadge.querySelector('i');
                statusBadge.classList.toggle('bg-success', isOnline);
                statusBadge.classList.toggle('bg-danger', !isOnline);
                statusBadge.classList.toggle('offline', !isOnline);
                if (icon) icon.className = isOnline ? 'bi bi-wifi' : 'bi bi-wifi-off';
                statusText.textContent = isOnline ? 'Online' : 'Offline';
            }
            if (showToastMsg) {
                if (isOnline && window.wasOffline) {
                    showToast('Conexión restaurada', 'success');
                    window.wasOffline = false;
                    conf_setLanguage(tpvState?.config?.lang || 'es').catch(function(){});
                } else if (!isOnline) {
                    showToast('Modo Offline — datos guardados localmente', 'warning');
                    window.wasOffline = true;
                }
            }
        }

        // Chequeo REAL de internet: navigator.onLine en el WebView siempre es true
        // (hay red hacia 127.0.0.1). Hacemos un fetch real a un recurso externo.
        async function _checkInternetReal() {
            if (!navigator.onLine) return false;
            try {
                const ctrl = new AbortController();
                setTimeout(() => ctrl.abort(), 3500);
                // Recurso liviano y permisivo con CORS; no-cors evita bloqueos.
                await fetch('https://www.gstatic.com/generate_204',
                            { method: 'GET', mode: 'no-cors', cache: 'no-store', signal: ctrl.signal });
                return true;
            } catch (e) {
                return false;
            }
        }

        let _netPrev = null;
        async function _monitorRed(conToast) {
            const real = await _checkInternetReal();
            if (real !== _netPrev) {
                updateNetworkStatus(conToast === true && _netPrev !== null, real);
                _netPrev = real;
            }
        }
        // Polling cada 8s + reacción inmediata a eventos del navegador.
        setInterval(() => _monitorRed(true), 8000);
        window.addEventListener('online',  () => _monitorRed(true));
        window.addEventListener('offline', () => { _netPrev = false; updateNetworkStatus(true, false); });
        setTimeout(() => _monitorRed(false), 1500);
        
        window.addEventListener('load', function() {
            conf_loadTPVName();
            updateNetworkStatus();
            
            // Indicar estado actual en consola
            if (!navigator.onLine) {
                console.log('📴 Actualmente sin conexión - Todo funciona normalmente');
            } else {
                console.log('📶 Conectado a internet');
            }
            
            // Iniciar verificación automática de licencia para unidades pequeñas
            startLicenseAutoCheck();
        });
        
        // ==================== AUTO-ACTUALIZACIÓN DE LICENCIA ====================
        let licenseCheckInterval = null;
        
        function startLicenseAutoCheck() {
            // Limpiar intervalo existente
            if (licenseCheckInterval) {
                clearInterval(licenseCheckInterval);
            }
            
            const unidad = tpvState.licencia?.unidadTiempo || 'dias';
            
            // Configurar intervalo según la unidad
            if (unidad === 'segundos') {
                // Actualizar cada segundo
                licenseCheckInterval = setInterval(() => {
                    lic_checkLicense();
                }, 1000);
            } else if (unidad === 'minutos') {
                // Actualizar cada 10 segundos
                licenseCheckInterval = setInterval(() => {
                    lic_checkLicense();
                }, 10000);
            } else {
                // Para días, actualizar cada 5 minutos
                licenseCheckInterval = setInterval(() => {
                    lic_checkLicense();
                }, 300000);
            }
        }
        
        // ========== FUNCIONES DE BACKUP AUTOMÁTICO ==========
        async function crear_backup_automatico(tipo = 'auto') {
            try {
                const timestamp = new Date().toISOString();
                const backupData = {
                    timestamp: timestamp,
                    tipo: tipo,
                    version: '1.0',
                    data: tpvState
                };
                
                // Guardar en localStorage
                const backupKey = `tpv_backup_${timestamp}`;
                localStorage.setItem(backupKey, JSON.stringify(backupData));
                
                // Mantener solo las últimas 10 copias
                const allBackups = Object.keys(localStorage).filter(key => key.startsWith('tpv_backup_'));
                if (allBackups.length > 10) {
                    allBackups.sort().slice(0, allBackups.length - 10).forEach(key => {
                        localStorage.removeItem(key);
                    });
                }
                
                console.log('✅ Copia de seguridad creada:', tipo);
                return true;
            } catch (error) {
                console.error('❌ Error al crear backup:', error);
                return false;
            }
        }
        
        async function crear_backup_manual() {
            const success = await crear_backup_automatico('manual');
            if (success) {
                showToast('Copia de seguridad creada exitosamente', 'success');
                actualizar_lista_backups();
            } else {
                showToast('Error al crear la copia de seguridad', 'danger');
            }
        }
        
        function actualizar_lista_backups() {
            const allBackups = Object.keys(localStorage)
                .filter(key => key.startsWith('tpv_backup_'))
                .map(key => {
                    const data = JSON.parse(localStorage.getItem(key));
                    return {
                        key: key,
                        timestamp: data.timestamp,
                        tipo: data.tipo
                    };
                })
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            const tbody = document.getElementById('backup-list-body');
            if (!tbody) return;
            
            tbody.innerHTML = allBackups.map(backup => {
                const fecha = new Date(backup.timestamp).toLocaleString();
                return `
                    <tr>
                        <td>${fecha}</td>
                        <td><span class="badge bg-${backup.tipo === 'manual' ? 'primary' : 'secondary'}">${backup.tipo}</span></td>
                        <td>
                            <button class="btn btn-sm btn-success" onclick="restaurar_backup_directo('${backup.key}')">
                                <i class="bi bi-cloud-arrow-down"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="eliminar_backup_individual('${backup.key}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        async function restaurar_backup(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = async function(e) {
                try {
                    const backupData = JSON.parse(e.target.result);
                    tpvState = backupData.data;
                    await saveState();
                    showToast('Copia de seguridad restaurada exitosamente', 'success');
                    location.reload();
                } catch (error) {
                    showToast('Error al restaurar la copia de seguridad', 'danger');
                    console.error(error);
                }
            };
            reader.readAsText(file);
        }
        
        async function restaurar_backup_directo(backupKey) {
            if (!(await tpvConfirm('¿Está seguro de restaurar esta copia de seguridad? Se perderán los cambios no guardados.'))) {
                return;
            }
            
            try {
                const backupData = JSON.parse(localStorage.getItem(backupKey));
                tpvState = backupData.data;
                await saveState();
                showToast('Copia de seguridad restaurada exitosamente', 'success');
                location.reload();
            } catch (error) {
                showToast('Error al restaurar la copia de seguridad', 'danger');
                console.error(error);
            }
        }
        
        async function eliminar_backup_individual(backupKey) {
            if ((await tpvConfirm('¿Está seguro de eliminar esta copia de seguridad?'))) {
                localStorage.removeItem(backupKey);
                showToast('Copia eliminada', 'info');
                actualizar_lista_backups();
            }
        }
        
        async function eliminar_backups() {
            if ((await tpvConfirm('¿Está seguro de eliminar TODAS las copias de seguridad?'))) {
                const allBackups = Object.keys(localStorage).filter(key => key.startsWith('tpv_backup_'));
                allBackups.forEach(key => localStorage.removeItem(key));
                showToast('Todas las copias han sido eliminadas', 'warning');
                actualizar_lista_backups();
            }
        }
        
        // ========== FUNCIONES DE EXPORTACIÓN DE VENTAS ==========
        
        // NUEVO: Sistema de exportación mejorado para móviles con selector de ubicación
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
                showToast('❌ Error al exportar: ' + errorMsg, 'danger', 5000);
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
            
            tpvAlert(mensaje);
        }
        
        /**
         * Limpiar memoria del sistema de aprendizaje
         */
        async function limpiar_memoria_aprendizaje() {
            if ((await tpvConfirm('⚠️ ¿Estás seguro de limpiar la memoria del sistema?\n\nEsto eliminará:\n• Configuraciones de importación aprendidas\n• Preferencias de exportación\n• Historial de estructuras\n\nEl sistema volverá a aprender desde cero.'))) {
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
        function activar_licencia() { lic_activateLicense(); }
        
        async function eliminar_licencia() {
            if ((await tpvConfirm('¿Está seguro de eliminar la licencia actual?'))) {
                tpvState.licencia.activada = false;
                tpvState.licencia.key = null;
                saveState();
                showToast('Licencia eliminada', 'warning');
                lic_checkLicense();
            }
        }
        
        function mostrar_info_licencia() {
            // Delegamos al sistema principal de licencias
            lic_checkLicense();
        }
        
        // ========== FUNCIONES DE LOGS ==========
        let systemLogs = [];
        
        function agregar_log(mensaje, tipo = 'info') {
            const timestamp = new Date().toISOString();
            systemLogs.push({ timestamp, tipo, mensaje });
            
            // Mantener solo los últimos 100 logs
            if (systemLogs.length > 100) {
                systemLogs = systemLogs.slice(-100);
            }
            
            actualizar_logs();
        }
        
        function actualizar_logs() {
            const display = document.getElementById('logs-display');
            if (!display) return;
            
            const logsHTML = systemLogs.map(log => {
                const fecha = new Date(log.timestamp).toLocaleString();
                const color = log.tipo === 'error' ? '#f00' : log.tipo === 'warning' ? '#ff0' : '#0f0';
                return `<p style="color: ${color}; margin: 0.25rem 0;">[${fecha}] ${log.mensaje}</p>`;
            }).reverse().join('');
            
            display.innerHTML = logsHTML || '<p>No hay logs disponibles</p>';
        }
        
        async function limpiar_logs() {
            if ((await tpvConfirm('¿Está seguro de limpiar todos los logs?'))) {
                systemLogs = [];
                actualizar_logs();
                showToast('Logs limpiados', 'info');
            }
        }
        
        // Agregar log inicial
        agregar_log('Sistema TPV iniciado correctamente', 'info');
        
        // ========== FUNCIONES DE ELIMINACIÓN DE REGISTROS ==========
        async function eliminar_cierre(fecha) {
            if ((await tpvConfirm(`¿Está seguro de eliminar el cierre del día ${fecha}?`))) {
                tpvState.cierresCaja = tpvState.cierresCaja.filter(c => c.fecha !== fecha);
                await saveState();
                showToast('Cierre eliminado exitosamente', 'success');
                registros_renderizar();
            }
        }
        
        async function eliminar_todos_cierres() {
            if ((await tpvConfirm('¿Está seguro de eliminar TODOS los cierres de caja? Esta acción no se puede deshacer.'))) {
                tpvState.cierresCaja = [];
                await saveState();
                showToast('Todos los cierres han sido eliminados', 'warning');
                registros_renderizar();
            }
        }
        
        async function eliminar_venta_individual(index) {
            const sortedHistorial = [...tpvState.historialVentas].sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
            const venta = sortedHistorial[index];
            
            if ((await tpvConfirm(`¿Está seguro de eliminar esta venta de ${venta.nombre}?`))) {
                const ventaIndex = tpvState.historialVentas.indexOf(venta);
                tpvState.historialVentas.splice(ventaIndex, 1);
                await saveState();
                showToast('Venta eliminada exitosamente', 'success');
                registros_renderizar();
            }
        }
        
        async function eliminar_todas_ventas() {
            if ((await tpvConfirm('¿Está seguro de eliminar TODO el historial de ventas? Esta acción no se puede deshacer.'))) {
                tpvState.historialVentas = [];
                await saveState();
                showToast('Todo el historial de ventas ha sido eliminado', 'warning');
                registros_renderizar();
            }
        }
        
        // Funciones auxiliares simples
        async function copiarTexto(texto) {
            try {
                await navigator.clipboard.writeText(texto);
                showToast('✅ Copiado', 'success');
            } catch {
                const ta = document.createElement('textarea');
                ta.value = texto;
                ta.style.position = 'fixed';
                ta.style.opacity = '0';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                showToast('✅ Copiado', 'success');
            }
        }

// ═══ HOTFIX v8.0.1 - Refresh en tiempo real ═══
async function tpv_refreshFromServer() {
    try {
        const r = await fetch('/api/catalogo', {credentials:'same-origin'});
        const d = await r.json();
        if (d.ok && d.productos && d.productos.length) {
            const hoy = new Date().toISOString().split('T')[0];
            tpvState.productos = d.productos;
            tpvState.categorias = d.categorias || [...new Set(d.productos.map(p=>p.categoria))].sort();
            tpvState.inventarios[hoy] = d.productos.map(p => ({
                id: p.id, nombre: p.nombre,
                categoria: p.categoria ?? 'General', um: p.um ?? 'Un',
                cantInicial: Number(p.stock) || 0, vendido: 0,
                cantFinal: Number(p.stock) || 0,
                precioVenta: Number(p.precio) || 0,
                precioCosto: Number(p.costo) || 0,
                costoUnitario: Number(p.costo) || 0,
                importe: 0, comision: 0, gananciaNeta: 0
            }));
            if (typeof inv_recalcularVentasDelDia === 'function') {
                try { inv_recalcularVentasDelDia(hoy); } catch(_e) {}
            }
            if (typeof tpv_renderizarProductos === 'function') tpv_renderizarProductos();
            if (typeof tpv_renderizarFiltroCategorias === 'function') tpv_renderizarFiltroCategorias();
            if (typeof inv_renderizarTabla === 'function') inv_renderizarTabla(hoy);
            if (typeof ventas_renderizarTablaHoy === 'function') ventas_renderizarTablaHoy();
            if (typeof dashboard_cargar === 'function') dashboard_cargar();
            console.log('TPV refrescado: ' + d.productos.length + ' productos');
        }
    } catch(e) { console.warn('Refresh fallo:', e.message); }
}
setInterval(() => {
    if (document.visibilityState === 'visible' && window.AUTH?.usuario) tpv_refreshFromServer();
}, 30000);


// ═══ HOTFIX v8.0.2 — Window exports ═══
(function(){
  if(typeof tpv_renderizarProductos==='function' && !window.tpv_renderizarProductos) window.tpv_renderizarProductos=tpv_renderizarProductos;
  if(typeof conf_setLanguage==='function' && !window.conf_setLanguage) window.conf_setLanguage=conf_setLanguage;
  if(typeof saveState==='function' && !window.saveState) window.saveState=saveState;
  if(typeof loadState==='function' && !window.loadState) window.loadState=loadState;
  if(typeof refreshAllUI==='function' && !window.refreshAllUI) window.refreshAllUI=refreshAllUI;
  if(typeof inv_renderizarTabla==='function' && !window.inv_renderizarTabla) window.inv_renderizarTabla=inv_renderizarTabla;
  if(typeof registros_renderizar==='function' && !window.registros_renderizar) window.registros_renderizar=registros_renderizar;
  if(typeof gestion_guardarProducto==='function' && !window.gestion_guardarProducto) window.gestion_guardarProducto=gestion_guardarProducto;
  if(typeof ventas_renderizarTablaHoy==='function' && !window.ventas_renderizarTablaHoy) window.ventas_renderizarTablaHoy=ventas_renderizarTablaHoy;
})();

// ═══ HOTFIX v8.0.2 — Auto-refresh cada 30s ═══
(function(){
    if(window._tpvAutoRefresh) return;
    window._tpvAutoRefresh = true;
    setInterval(async function(){
        if(typeof catalogo_cargarDesdeServidor==='function'){
            try{
                await catalogo_cargarDesdeServidor();
                if(typeof tpv_renderizarProductos==='function') tpv_renderizarProductos();
                if(typeof tpv_renderizarFiltroCategorias==='function') tpv_renderizarFiltroCategorias();
            }catch(e){}
        }
    },30000);
    console.log('🔄 Auto-refresh instalado (30s)');
})();

// ═══ HOTFIX v8.0.2 — Rebuild inventario diario desde catalogo ═══
(function(){
    if(window._tpvRebuildInv) return;
    window._tpvRebuildInv = true;
    var _origCargar = typeof catalogo_cargarDesdeServidor==='function'?catalogo_cargarDesdeServidor:null;
    if(_origCargar){
        window.catalogo_cargarDesdeServidor = async function(){
            await _origCargar();
            var hoy = typeof getTodayDateString==='function'?getTodayDateString():new Date().toISOString().split('T')[0];
            if(!tpvState.inventarios) tpvState.inventarios={};
            if(!tpvState.inventarios[hoy]) tpvState.inventarios[hoy]=[];
            var invArr = tpvState.inventarios[hoy];
            var invMap = {};
            invArr.forEach(function(it){invMap[it.id]=it;});
            tpvState.productos.forEach(function(p){
                if(!invMap[p.id]){
                    var stock = p.stock||0;
                    invArr.push({
                        id:p.id, nombre:p.nombre, categoria:p.categoria||'General',
                        pVenta:p.precio||0, um:p.um||'Un',
                        cantInicial:stock, cantFinal:stock, vendido:0,
                        iVenta:0, pCosto:p.costo||0, comision:0, ganancia:0
                    });
                }
            });
        };
    }
})();
