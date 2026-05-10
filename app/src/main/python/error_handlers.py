"""error_handlers.py — Manejo centralizado de errores v2.3.0"""
import logging, traceback, functools
from flask import jsonify
from datetime import datetime

_log = logging.getLogger("tpv.errors")

class APIError(Exception):
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotFoundError(APIError):
    def __init__(self, resource="recurso"):
        super().__init__("%s no encontrado" % resource, 404)

class ValidationError(APIError):
    def __init__(self, message="Datos invalidos", details=None):
        super().__init__(message, 422, details)

class AuthError(APIError):
    def __init__(self, message="No autorizado"):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    def __init__(self, message="Acceso denegado"):
        super().__init__(message, 403)

def setup_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(e):
        _log.warning("APIError %s: %s" % (e.status_code, e.message))
        resp = {"error": True, "message": e.message, "status": e.status_code,
                "timestamp": datetime.now().isoformat()}
        if e.details:
            resp["details"] = e.details
        return jsonify(resp), e.status_code

    @app.errorhandler(400)
    def handle_400(e):
        return jsonify({"error": True, "message": "Peticion incorrecta", "status": 400}), 400

    @app.errorhandler(401)
    def handle_401(e):
        return jsonify({"error": True, "message": "No autorizado", "status": 401}), 401

    @app.errorhandler(403)
    def handle_403(e):
        return jsonify({"error": True, "message": "Acceso denegado", "status": 403}), 403

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": True, "message": "Ruta no encontrada", "status": 404}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": True, "message": "Metodo no permitido", "status": 405}), 405

    @app.errorhandler(500)
    def handle_500(e):
        _log.error("InternalServerError: %s" % traceback.format_exc())
        return jsonify({"error": True, "message": "Error interno", "status": 500}), 500

def api_response(success=True, message="", data=None, status=200):
    resp = {"success": success, "message": message, "timestamp": datetime.now().isoformat()}
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status

def validate_json(*required_fields):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request
            data = request.get_json(silent=True) or {}
            missing = [fld for fld in required_fields if fld not in data or not data[fld]]
            if missing:
                raise ValidationError("Campos requeridos: %s" % ", ".join(missing),
                                       {"missing": missing})
            return f(*args, **kwargs)
        return wrapper
    return decorator
