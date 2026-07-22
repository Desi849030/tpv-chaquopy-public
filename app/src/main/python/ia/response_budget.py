"""
ia/response_budget.py — Gestión de longitud de respuesta.
Evita respuestas demasiado largas o cortas, optimizando
la comunicación con el usuario.

Inspirado en: free-code/src/utils/tokenBudget.ts
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class BudgetMode(Enum):
    """Modos de presupuesto de respuesta."""
    CONCISE = "concise"        # Respuestas breves y directas
    NORMAL = "normal"          # Balance entre detalle y brevedad
    DETAILED = "detailed"      # Respuestas con máximo detalle
    EXHAUSTIVE = "exhaustive"  # Desarrollador: informes extensos y verificables


@dataclass
class BudgetConfig:
    """Configuración de presupuesto por modo."""
    mode: BudgetMode
    max_chars: int
    max_lines: int
    min_chars: int
    truncation_suffix: str = "\n..."
    ellipsis_if_long: bool = True


# Configuraciones predefinidas
BUDGET_CONFIGS = {
    BudgetMode.CONCISE: BudgetConfig(
        mode=BudgetMode.CONCISE,
        max_chars=200,
        max_lines=5,
        min_chars=20,
        truncation_suffix="",
    ),
    BudgetMode.NORMAL: BudgetConfig(
        mode=BudgetMode.NORMAL,
        max_chars=600,
        max_lines=15,
        min_chars=30,
        truncation_suffix="\n...",
    ),
    BudgetMode.DETAILED: BudgetConfig(
        mode=BudgetMode.DETAILED,
        max_chars=1500,
        max_lines=40,
        min_chars=50,
        truncation_suffix="\n[respuesta truncada]",
    ),
    BudgetMode.EXHAUSTIVE: BudgetConfig(
        mode=BudgetMode.EXHAUSTIVE,
        max_chars=12000,
        max_lines=300,
        min_chars=50,
        truncation_suffix="\n[continúa con: siguiente]",
    ),
}


class ResponseBudget:
    """
    Gestor de presupuesto de respuesta.

    Uso:
        budget = ResponseBudget()

        # Aplicar a una respuesta
        result = budget.apply("Texto muy largo...", mode=BudgetMode.CONCISE)

        # O con config custom
        result = budget.apply(text, max_chars=300, max_lines=8)
    """

    def __init__(self, default_mode: BudgetMode = BudgetMode.NORMAL):
        self.default_mode = default_mode
        self._stats = {
            "total_processed": 0,
            "truncated": 0,
            "expanded": 0,
            "passed": 0,
        }

    def apply(
        self,
        text: str,
        mode: BudgetMode | None = None,
        max_chars: int | None = None,
        max_lines: int | None = None,
        min_chars: int | None = None,
    ) -> str:
        """
        Aplica el presupuesto a una respuesta.

        Args:
            text: Texto de la respuesta.
            mode: Modo de presupuesto (usa default si None).
            max_chars: Override de caracteres máximos.
            max_lines: Override de líneas máximas.
            min_chars: Override de caracteres mínimos.

        Returns:
            Texto ajustado al presupuesto.
        """
        if not text:
            return text

        self._stats["total_processed"] += 1
        mode = mode or self.default_mode
        config = BUDGET_CONFIGS[mode]

        # Aplicar overrides
        mc = max_chars if max_chars is not None else config.max_chars
        ml = max_lines if max_lines is not None else config.max_lines
        min_c = min_chars if min_chars is not None else config.min_chars

        result = text

        # Truncar si es muy largo
        if len(result) > mc:
            result = self._smart_truncate(result, mc, ml, config.truncation_suffix)
            self._stats["truncated"] += 1

        # Expandir si es muy corto
        elif len(result.strip()) < min_c:
            result = self._expand_short(result, min_c)
            self._stats["expanded"] += 1
        else:
            self._stats["passed"] += 1

        return result

    def _smart_truncate(
        self,
        text: str,
        max_chars: int,
        max_lines: int,
        suffix: str,
    ) -> str:
        """
        Trunca inteligentemente: corta en la última oración/palabra completa.
        """
        # Primero verificar líneas
        lines = text.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            text = "\n".join(lines)

        # Si aún es muy largo, truncar por caracteres
        if len(text) <= max_chars:
            return text

        # Buscar el último punto/punto y coma/coma antes del límite
        cut_point = max_chars - len(suffix)
        # Asegurar que cut_point no sea negativo
        cut_point = max(cut_point, 0)

        # Buscar separador de oración más cercano al punto de corte
        best_cut = -1
        for separator in [". ", ".", "; ", ",", " "]:
            pos = text.rfind(separator, 0, cut_point)
            if pos > best_cut:
                best_cut = pos

        if best_cut > 0:
            truncated = text[:best_cut + 1].rstrip()
        else:
            truncated = text[:cut_point].rstrip()

        # Evitar cortar palabras a la mitad
        if truncated and not truncated[-1] in ".;,!?: ":
            last_space = truncated.rfind(" ")
            if last_space > len(truncated) * 0.5:  # No retroceder demasiado
                truncated = truncated[:last_space]

        return truncated + suffix

    def _expand_short(self, text: str, min_chars: int) -> str:
        """
        Expande respuestas muy cortas con contexto adicional.
        """
        text = text.strip()
        if not text:
            return "Entendido."

        # Si es una sola palabra o muy corta, añadir contexto
        words = text.split()
        if len(words) <= 3:
            # Afirmaciones simples
            lower = text.lower()
            if lower in ("sí", "si", "yes", "ok", "vale", "bien", "claro", "perfecto"):
                return "Entendido, puedo ayudarte con algo más."
            if lower in ("no", "nop", "nope"):
                return "De acuerdo, dime si necesitas algo más."
            if lower in ("gracias", "thanks", "gracias!"):
                return "De nada, estoy aquí para ayudarte."

        # Si necesita más longitud, intentar añadir una pregunta adicional
        if len(text) < min_chars:
            suggestions = [
                " ¿Necesitas algo más?",
                " ¿Puedo ayudarte con otra consulta?",
                " ¿Deseas realizar alguna otra operación?",
            ]
            for suggestion in suggestions:
                if len(text + suggestion) <= min_chars + 20:
                    return text + suggestion

        return text

    def get_stats(self) -> dict:
        """Estadísticas del budget."""
        total = self._stats["total_processed"]
        return {
            "total_processed": total,
            "truncated": self._stats["truncated"],
            "expanded": self._stats["expanded"],
            "passed": self._stats["passed"],
            "truncation_rate": round(self._stats["truncated"] / total * 100, 1) if total > 0 else 0,
        }


# Singleton
_budget: ResponseBudget | None = None


def get_budget() -> ResponseBudget:
    """Devuelve el budget singleton."""
    global _budget
    if _budget is None:
        _budget = ResponseBudget()
    return _budget


def reset_budget() -> None:
    """Resetea el budget (útil para tests)."""
    global _budget
    _budget = ResponseBudget()
