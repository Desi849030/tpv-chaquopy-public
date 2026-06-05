PREDEFINED_PLANS = {
    "optimizar_inventario": {
        "description": "Analiza stock bajo y sugiere reorden",
        "steps": [
            {"action": "search_and_call", "query": "inventario alerta stock", "purpose": "Alertas de stock bajo"},
            {"action": "search_and_call", "query": "analytics vendido", "purpose": "Productos mas vendidos"},
            {"action": "search_and_call", "query": "inventario producto listar", "purpose": "Inventario actual"},
            {"action": "compile_response", "template": "inventory_optimization"},
        ],
    },
    "cierre_fin_semana": {
        "description": "Resumen financiero para cierre de caja",
        "steps": [
            {"action": "search_and_call", "query": "ventas resumen total", "purpose": "Resumen de ventas"},
            {"action": "search_and_call", "query": "analytics estadistica", "purpose": "Estadisticas"},
            {"action": "search_and_call", "query": "finanza reporte", "purpose": "Reporte financiero"},
            {"action": "compile_response", "template": "closing_summary"},
        ],
    },
    "diagnostico_negocio": {
        "description": "Diagnostico completo del negocio",
        "steps": [
            {"action": "search_and_call", "query": "analytics", "purpose": "Metricas de negocio"},
            {"action": "search_and_call", "query": "inventario", "purpose": "Estado inventario"},
            {"action": "search_and_call", "query": "ventas", "purpose": "Actividad ventas"},
            {"action": "search_and_call", "query": "cliente", "purpose": "Base de clientes"},
            {"action": "compile_response", "template": "business_diagnosis"},
        ],
    },
    "status_clientes": {
        "description": "Reporte de clientes y lealtad",
        "steps": [
            {"action": "search_and_call", "query": "cliente listar", "purpose": "Lista de clientes"},
            {"action": "search_and_call", "query": "lealtad puntos", "purpose": "Puntos de lealtad"},
            {"action": "search_and_call", "query": "analytics cliente", "purpose": "Metricas clientes"},
            {"action": "compile_response", "template": "client_status"},
        ],
    },
    "auditoria_seguridad": {
        "description": "Revision de logs y politicas de seguridad",
        "steps": [
            {"action": "search_and_call", "query": "seguridad auditoria log", "purpose": "Logs de auditoria"},
            {"action": "search_and_call", "query": "admin usuario", "purpose": "Usuarios del sistema"},
            {"action": "search_and_call", "query": "seguridad politica", "purpose": "Politicas seguridad"},
            {"action": "compile_response", "template": "security_audit"},
        ],
    },
    "reporte_ventas_periodo": {
        "description": "Reporte de ventas para un periodo",
        "steps": [
            {"action": "search_and_call", "query": "ventas historial", "purpose": "Historial ventas"},
            {"action": "search_and_call", "query": "analytics producto", "purpose": "Mas vendidos"},
            {"action": "search_and_call", "query": "analytics estadistica", "purpose": "Estadisticas"},
            {"action": "compile_response", "template": "sales_report"},
        ],
    },
}