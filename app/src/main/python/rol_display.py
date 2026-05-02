"""
rol_display.py - Nombres de visualizacion para roles
Se inyecta en la app Flask para que la UI muestre "Usuario" en vez de "desarrollador"
"""

ROLES_DISPLAY = {
    "desarrollador": "Usuario",
    "administrador": "Administrador",
    "supervisor": "Supervisor",
    "vendedor": "Vendedor",
}

def rol_a_display(rol):
    return ROLES_DISPLAY.get(rol, rol)

def injectar_rol_display(app):
    @app.after_request
    def after(resp):
        return resp

    @app.route('/api/roles/nombres')
    def obtener_nombres_roles():
        import json
        return json.dumps(ROLES_DISPLAY), 200, {'Content-Type': 'application/json'}
