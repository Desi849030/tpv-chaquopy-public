"""
i18n_builder.py - Construye y auto-nutre el diccionario i18n offline
Extrae claves data-i18n del HTML, genera traducciones ES/EN,
y se actualiza automáticamente con nuevas claves encontradas.
"""
import os, re, json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "assets", "frontend", "templates", "partials")
DICT_FILE = os.path.join(BASE_DIR, "..", "assets", "frontend", "static", "js", "tpv", "tpv_i18n_dict.js")

# Traducciones base (español → inglés)
TRANSLATIONS = {
    # Navegación
    "menu_catalog": "Catalog",
    "menu_sales": "Sales",
    "menu_inventory": "Inventory",
    "menu_reports": "Reports",
    "menu_settings": "Settings",
    "menu_tienda": "Store",
    "menu_caja": "Cash Register",
    "menu_dashboard": "Dashboard",
    "menu_clients": "Clients",
    "menu_orders": "Orders",
    
    # Acciones
    "th_actions": "Actions",
    "btn_save": "Save",
    "btn_cancel": "Cancel",
    "btn_delete": "Delete",
    "btn_edit": "Edit",
    "btn_add": "Add",
    "btn_search": "Search",
    "btn_export": "Export",
    "btn_import": "Import",
    "btn_refresh": "Refresh",
    "btn_close": "Close",
    "btn_confirm": "Confirm",
    "btn_back": "Back",
    "btn_next": "Next",
    
    # Productos
    "th_product": "Product",
    "th_price": "Price",
    "th_stock": "Stock",
    "th_category": "Category",
    "th_cost": "Cost",
    "th_total": "Total",
    "th_quantity": "Quantity",
    "th_date": "Date",
    "th_status": "Status",
    "th_name": "Name",
    "th_email": "Email",
    "th_phone": "Phone",
    "th_description": "Description",
    "th_barcode": "Barcode",
    "th_image": "Image",
    "th_unit": "Unit",
    "mgmt_th_category": "Category",
    "filter_by_price": "Filter by price",
    "filter_by_category": "Filter by category",
    "filter_all": "All",
    "search_placeholder": "Search...",
    
    # Ventas
    "total_sales": "Total Sales",
    "total_units": "Total Units",
    "total_value": "Total (Value)",
    "daily_sales": "Daily Sales",
    "monthly_sales": "Monthly Sales",
    "sale_detail": "Sale Detail",
    "payment_method": "Payment Method",
    
    # Clientes
    "client_name": "Name",
    "client_email": "Email",
    "client_phone": "Phone",
    "client_register": "Register Client",
    "client_list": "Client List",
    
    # Inventario
    "current_stock": "Current Stock",
    "min_stock": "Min Stock",
    "stock_alert": "Stock Alert",
    "stock_movement": "Stock Movement",
    "entry": "Entry",
    "exit": "Exit",
    
    # General
    "loading": "Loading...",
    "no_data": "No data",
    "confirm_delete": "Delete?",
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "info": "Info",
    "saving": "Saving...",
    "deleting": "Deleting...",
    "processing": "Processing...",
    
    # Licencias
    "license_status": "License Status",
    "license_activate": "Activate License",
    "license_key": "License Key",
    "license_expires": "Expires",
    "license_days_left": "Days Left",
    
    # Dashboard
    "dashboard_title": "Dashboard",
    "kpi_revenue": "Revenue",
    "kpi_orders": "Orders",
    "kpi_clients": "Clients",
    "kpi_products": "Products",
}


def extraer_claves_html():
    """Extrae todas las claves data-i18n de los archivos HTML"""
    claves = set()
    if not os.path.exists(TEMPLATES_DIR):
        print(f"❌ Directorio no encontrado: {TEMPLATES_DIR}")
        return claves
    
    for root, _, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    # Buscar data-i18n="..."
                    matches = re.findall(r'data-i18n="([^"]+)"', content)
                    claves.update(matches)
                    # Buscar data-i18n-placeholder="..."
                    matches = re.findall(r'data-i18n-placeholder="([^"]+)"', content)
                    claves.update(matches)
    
    return claves


