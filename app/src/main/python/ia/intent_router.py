"""
ia/intent_router.py — Router de intenciones por scoring.
Reemplaza el patrón _fm(agent, t, ['kw1','kw2']) con un sistema
de scoring que evalúa todas las intenciones registradas y devuelve
la mejor coincidencia por puntuación.

Inspirado en: free-code/src/utils/toolSearch.ts
"""

from __future__ import annotations
import re
import math
from dataclasses import dataclass, field
from typing import Callable, Any, Optional


@dataclass
class IntentMatch:
    """Resultado del match de una intención."""
    name: str
    score: float
    handler: Callable
    matched_keywords: list[str] = field(default_factory=list)
    confidence: str = ""  # "high" | "medium" | "low" | "none"

    def __post_init__(self):
        if self.score >= 0.8:
            self.confidence = "high"
        elif self.score >= 0.5:
            self.confidence = "medium"
        elif self.score >= 0.25:
            self.confidence = "low"
        else:
            self.confidence = "none"


@dataclass
class IntentDefinition:
    """Definición de una intención registrable."""
    name: str
    keywords: list[str]
    patterns: list[str]  # regex patterns
    handler: Callable
    priority: float = 1.0
    description: str = ""
    required_role: Optional[str] = None  # "dev", "vendedor", "cliente", "cajero"


