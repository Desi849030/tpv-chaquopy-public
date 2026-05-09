"""
tool_registry.py — Catalogo de herramientas para la IA Agéntica.
Registra todas las funciones disponibles del TPV como "tools" con
descripcion, parametros y tipo de acceso. El reasoning_engine consulta
este catalogo para decidir que herramienta usar.

Industrialization v5 — Agentic AI Layer
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ToolDefinition:
    """Definicion de una herramienta disponible para el agente."""
    name: str
    description: str
    category: str  # inventario, ventas, clientes, finanzas, reportes, sistema
    params: List[Dict[str, str]]  # [{name, type, description, required}]
    requires_auth: bool = True
    requires_role: Optional[str] = None  # administrador, vendedor, etc.


# ══════════════════════════════════════════════════════════
#  CATALOGO COMPLETO DE HERRAMIENTAS
# ══════════════════════════════════════════════════════════

TOOL_CATALOG: Dict[str, ToolDefinition] = {
    # ── INVENTARIO ──
    "buscar_productos": ToolDefinition(
        name="buscar_productos",
        description="Busca productos por nombre, categoria o codigo de barras. "
                    "Retorna lista de productos con precio, stock y categoria.",
        category="inventario",
        params=[
            {"name": "query", "type": "str", "description": "Termino de busqueda", "required": False},
            {"name": "categoria", "type": "str", "description": "Filtrar por categoria", "required": False},
        ],
    ),
    "obtener_inventario": ToolDefinition(
        name="obtener_inventario",
        description="Obtiene el stock actual de todos los productos o de uno especifico. "
                    "Incluye stock minimo y alertas de reorden.",
        category="inventario",
        params=[
            {"name": "producto_id", "type": "str", "description": "ID del producto (opcional)", "required": False},
        ],
    ),
    "modificar_stock": ToolDefinition(
        name="modificar_stock",
        description="Ajusta el stock de un producto: entrada, salida o ajuste manual. "
                    "Registra el movimiento y actualiza el inventario.",
        category="inventario",
        params=[
            {"name": "producto_id", "type": "str", "description": "ID del producto", "required": True},
            {"name": "cantidad", "type": "float", "description": "Cantidad a ajustar", "required": True},
            {"name": "tipo", "type": "str", "description": "entrada, salida o ajuste", "required": True},
            {"name": "motivo", "type": "str", "description": "Razon del ajuste", "required": False},
        ],
        requires_role="vendedor",
    ),
    "importar_productos": ToolDefinition(
        name="importar_productos",
        description="Importa un lote de productos con validacion profesional. "
                    "Ejecuta dry-run primero y luego transaccion atomica.",
        category="inventario",
        params=[
            {"name": "productos", "type": "list", "description": "Lista de productos a importar", "required": True},
            {"name": "ejecutar", "type": "bool", "description": "True para ejecutar, False para solo validar", "required": False},
        ],
        requires_role="vendedor",
    ),

    # ── VENTAS ──
    "consultar_ventas": ToolDefinition(
        name="consultar_ventas",
        description="Consulta ventas por fecha, rango, metodo de pago o las mas recientes. "
                    "Retorna detalles incluyendo productos vendidos y totales.",
        category="ventas",
        params=[
            {"name": "fecha_inicio", "type": "str", "description": "Fecha inicio (YYYY-MM-DD)", "required": False},
            {"name": "fecha_fin", "type": "str", "description": "Fecha fin (YYYY-MM-DD)", "required": False},
            {"name": "metodo_pago", "type": "str", "description": "Filtrar por metodo de pago", "required": False},
            {"name": "limite", "type": "int", "description": "Numero maximo de resultados", "required": False},
        ],
    ),
    "registrar_venta": ToolDefinition(
        name="registrar_venta",
        description="Registra una nueva venta con productos, metodo de pago y opcionalmente cliente. "
                    "Actualiza inventario automaticamente.",
        category="ventas",
        params=[
            {"name": "productos", "type": "list", "description": "Lista de {producto_id, cantidad}", "required": True},
            {"name": "metodo_pago", "type": "str", "description": "efectivo, tarjeta, credito", "required": True},
            {"name": "cliente_id", "type": "str", "description": "ID del cliente (opcional)", "required": False},
        ],
        requires_role="vendedor",
    ),
    "obtener_detalle_venta": ToolDefinition(
        name="obtener_detalle_venta",
        description="Obtiene el detalle completo de una venta especifica: productos, "
                    "cantidades, subtotales, metodo de pago y estado.",
        category="ventas",
        params=[
            {"name": "venta_id", "type": "str", "description": "ID de la venta", "required": True},
        ],
    ),

    # ── CLIENTES ──
    "buscar_clientes": ToolDefinition(
        name="buscar_clientes",
        description="Busca clientes por nombre, telefono o email. "
                    "Retorna lista con datos de contacto y historial.",
        category="clientes",
        params=[
            {"name": "query", "type": "str", "description": "Termino de busqueda", "required": False},
        ],
    ),
    "crear_cliente": ToolDefinition(
        name="crear_cliente",
        description="Registra un nuevo cliente en el sistema con nombre, telefono y email.",
        category="clientes",
        params=[
            {"name": "nombre", "type": "str", "description": "Nombre del cliente", "required": True},
            {"name": "telefono", "type": "str", "description": "Telefono", "required": False},
            {"name": "email", "type": "str", "description": "Email", "required": False},
        ],
        requires_role="vendedor",
    ),

    # ── FINANZAS / CAJA ──
    "estado_caja": ToolDefinition(
        name="estado_caja",
        description="Muestra el estado actual de la caja: monto inicial, ventas del dia, "
                    "retiros, ingresos y saldo actual.",
        category="finanzas",
        params=[],
    ),
    "abrir_caja": ToolDefinition(
        name="abrir_caja",
        description="Abre la caja registradora con un monto inicial. "
                    "Solo una caja puede estar abierta a la vez.",
        category="finanzas",
        params=[
            {"name": "monto_inicial", "type": "float", "description": "Monto inicial de la caja", "required": True},
        ],
        requires_role="vendedor",
    ),
    "cierre_caja": ToolDefinition(
        name="cierre_caja",
        description="Cierra la caja actual y genera el resumen del dia.",
        category="finanzas",
        params=[
            {"name": "monto_real", "type": "float", "description": "Monto real contado", "required": False},
        ],
        requires_role="vendedor",
    ),
    "corte_caja": ToolDefinition(
        name="corte_caja",
        description="Genera corte de caja del dia: ventas por metodo de pago, "
                    "retiros, ingresos y diferencia esperada vs real.",
        category="finanzas",
        params=[],
        requires_role="administrador",
    ),

    # ── REPORTES ──
    "estadisticas_ventas": ToolDefinition(
        name="estadisticas_ventas",
        description="Estadisticas de ventas por periodo: total, promedio, "
                    "productos mas vendidos, metodo de pago mas usado.",
        category="reportes",
        params=[
            {"name": "dias", "type": "int", "description": "Numero de dias a analizar", "required": False},
        ],
    ),
    "analisis_abc": ToolDefinition(
        name="analisis_abc",
        description="Analisis ABC de productos: clasifica en A (80% ventas), "
                    "B (15%) y C (5%) segun su contribucion a ingresos.",
        category="reportes",
        params=[],
    ),
    "productos_mas_vendidos": ToolDefinition(
        name="productos_mas_vendidos",
        description="Ranking de los productos mas vendidos en un periodo dado.",
        category="reportes",
        params=[
            {"name": "dias", "type": "int", "description": "Numero de dias", "required": False},
            {"name": "limite", "type": "int", "description": "Top N productos", "required": False},
        ],
    ),

    # ── CREDITOS ──
    "consultar_creditos": ToolDefinition(
        name="consultar_creditos",
        description="Consulta creditos pendientes de clientes: monto, vencimiento y estado.",
        category="finanzas",
        params=[
            {"name": "cliente_id", "type": "str", "description": "ID del cliente (opcional)", "required": False},
        ],
    ),

    # ── SISTEMA ──
    "config_sistema": ToolDefinition(
        name="config_sistema",
        description="Obtiene o modifica la configuracion del sistema: nombre del negocio, "
                    "impuesto, moneda, etc.",
        category="sistema",
        params=[
            {"name": "clave", "type": "str", "description": "Clave de configuracion", "required": False},
        ],
        requires_role="administrador",
    ),
    "health_check": ToolDefinition(
        name="health_check",
        description="Verifica el estado del sistema: base de datos, servidor, memoria.",
        category="sistema",
        params=[],
        requires_auth=False,
    ),
}


# ══════════════════════════════════════════════════════════
#  FUNCIONES DE CONSULTA
# ══════════════════════════════════════════════════════════

def get_tool(name: str) -> Optional[ToolDefinition]:
    """Obtiene una herramienta por nombre."""
    return TOOL_CATALOG.get(name)


def get_tools_by_category(category: str) -> List[ToolDefinition]:
    """Filtra herramientas por categoria."""
    return [t for t in TOOL_CATALOG.values() if t.category == category]


def get_all_tools() -> Dict[str, ToolDefinition]:
    """Retorna todo el catalogo."""
    return dict(TOOL_CATALOG)


def search_tools(query: str) -> List[ToolDefinition]:
    """Busca herramientas por texto en nombre o descripcion."""
    q = query.lower()
    results = []
    for tool in TOOL_CATALOG.values():
        if q in tool.name.lower() or q in tool.description.lower() or q in tool.category.lower():
            results.append(tool)
    return results


def get_tool_summary(tool: ToolDefinition) -> str:
    """Genera un resumen legible de una herramienta para el agente."""
    params_str = ", ".join(
        f"{p['name']}({p['type']})" + (" *" if p.get('required') else "")
        for p in tool.params
    )
    role = f" [rol: {tool.requires_role}]" if tool.requires_role else ""
    return f"- {tool.name}({params_str}): {tool.description}{role}"