def generar_traduccion_automatica(clave_es):
    """Genera traducción automática basada en reglas simples"""
    # Si ya existe, usarla
    if clave_es in TRANSLATIONS:
        return TRANSLATIONS[clave_es]
    
    # Reglas de traducción automática
    traducciones = {
        "th_": lambda x: x[3:].replace("_", " ").title(),
        "btn_": lambda x: x[4:].replace("_", " ").title(),
        "menu_": lambda x: x[5:].replace("_", " ").title(),
        "filter_": lambda x: x[7:].replace("_", " ").title(),
        "kpi_": lambda x: x[4:].replace("_", " ").title(),
        "tab_": lambda x: x[4:].replace("_", " ").title(),
        "label_": lambda x: x[6:].replace("_", " ").title(),
    }
    
    for prefix, func in traducciones.items():
        if clave_es.startswith(prefix):
            # Traducción simple de palabras comunes
            text = func(clave_es)
            words = {
                "producto": "Product", "productos": "Products",
                "categoria": "Category", "categorias": "Categories",
                "precio": "Price", "stock": "Stock",
                "venta": "Sale", "ventas": "Sales",
                "cliente": "Client", "clientes": "Clients",
                "accion": "Action", "acciones": "Actions",
                "nombre": "Name", "email": "Email",
                "telefono": "Phone", "direccion": "Address",
                "fecha": "Date", "estado": "Status",
                "total": "Total", "cantidad": "Quantity",
                "descripcion": "Description",
                "guardar": "Save", "cancelar": "Cancel",
                "eliminar": "Delete", "editar": "Edit",
                "agregar": "Add", "buscar": "Search",
                "exportar": "Export", "importar": "Import",
                "actualizar": "Refresh", "cerrar": "Close",
                "confirmar": "Confirm", "volver": "Back",
                "siguiente": "Next", "anterior": "Previous",
                "todos": "All", "ninguno": "None",
                "activo": "Active", "inactivo": "Inactive",
                "pendiente": "Pending", "completado": "Completed",
                "cancelado": "Cancelled", "error": "Error",
                "exito": "Success", "advertencia": "Warning",
            }
            for es, en in words.items():
                text = text.replace(es.title(), en).replace(es, en)
            return text
    
    # Fallback: devolver la clave formateada
    return clave_es.replace("_", " ").title()


def construir_diccionario():
    """Construye el archivo JS del diccionario"""
    claves = extraer_claves_html()
    
    if not claves:
        print("❌ No se encontraron claves i18n")
        return
    
    print(f"✅ {len(claves)} claves i18n encontradas")
    
    # Construir objetos ES y EN
    es_dict = {}
    en_dict = {}
    
    for clave in sorted(claves):
        # El texto en español es la misma clave formateada
        texto_es = clave.replace("_", " ").replace("th ", "").replace("btn ", "").replace("menu ", "")
        texto_es = texto_es[0].upper() + texto_es[1:] if texto_es else clave
        es_dict[clave] = texto_es
        
        # Traducción al inglés
        en_dict[clave] = generar_traduccion_automatica(clave)
    
    # Generar archivo JS
    js_content = f"""// Diccionario i18n offline - Auto-generado por i18n_builder.py
// {len(claves)} términos ES/EN
// Actualizado: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
var TPV_I18N = {{
  es: {json.dumps(es_dict, indent=4, ensure_ascii=False)},
  en: {json.dumps(en_dict, indent=4, ensure_ascii=False)}
}};

// Aplicar traducción offline
function tpv_i18n_apply(lang) {{
  if (!TPV_I18N || !TPV_I18N[lang]) return;
  
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    const key = el.getAttribute('data-i18n');
    if (TPV_I18N[lang][key]) {{
      el.textContent = TPV_I18N[lang][key];
    }}
  }});
  
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {{
    const key = el.getAttribute('data-i18n-placeholder');
    if (TPV_I18N[lang][key]) {{
      el.placeholder = TPV_I18N[lang][key];
    }}
  }});
}}

console.log('📖 Diccionario i18n offline: ' + Object.keys(TPV_I18N.es).length + ' términos ES/EN');
"""
    
    # Escribir archivo
    os.makedirs(os.path.dirname(DICT_FILE), exist_ok=True)
    with open(DICT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Diccionario guardado: {DICT_FILE}")
    print(f"   Términos ES: {len(es_dict)}")
    print(f"   Términos EN: {len(en_dict)}")
    
    # Mostrar nuevas claves sin traducción manual
    nuevas = [c for c in claves if c not in TRANSLATIONS]
    if nuevas:
        print(f"\n📝 {len(nuevas)} claves sin traducción manual (usando auto-traducción):")
        for c in nuevas[:10]:
            print(f"   {c} → {en_dict[c]}")
        if len(nuevas) > 10:
            print(f"   ... y {len(nuevas)-10} más")


if __name__ == "__main__":
    print("🔧 i18n Builder - TPV UltraSmart")
    print("=" * 50)
    construir_diccionario()
    print("\n💡 Para regenerar: python tools/i18n_builder.py")
