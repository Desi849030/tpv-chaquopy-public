"""
ia/error_formatter.py — Formato estructurado de errores.
Convierte excepciones en mensajes de usuario amigables
y logs técnicos detallados.

Inspirado en: free-code/src/utils/toolErrors.ts
"""

from __future__ import annotations
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Niveles de severidad del error."""
    LOW = "low"          # Informativo, no afecta operación
    MEDIUM = "medium"    # Operación falló pero se puede reintentar
    HIGH = "high"        # Error que afecta múltiples funciones
    CRITICAL = "critical"  # Error del sistema


class ErrorCategory(Enum):
    """Categorías de error."""
    DATABASE = "database"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


# Mapeo de excepciones conocidas a categorías y mensajes amigables
EXCEPTION_MAP = {
    "OperationalError": (
        ErrorCategory.DATABASE,
        "Error en la base de datos. Intenta nuevamente en unos segundos.",
        ErrorSeverity.HIGH,
    ),
    "IntegrityError": (
        ErrorCategory.DATABASE,
        "No se pudo guardar porque los datos ya existen o son inconsistentes.",
        ErrorSeverity.MEDIUM,
    ),
    "ValueError": (
        ErrorCategory.VALIDATION,
        "El valor proporcionado no es válido. Verifica los datos e intenta de nuevo.",
        ErrorSeverity.LOW,
    ),
    "KeyError": (
        ErrorCategory.NOT_FOUND,
        "No se encontró la información solicitada.",
        ErrorSeverity.MEDIUM,
    ),
    "IndexError": (
        ErrorCategory.NOT_FOUND,
        "No se encontró el elemento buscado.",
        ErrorSeverity.MEDIUM,
    ),
    "TypeError": (
        ErrorCategory.VALIDATION,
        "Error en el tipo de datos. Contacta soporte si persiste.",
        ErrorSeverity.MEDIUM,
    ),
    "AttributeError": (
        ErrorCategory.UNKNOWN,
        "Error interno del asistente. Intenta reformular tu consulta.",
        ErrorSeverity.MEDIUM,
    ),
    "PermissionError": (
        ErrorCategory.PERMISSION,
        "No tienes permisos para realizar esa acción.",
        ErrorSeverity.HIGH,
    ),
}


@dataclass
class FormattedError:
    """Error formateado con información para usuario y para debug."""
    user_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    technical_details: str
    exception_type: str = ""
    context: dict | None = None
    suggestion: str = ""
    can_retry: bool = True

    def to_user_string(self) -> str:
        """Representación para el usuario final."""
        parts = [self.user_message]
        if self.suggestion:
            parts.append(f"\nSugerencia: {self.suggestion}")
        return "\n".join(parts)

    def to_log_dict(self) -> dict:
        """Representación para logs técnicos."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "exception": self.exception_type,
            "user_message": self.user_message,
            "technical": self.technical_details,
            "context": self.context,
            "can_retry": self.can_retry,
        }


class ErrorFormatter:
    """
    Formateador de errores para el agente TPV.

    Uso:
        formatter = ErrorFormatter()
        try:
            db_utils.q("SELECT * FROM nonexistent")
        except Exception as e:
            fmt = formatter.format(e, context={"query": "...", "role": "vendedor"})
            print(fmt.to_user_string())  # Mensaje para el usuario
            logger.error(fmt.to_log_dict())  # Log técnico
    """

    def __init__(self, include_traceback: bool = True):
        self.include_traceback = include_traceback
        self._custom_mappings: dict[str, tuple] = {}

    def register_exception(
        self,
        exception_type: str,
        category: ErrorCategory,
        user_message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> None:
        """Registra un mapeo personalizado de excepción."""
        self._custom_mappings[exception_type] = (category, user_message, severity)

    def format(
        self,
        error: Exception,
        context: dict | None = None,
        fallback_message: str = "Ocurrió un error inesperado. Intenta de nuevo.",
    ) -> FormattedError:
        """
        Formatea una excepción en un StructuredError.

        Args:
            error: La excepción capturada.
            context: Contexto adicional (query, role, etc).
            fallback_message: Mensaje por defecto si no se reconoce la excepción.

        Returns:
            FormattedError con información para usuario y debug.
        """
        exc_name = type(error).__name__
        exc_msg = str(error)

        # Buscar en mapeos personalizados primero
        if exc_name in self._custom_mappings:
            category, user_msg, severity = self._custom_mappings[exc_name]
            return self._build(error, user_msg, category, severity, context)

        # Buscar en mapeos predefinidos
        if exc_name in EXCEPTION_MAP:
            category, user_msg, severity = EXCEPTION_MAP[exc_name]
            # Enriquecer con detalles específicos del error
            enriched_msg = self._enrich_message(user_msg, exc_msg, category)
            return self._build(error, enriched_msg, category, severity, context)

        # Fallback: error desconocido
        return self._build(
            error,
            fallback_message,
            ErrorCategory.UNKNOWN,
            ErrorSeverity.MEDIUM,
            context,
        )

    def format_simple(self, error: Exception) -> str:
        """Versión simplificada: devuelve solo el mensaje de usuario."""
        return self.format(error).to_user_string()

    def _build(
        self,
        error: Exception,
        user_message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: dict | None,
    ) -> FormattedError:
        """Construye un FormattedError."""
        tb_str = ""
        if self.include_traceback:
            tb_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        # Generar sugerencia basada en categoría
        suggestion = self._get_suggestion(category)

        # Determinar si se puede reintentar
        can_retry = severity in (ErrorSeverity.LOW, ErrorSeverity.MEDIUM)

        return FormattedError(
            user_message=user_message,
            severity=severity,
            category=category,
            technical_details=tb_str or str(error),
            exception_type=type(error).__name__,
            context=context,
            suggestion=suggestion,
            can_retry=can_retry,
        )

    def _enrich_message(self, base_msg: str, exc_msg: str, category: ErrorCategory) -> str:
        """Enriquece el mensaje base con detalles del error."""
        if category == ErrorCategory.DATABASE:
            if "no such table" in exc_msg.lower():
                return f"{base_msg}\nDetalle: La tabla solicitada no existe en el sistema."
            if " UNIQUE constraint" in exc_msg:
                return f"{base_msg}\nDetalle: Ya existe un registro con estos datos."
            if "foreign key" in exc_msg.lower():
                return f"{base_msg}\nDetalle: Referencia a un dato que no existe."
        elif category == ErrorCategory.VALIDATION:
            if exc_msg:
                return f"{base_msg}\nDetalle: {exc_msg}"
        return base_msg

    def _get_suggestion(self, category: ErrorCategory) -> str:
        """Genera sugerencia según categoría."""
        suggestions = {
            ErrorCategory.DATABASE: "Si el problema persiste, verifica que la base de datos esté operativa.",
            ErrorCategory.VALIDATION: "Revisa que los datos ingresados sean correctos (números, nombres, fechas).",
            ErrorCategory.NOT_FOUND: "Intenta buscar con otro nombre o verifica el identificador.",
            ErrorCategory.PERMISSION: "Contacta al administrador si necesitas acceso a esta función.",
            ErrorCategory.TIMEOUT: "La operación tardó demasiado. Intenta con una consulta más específica.",
            ErrorCategory.UNKNOWN: "Si el error persiste, contacta al administrador del sistema.",
        }
        return suggestions.get(category, "")


# Singleton
_formatter: ErrorFormatter | None = None


def get_error_formatter() -> ErrorFormatter:
    """Devuelve el formatter singleton."""
    global _formatter
    if _formatter is None:
        _formatter = ErrorFormatter()
    return _formatter
