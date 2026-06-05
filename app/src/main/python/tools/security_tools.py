from tools.base import _t

SECURITY_TOOLS = {
    "ws_events": _t("ws_events",
        "Eventos WebSocket para terminal ID especifico",
        "websocket", "/ws/events/<tid>", "GET",
        [{"name": "tid", "type": "str", "description": "Terminal ID", "required": True}]),
    "ws_list": _t("ws_list",
        "Lista terminales WebSocket conectadas",
        "websocket", "/ws/terminals", "GET", []),
    "ws_register": _t("ws_register",
        "Registra un terminal WebSocket",
        "websocket", "/ws/register", "POST",
        [{"name": "terminal_id", "type": "str", "description": "ID del terminal", "required": True}]),
    "ws_unregister": _t("ws_unregister",
        "Desregistra un terminal WebSocket",
        "websocket", "/ws/unregister", "POST",
        [{"name": "terminal_id", "type": "str", "description": "ID del terminal", "required": True}]),
}
