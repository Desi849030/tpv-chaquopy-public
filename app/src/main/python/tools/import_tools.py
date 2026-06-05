from tools.base import _t

IMPORT_TOOLS = {
    "reconstruir_productos": _t("reconstruir_productos",
        "Sincroniza una lista de productos con la base de datos SQLite. Reemplaza el catalogo completo y actualiza inventario_general.",
        "importacion", "/api/reconstruir-desde-productos", "POST",
        [{"name": "productos", "type": "list", "description": "Lista de productos con id, nombre, precio, costoUnitario, categoria, um", "required": True},
         {"name": "admin_id", "type": "str", "description": "ID del administrador (default: system)", "required": False}],
        role="administrador"),
    "importar_catalogo_inventario": _t("importar_catalogo_inventario",
        "Importa todos los productos del catalogo al inventario general. Nuevos: stock 0. Existentes: conserva stock actual.",
        "importacion", "/api/inventario/importar-catalogo", "POST",
        [],
        role="administrador"),
    "obtener_productos_catalogo": _t("obtener_productos_catalogo",
        "Retorna todos los productos del catalogo desde la base de datos SQLite.",
        "importacion", "/api/productos", "GET",
        [],
        role="administrador"),
}
