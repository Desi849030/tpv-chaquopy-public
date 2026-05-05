# -*- coding: utf-8 -*-
"""ia/tool_system.py - Sistema de herramientas con permisos por rol
Cataloga las capacidades del IA y sugiere herramientas relevantes.
100% offline, sin dependencias externas."""

TOOLS = {
    'finanzas': {
        'desc': 'Balance del dia: ingresos, gastos, ganancia, margen, comision',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['finanza', 'margen', 'gasto', 'ingreso', 'balance', 'ganancia', 'comision', 'rentabilidad'],
        'icon': '💰',
    },
    'abc': {
        'desc': 'Analisis ABC/Pareto de productos por ingresos',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['abc', 'pareto', 'clasificacion'],
        'icon': '📊',
    },
    'punto_equilibrio': {
        'desc': 'Calculo de punto de equilibrio diario',
        'roles': ['desarrollador', 'administrador'],
        'keywords': ['punto equilibrio', 'break even', 'umbral'],
        'icon': '⚖️',
    },
    'stock': {
        'desc': 'Estado de inventario: stock bajo, agotados, criticos',
        'roles': ['desarrollador', 'administrador', 'supervisor', 'vendedor'],
        'keywords': ['stock', 'inventario', 'critico', 'agotado', 'bajo'],
        'icon': '📦',
    },
    'predicciones': {
        'desc': 'Pronostico de ventas basado en tendencia de 7 dias',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['prediccion', 'pronostico', 'proyeccion', 'forecast', 'tendencia'],
        'icon': '🔮',
    },
    'ofertas': {
        'desc': 'Productos ideales para descuentos segun margen',
        'roles': ['desarrollador', 'administrador', 'vendedor'],
        'keywords': ['oferta', 'descuento', 'rebaja', 'promocion'],
        'icon': '🏷️',
    },
    'rotacion': {
        'desc': 'Indice de rotacion de inventario (30 dias)',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['rotacion', 'indice rotacion'],
        'icon': '🔄',
    },
    'gastos': {
        'desc': 'Listado de gastos del dia con totales por categoria',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['gasto', 'egreso', 'costo fijo'],
        'icon': '🧾',
    },
    'eoq': {
        'desc': 'Lote optimo de pedido (EOQ) para productos top',
        'roles': ['desarrollador', 'administrador'],
        'keywords': ['eoq', 'lote optimo', 'pedido optimo'],
        'icon': '📐',
    },
    'ventas_hoy': {
        'desc': 'Resumen de ventas del dia actual',
        'roles': ['desarrollador', 'administrador', 'supervisor', 'vendedor'],
        'keywords': ['ventas de hoy', 'ventas hoy', 'resumen ventas', 'cuanto vendido'],
        'icon': '🛒',
    },
    'top_productos': {
        'desc': 'Productos mas vendidos en un periodo',
        'roles': ['desarrollador', 'administrador', 'supervisor', 'vendedor'],
        'keywords': ['top', 'mas vendido', 'vendido', 'popular', 'ranking'],
        'icon': '🏆',
    },
    'dashboard': {
        'desc': 'Panel KPIs: ventas, productos, stock bajo, categorias',
        'roles': ['desarrollador', 'administrador', 'supervisor'],
        'keywords': ['dashboard', 'resumen', 'estado', 'kpi', 'panel'],
        'icon': '📋',
    },
    'busqueda': {
        'desc': 'Buscar productos por nombre y ver precio, stock, margen',
        'roles': ['desarrollador', 'administrador', 'supervisor', 'vendedor', 'cliente'],
        'keywords': ['buscar', 'buscar producto', 'busco', 'precio de', 'cuanto cuesta'],
        'icon': '🔍',
    },
}


def get_tools_for_role(role):
    """Devuelve herramientas disponibles para un rol."""
    return {k: v for k, v in TOOLS.items() if role in v['roles']}


def suggest_tools(text, role='cliente'):
    """Sugiere herramientas relevantes basadas en el texto del usuario."""
    t = text.lower().strip()
    if not t or len(t) < 2:
        return []
    results = []
    for name, tool in TOOLS.items():
        if role not in tool['roles']:
            continue
        score = sum(1 for kw in tool['keywords'] if kw in t)
        if score > 0:
            results.append((name, tool, score))
    results.sort(key=lambda x: x[2], reverse=True)
    return [{'name': r[0], 'desc': r[1]['desc'], 'icon': r[1]['icon'],
             'relevance': r[2]} for r in results[:3]]


def get_help_menu(role='cliente'):
    """Genera menu de ayuda contextual por rol."""
    tools = get_tools_for_role(role)
    if not tools:
        return "No hay herramientas disponibles para su rol."
    lines = ["Herramientas disponibles:\n"]
    for name, tool in tools.items():
        lines.append(f"{tool['icon']} {tool['desc']}")
    lines.append("\nEscriba el nombre de la herramienta o pregunte directamente.")
    return '\n'.join(lines)


def check_permission(tool_name, role):
    """Verifica si un rol tiene acceso a una herramienta."""
    tool = TOOLS.get(tool_name)
    if not tool:
        return False
    return role in tool['roles']