class IntentRouter:
    """
    Router de intenciones con scoring multi-criterio.

    Reemplaza el patrón:
        if _fm(agent, t, ['palabra1', 'palabra2']):
            ...
        elif _fm(agent, t, ['otra']):
            ...

    Con:
        router = IntentRouter()
        router.register("consultar_stock", keywords=["stock","inventario","cantidad"],
                        patterns=[r"cu[áa]nto.*stock", r"hay.*disponible"],
                        handler=fn_consultar_stock, priority=1.0)
        match = router.route(text, role="vendedor")
        if match:
            result = match.handler(agent, text, match)
    """

    def __init__(self):
        self._intents: list[IntentDefinition] = []
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        self._stats = {"calls": 0, "hits": 0, "misses": 0, "top_intent": ""}

    def register(
        self,
        name: str,
        keywords: list[str] | None = None,
        patterns: list[str] | None = None,
        handler: Callable | None = None,
        priority: float = 1.0,
        description: str = "",
        required_role: str | None = None,
    ) -> None:
        """Registra una intención en el router."""
        keywords = keywords or []
        patterns = patterns or []
        intent = IntentDefinition(
            name=name,
            keywords=keywords,
            patterns=patterns,
            handler=handler,
            priority=priority,
            description=description,
            required_role=required_role,
        )
        self._intents.append(intent)
        # Pre-compilar regex patterns
        compiled = []
        for p in patterns:
            try:
                compiled.append(re.compile(p, re.IGNORECASE | re.DOTALL))
            except re.error:
                pass
        self._compiled_patterns[name] = compiled

    def _score_keywords(self, text: str, keywords: list[str]) -> tuple[float, list[str]]:
        """Calcula score basado en coincidencia de keywords.
        Score: cuenta de keywords encontradas / total keywords,
        penalizado por distancia si hay muchos keywords y pocos matchean.
        """
        if not keywords:
            return 0.0, []
        text_lower = text.lower()
        matched = [kw for kw in keywords if kw.lower() in text_lower]
        if not matched:
            return 0.0, []
        # Base score: fracción de keywords encontrados
        base = len(matched) / len(keywords)
        # Bonus por densidad: si todos los keywords matchean en un texto corto
        word_count = len(text_lower.split())
        density_bonus = min(len(matched) / max(word_count, 1), 0.2)
        # Bonus por posición temprana (primeras 30 palabras)
        early_words = " ".join(text_lower.split()[:30])
        early_matches = sum(1 for kw in matched if kw.lower() in early_words)
        position_bonus = 0.1 * (early_matches / len(matched)) if matched else 0.0
        score = min(base + density_bonus + position_bonus, 1.0)
        return score, matched

    def _score_patterns(self, text: str, patterns: list[re.Pattern]) -> float:
        """Calcula score basado en coincidencia de regex patterns."""
        if not patterns:
            return 0.0
        match_count = sum(1 for p in patterns if p.search(text))
        if match_count == 0:
            return 0.0
        # Un pattern match vale más que keywords por ser más específico
        base = 0.7 * (match_count / len(patterns))
        length_bonus = min(0.3 * match_count, 0.3)
        return min(base + length_bonus, 1.0)

    def route(
        self,
        text: str,
        role: str | None = None,
        min_score: float = 0.15,
        context: dict | None = None,
    ) -> IntentMatch | None:
        """
        Evalúa todas las intenciones y devuelve la mejor coincidencia.

        Args:
            text: Texto del usuario.
            role: Rol actual (filtra intenciones con required_role).
            min_score: Score mínimo para considerar un match.
            context: Contexto adicional (ej: conversation_history).

        Returns:
            IntentMatch con la mejor coincidencia, o None.
        """
        self._stats["calls"] += 1
        if not text or not text.strip():
            self._stats["misses"] += 1
            return None

        best_match: IntentMatch | None = None
        best_score = min_score

        for intent in self._intents:
            # Filtrar por rol
            if intent.required_role and intent.required_role != role:
                continue

            # Calcular scores
            kw_score, matched_kws = self._score_keywords(text, intent.keywords)
            pat_score = self._score_patterns(text, self._compiled_patterns.get(intent.name, []))

            # Score combinado: patterns valen más que keywords
            combined = max(kw_score, pat_score)
            if kw_score > 0 and pat_score > 0:
                combined = min(kw_score * 0.4 + pat_score * 0.6 + 0.1, 1.0)

            # Aplicar prioridad
            final_score = combined * intent.priority

            if final_score > best_score:
                best_score = final_score
                best_match = IntentMatch(
                    name=intent.name,
                    score=final_score,
                    handler=intent.handler,
                    matched_keywords=matched_kws,
                )

        if best_match:
            self._stats["hits"] += 1
            self._stats["top_intent"] = best_match.name
        else:
            self._stats["misses"] += 1

        return best_match

    def route_multi(
        self,
        text: str,
        role: str | None = None,
        min_score: float = 0.15,
        max_results: int = 3,
    ) -> list[IntentMatch]:
        """Devuelve hasta max_results coincidencias ordenadas por score."""
        self._stats["calls"] += 1
        if not text or not text.strip():
            return []

        candidates: list[IntentMatch] = []
        for intent in self._intents:
            if intent.required_role and intent.required_role != role:
                continue
            kw_score, matched_kws = self._score_keywords(text, intent.keywords)
            pat_score = self._score_patterns(text, self._compiled_patterns.get(intent.name, []))
            combined = max(kw_score, pat_score)
            if kw_score > 0 and pat_score > 0:
                combined = min(kw_score * 0.4 + pat_score * 0.6 + 0.1, 1.0)
            final_score = combined * intent.priority
            if final_score >= min_score:
                candidates.append(IntentMatch(
                    name=intent.name,
                    score=final_score,
                    handler=intent.handler,
                    matched_keywords=matched_kws,
                ))

        candidates.sort(key=lambda m: m.score, reverse=True)
        return candidates[:max_results]

    def get_stats(self) -> dict:
        """Devuelve estadísticas del router."""
        total = self._stats["calls"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
        return {
            "total_calls": total,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 1),
            "top_intent": self._stats["top_intent"],
            "registered_intents": len(self._intents),
        }

    def list_intents(self) -> list[dict]:
        """Lista todas las intenciones registradas."""
        return [
            {
                "name": i.name,
                "keywords": i.keywords,
                "patterns_count": len(i.patterns),
                "priority": i.priority,
                "has_handler": i.handler is not None,
                "required_role": i.required_role,
            }
            for i in self._intents
        ]


# Singleton global
_router: IntentRouter | None = None


def get_router() -> IntentRouter:
    """Devuelve el router singleton."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


def reset_router() -> None:
    """Resetea el router (útil para tests)."""
    global _router
    _router = IntentRouter()
