// tpv_estado_persist.js -- Estado global, IndexedDB, listeners
// tpv_estado_sync.js — Estado global, IndexedDB, sincronización servidor, config UI
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
            // v6.9 PARCHE_6: sin clave hardcodeada
            var key = TPV_CONFIG ? TPV_CONFIG.getCurrentKey() : "(clave pendiente)"; return (typeof key === 'string') ? key : "(clave pendiente)";
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
                license_expired_title:"Licencia Expirada", license_expired_desc:"Por favor, active su producto.", license_activated: "Activada", license_trial: (days) => `Prueba (${days} días restantes)`, license_expired: "Expirada",
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
            openDb: () => new Promise((resolve, reject) => {
                const request = indexedDB.open(DB_NAME, DB_VERSION);
                request.onupgradeneeded = e => {
                    const db = e.target.result;
                    if (!db.objectStoreNames.contains(STORE_NAME)) {
                        db.createObjectStore(STORE_NAME);
                    }
                };
                request.onsuccess = e => resolve(e.target.result);
                request.onerror = e => reject(e.target.error);
            }),
            save: (db, data) => new Promise((resolve, reject) => {
                const tx = db.transaction(STORE_NAME, 'readwrite');
                tx.objectStore(STORE_NAME).put(data, 'appState');
                tx.oncomplete = () => resolve();
                tx.onerror = e => reject(e.target.error);
            }),
            load: (db) => new Promise((resolve, reject) => {
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

        // navigator.onLine NO es confiable en Android WebView
        // Usamos polling real a /api/status cada 6 segundos
        window._realOnline = navigator.onLine;

        window.addEventListener('online',  function(){ updateNetworkStatus(true); });
        window.addEventListener('offline', function(){ updateNetworkStatus(false); });

        setInterval(function() {
            fetch('/api/ping',{method:'GET',cache:'no-store'})
            .then(function(r){return r.json();})
            .then(function(d){
                if(d.online){var e=!window._realOnline;window._realOnline=true;if(e)updateNetworkStatus(true);}
                else{window._realOnline=false;updateNetworkStatus(false);}
            })
            .catch(function(){var e=window._realOnline;window._realOnline=false;if(e)updateNetworkStatus(false);});
        }, 6000);       // --- INICIALIZACIÓN Y MANEJO DE ESTADO ---
        document.addEventListener('DOMContentLoaded', async () => {
            // Solo cargamos el estado en memoria.
            // La UI se inicializa en _auth_mostrarApp() DESPUÉS del login.
            if (typeof loadState === "function") await loadState();
            console.log('✅ TPV state cargado — esperando autenticación');
        });

        document.addEventListener('visibilitychange', async () => {
            // Si se perdió el estado Y ya hay sesión activa, recargar UI
            if (document.visibilityState === 'visible'
                && Object.keys(tpvState).length === 0
                && window.AUTH?.usuario) {
                if (typeof loadState === "function") await loadState();
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
            const inventarioHoy = [];  // v6.9 BUG FIX 1: era {} (objeto), ahora [] (array)
            
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

