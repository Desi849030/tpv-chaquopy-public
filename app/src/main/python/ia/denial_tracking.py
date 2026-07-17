"""
ia/denial_tracking.py — Tracking de fallos consecutivos para recuperación.
Cuenta fallos seguidos y activa estrategias de recuperación.

Inspirado en: free-code/src/utils/permissions/denialTracking.ts
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
import time


@dataclass
class DenialState:
    """Estado del tracking de fallos."""
    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_failure_time: float = 0.0
    last_failure_reason: str = ""
    last_success_time: float = 0.0
    recovery_mode: bool = False
    recovery_attempt: int = 0
    failure_history: list[dict] = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        total = self.total_failures + self.total_successes
        return (self.total_failures / total * 100) if total > 0 else 0.0

    @property
    def is_stuck(self) -> bool:
        """True si hay 3+ fallos consecutivos."""
        return self.consecutive_failures >= 3

    @property
    def should_escalate(self) -> bool:
        """True si hay 5+ fallos consecutivos (necesita intervención)."""
        return self.consecutive_failures >= 5


@dataclass
class RecoveryAction:
    """Acción de recuperación definida."""
    name: str
    handler: Callable
    max_attempts: int = 3
    trigger_at_failures: int = 3


class DenialTracker:
    """
    Tracker de fallos con recuperación automática.

    Uso:
        tracker = DenialTracker()
        tracker.register_recovery("sugerir_reformular",
            trigger_at=3, max_attempts=3,
            handler=lambda ctx: "¿Podrías reformular tu pregunta?")
        tracker.record_success()
        tracker.record_failure("No encontré el producto")
        if tracker.state.is_stuck:
            recovery = tracker.get_recovery_action(ctx)
    """

    # Mensajes de recuperación por defecto según nivel
    DEFAULT_RECOVERY_MESSAGES = {
        3: "No estoy logrando entender tu solicitud. ¿Podrías reformularla de otra manera?",
        4: "Llevo varios intentos sin éxito. Si me das más detalles, como el nombre del producto o el número de mesa, puedo ayudarte mejor.",
        5: "No he podido procesar tu solicitud. Te sugiero consultar el menú de ayuda o contactar al administrador.",
    }

    def __init__(self, max_history: int = 50):
        self.state = DenialState()
        self._recovery_actions: list[RecoveryAction] = []
        self._custom_messages: dict[int, str] = {}
        self.max_history = max_history

    def register_recovery(
        self,
        name: str,
        handler: Callable,
        trigger_at: int = 3,
        max_attempts: int = 3,
    ) -> None:
        """Registra una acción de recuperación personalizada."""
        self._recovery_actions.append(RecoveryAction(
            name=name,
            handler=handler,
            max_attempts=max_attempts,
            trigger_at_failures=trigger_at,
        ))

    def set_recovery_message(self, at_failures: int, message: str) -> None:
        """Sobreescribe el mensaje de recuperación para un nivel."""
        self._custom_messages[at_failures] = message

    def record_success(self) -> DenialState:
        """Registra un éxito y resetea contadores consecutivos."""
        self.state.consecutive_failures = 0
        self.state.recovery_mode = False
        self.state.recovery_attempt = 0
        self.state.total_successes += 1
        self.state.last_success_time = time.time()
        return self.state

    def record_failure(self, reason: str = "") -> DenialState:
        """Registra un fallo y actualiza estado."""
        self.state.consecutive_failures += 1
        self.state.total_failures += 1
        self.state.last_failure_time = time.time()
        self.state.last_failure_reason = reason

        # Guardar en historial
        self.state.failure_history.append({
            "reason": reason,
            "time": time.time(),
            "consecutive": self.state.consecutive_failures,
        })
        if len(self.state.failure_history) > self.max_history:
            self.state.failure_history = self.state.failure_history[-self.max_history:]

        # Activar recovery mode si corresponde
        if self.state.is_stuck and not self.state.recovery_mode:
            self.state.recovery_mode = True

        return self.state

    def get_recovery_message(self) -> str | None:
        """
        Devuelve el mensaje de recuperación apropiado según el nivel de fallos.

        Returns:
            Mensaje de recuperación o None si no aplica.
        """
        failures = self.state.consecutive_failures
        if failures < 3:
            return None

        # Buscar mensaje personalizado
        for level in sorted(self._custom_messages.keys(), reverse=True):
            if failures >= level:
                return self._custom_messages[level]

        # Buscar en mensajes por defecto
        for level in sorted(self.DEFAULT_RECOVERY_MESSAGES.keys(), reverse=True):
            if failures >= level:
                return self.DEFAULT_RECOVERY_MESSAGES[level]

        return self.DEFAULT_RECOVERY_MESSAGES.get(5, self.DEFAULT_RECOVERY_MESSAGES[3])

    def get_recovery_action(self, context: Any = None) -> str | None:
        """
        Ejecuta la primera acción de recuperación aplicable.

        Returns:
            Resultado de la acción o None si no hay acciones disponibles.
        """
        if not self.state.recovery_mode:
            return None

        for action in self._recovery_actions:
            if (self.state.consecutive_failures >= action.trigger_at_failures
                    and self.state.recovery_attempt < action.max_attempts):
                self.state.recovery_attempt += 1
                try:
                    result = action.handler(context)
                    return str(result) if result else None
                except Exception:
                    continue

        return self.get_recovery_message()

    def should_suggest_alternative(self) -> bool:
        """True si debe sugerir alternativas (2+ fallos)."""
        return self.state.consecutive_failures >= 2

    def reset(self) -> None:
        """Resetea completamente el estado."""
        self.state = DenialState()

    def get_summary(self) -> dict:
        """Resumen del estado actual."""
        return {
            "consecutive_failures": self.state.consecutive_failures,
            "total_failures": self.state.total_failures,
            "total_successes": self.state.total_successes,
            "failure_rate": round(self.state.failure_rate, 1),
            "is_stuck": self.state.is_stuck,
            "should_escalate": self.state.should_escalate,
            "recovery_mode": self.state.recovery_mode,
            "last_failure_reason": self.state.last_failure_reason,
            "available_recoveries": len(self._recovery_actions),
        }


# Singleton
_tracker: DenialTracker | None = None


def get_tracker() -> DenialTracker:
    """Devuelve el tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = DenialTracker()
    return _tracker


def reset_tracker() -> None:
    """Resetea el tracker (útil para tests)."""
    global _tracker
    _tracker = DenialTracker()
