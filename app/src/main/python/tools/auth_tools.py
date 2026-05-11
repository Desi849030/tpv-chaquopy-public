from tools.base import _t

AUTH_TOOLS = {
    "login": _t("login",
        "Inicia sesion con username y password",
        "auth", "/api/auth/login", "POST",
        [{"name": "username", "type": "str", "description": "Usuario", "required": True},
         {"name": "password", "type": "str", "description": "Contrasena", "required": True}],
        auth=False),
    "logout": _t("logout",
        "Cierra la sesion actual del usuario",
        "auth", "/api/auth/logout", "POST", []),
    "auth_me": _t("auth_me",
        "Obtiene informacion del usuario autenticado actual",
        "auth", "/api/auth/me", "GET", []),
    "cambiar_password": _t("cambiar_password",
        "Cambia la contrasena del usuario actual",
        "auth", "/api/auth/cambiar-password", "POST",
        [{"name": "password_actual", "type": "str", "description": "Contrasena actual", "required": True},
         {"name": "password_nueva", "type": "str", "description": "Nueva contrasena", "required": True}]),
    "auto_backup": _t("auto_backup",
        "Guarda backup automatico y sincroniza con Supabase si esta disponible",
        "auth", "/api/auth/auto-backup", "POST", []),
}
