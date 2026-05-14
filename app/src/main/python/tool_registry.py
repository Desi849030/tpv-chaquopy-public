from tools.base import ToolDefinition, _t
from typing import Dict, List, Optional

from tools.admin_tools import ADMIN_TOOLS
from tools.analytic_tools import ANALYTIC_TOOLS
from tools.auth_tools import AUTH_TOOLS
from tools.inventario_tools import INVENTARIO_TOOLS
from tools.venta_tools import VENTA_TOOLS
from tools.tienda_tools import TIENDA_TOOLS
from tools.licencia_tools import LICENCIA_TOOLS
from tools.lealtad_tools import LEALTAD_TOOLS
from tools.seguridad_tools import SEGURIDAD_TOOLS
from tools.security_tools import SECURITY_TOOLS
from tools.setting_tools import SETTING_TOOLS
from tools.validacion_tools import VALIDACION_TOOLS
from tools.ia_tools import IA_TOOLS
from tools.general_tools import GENERAL_TOOLS
from tools.import_tools import IMPORT_TOOLS

TOOL_CATALOG: Dict[str, ToolDefinition] = {}
TOOL_CATALOG.update(ADMIN_TOOLS)

TOOL_CATALOG.update(ANALYTIC_TOOLS)

TOOL_CATALOG.update(AUTH_TOOLS)

TOOL_CATALOG.update(INVENTARIO_TOOLS)

TOOL_CATALOG.update(VENTA_TOOLS)

TOOL_CATALOG.update(TIENDA_TOOLS)

TOOL_CATALOG.update(LICENCIA_TOOLS)

TOOL_CATALOG.update(LEALTAD_TOOLS)

TOOL_CATALOG.update(SEGURIDAD_TOOLS)

TOOL_CATALOG.update(SECURITY_TOOLS)

TOOL_CATALOG.update(SETTING_TOOLS)

TOOL_CATALOG.update(VALIDACION_TOOLS)

TOOL_CATALOG.update(IA_TOOLS)

TOOL_CATALOG.update(GENERAL_TOOLS)

TOOL_CATALOG.update(IMPORT_TOOLS)

# ══════════════════════════════════════════════
#  FUNCIONES DE CONSULTA
# ══════════════════════════════════════════════

def get_tool(name: str) -> Optional[ToolDefinition]:
    return TOOL_CATALOG.get(name)

def get_tools_by_category(category: str) -> List[ToolDefinition]:
    return [t for t in TOOL_CATALOG.values() if t.category == category]

def get_all_tools_by_category():
    """Retorna TODAS las herramientas agrupadas por categoria."""
    result = {}
    for tool in TOOL_CATALOG.values():
        result.setdefault(tool.category, []).append(tool)
    return result

def get_all_tools() -> Dict[str, ToolDefinition]:
    return dict(TOOL_CATALOG)

def search_tools(query: str) -> List[ToolDefinition]:
    q = query.lower()
    return [t for t in TOOL_CATALOG.values()
            if q in t.name.lower() or q in t.description.lower() or q in t.category.lower()]

def get_tool_summary(tool: ToolDefinition) -> str:
    params_str = ", ".join(
        f"{p['name']}" + ("*" if p.get("required") else "")
        for p in tool.params
    )
    role = f" [{tool.requires_role}]" if tool.requires_role else ""
    return f"- {tool.name}({params_str}): {tool.description}{role}"

def get_catalog_stats() -> Dict[str, int]:
    """Retorna estadisticas del catalogo."""
    cats = {}
    for t in TOOL_CATALOG.values():
        cats[t.category] = cats.get(t.category, 0) + 1
    return {"total": len(TOOL_CATALOG), "categories": cats}