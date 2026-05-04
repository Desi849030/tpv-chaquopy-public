"""role_guidance.py - Matriz de Misiones por Rol"""
ROLE_MISSIONS = {
    "cliente": {
        "inicio": ["Bienvenido a TPV Smart. Puedo ayudarle a encontrar productos y precios."],
        "operativo": ["Tenemos ofertas especiales hoy. Escriba 'ofertas' para ver los descuentos."],
        "ayuda": ["Puede preguntarme: 'busco cafe', 'mejores ofertas', 'categorias'."]
    },
    "vendedor": {
        "inicio": ["Buenos dias. Revise el stock bajo antes de empezar a vender."],
        "operativo": ["Recuerde ofrecer los productos con mayor margen de ganancia."],
        "cierre": ["Turno terminado. Verifique su arqueo de caja."],
        "critico": ["ATENCION: Hay productos agotados. No los ofrezca al cliente."],
        "ayuda": ["Puedo ayudarle con: ventas, stock bajo, top productos, precios."]
    },
    "supervisor": {
        "inicio": ["Buenos dias. Revise el dashboard para ver el estado del equipo."],
        "operativo": ["Monitoree el rendimiento de los vendedores en tiempo real."],
        "cierre": ["Dia finalizado. Revise el resumen de ventas por vendedor."],
        "critico": ["ALERTA: Varios productos alcanzaron stock critico."],
        "ayuda": ["Puedo ayudarle con: dashboard, tendencias, inventario, predicciones."]
    },
    "administrador": {
        "inicio": ["Buenos dias. Revise las finanzas y el analisis ABC para empezar."],
        "operativo": ["Revise los margenes de ganancia y ajuste precios si es necesario."],
        "cierre": ["Balance final. Exporte los reportes para contabilidad."],
        "critico": ["ALERTA: Los gastos de hoy superan el promedio."],
        "ayuda": ["Puedo ayudarle con: finanzas, ABC, punto equilibrio, EOQ, rotacion, predicciones."]
    },
    "desarrollador": {
        "inicio": ["Acceso total activado. Todos los modulos y logs disponibles."],
        "operativo": ["Monitoree las conexiones a Supabase y el estado de los WebSockets."],
        "critico": ["ALERTA: Error en la sincronizacion con Supabase."],
        "ayuda": ["Acceso total. Puedo ayudarle con: debug, logs, Supabase, seguridad, API."]
    }
}
SCREEN_GUIDES = {
    "tpv-caja-tab-pane": "Punto de Venta. Escanee productos y procese el pago.",
    "dashboard-tab-pane": "Panel de Control. Vea el estado general del negocio.",
    "inv-inventario-tab-pane": "Control de Stock. Gestione existencias y reordenes.",
    "gestion-productos-tab-pane": "Catalogo. Cree productos y ajuste precios.",
    "conf-config-tab-pane": "Configuracion. Ajuste parametros del sistema.",
    "privilegios-tab-pane": "Privilegios. Asigne roles y permisos a empleados."
}
