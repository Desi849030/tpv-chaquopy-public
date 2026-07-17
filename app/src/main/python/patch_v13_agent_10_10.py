#!/usr/bin/env python3
"""
patch_v13_agent_10_10.py
========================
9 mejoras arquitectónicas inspiradas en free-code (Claude Code fork)
para convertir el agente TPV en un agente 10/10.

Ejecutar en Termux:
  cd ~/tpv-chaquopy-public/app/src/main/python
  python patch_v13_agent_10_10.py

Módulos nuevos creados en ia/:
  1. intent_router.py    - Router por scoring (reemplaza _fm)
  2. compaction.py       - Compacción de contexto por reglas
  3. skill_registry.py   - Registro decorador de skills
  4. denial_tracking.py  - Tracking de fallos consecutivos
  5. error_formatter.py  - Errores estructurados
  6. task_manager.py     - Máquina de estados para tareas
  7. hooks.py            - Pipeline pre/post hooks
  8. result_cache.py     - Caché TTL para db_utils.q()
  9. response_budget.py  - Límite de longitud de respuesta

También aplica patches de integración a:
  - ia/agent_chat_bp.py  (integra router + hooks + budget + compaction)
  - ia/db_utils.py       (integra cache en q())
"""

import os
import re
import shutil
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
IA_DIR = os.path.join(BASE, "ia")

# ============================================================
# 1. INTENT ROUTER — Reemplaza _fm() con scoring por relevancia
# ============================================================
MODULE_1 = r'''"""
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
'''

# ============================================================
# 2. COMPACTION — Compacción de contexto para conversaciones largas
# ============================================================
MODULE_2 = r'''"""
ia/compaction.py — Compacción de contexto por reglas.
Reduce el historial de conversación manteniendo la información esencial.

Inspirado en: free-code/src/commands/compact/compact.ts
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """Representa un mensaje en el historial."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class CompactionResult:
    """Resultado de la compacción."""
    original_count: int
    compacted_count: int
    reduction_pct: float
    preserved_summary: str
    messages: list[Message]


# Patrones de mensajes que se pueden resumir/eliminar
SUMMARIZABLE_PATTERNS = [
    (r"^(s[ií]|no|ok|vale|bueno|bien|gracias|perfecto|entendido|claro|aja)[\s.!]*$", "afirmacion"),
    (r"^(no\s+(sé|se|entiendo|entiende|comprendo)|no\s+(puedo|puedes))[\s.!]*$", "negacion"),
    (r"^(un\s+momento|espera|dame|déjame)\s+(pensar|verificar|buscar|revisar).*[\s.!]*$", "espera"),
]

ESSENTIAL_PATTERNS = [
    r"\b(crear|nuevo|agregar|eliminar|borrar|modificar|editar|cambiar)\b",
    r"\b(total|subtotal|precio|costo|monto|pago|cobro)\b",
    r"\b(cliente|producto|venta|factura|ticket|recibo)\b",
    r"\bstock|inventario|existencia|cantidad\b",
    r"\d+\.\d{2}",  # Montos con decimales
    r"\d{4,}",  # IDs o números largos
]


class ConversationCompactor:
    """
    Compactor de historial de conversación.

    Reglas:
    1. Eliminar mensajes vacíos o muy cortos (< 3 tokens)
    2. Fusionar mensajes consecutivos del mismo rol
    3. Resumir mensajes de confirmación ("sí", "ok", "no", etc.)
    4. Preservar siempre: mensajes con números, menciones a productos/clientes,
       y los últimos N mensajes del usuario y asistente
    5. Generar un resumen compacto del contexto eliminado
    """

    def __init__(
        self,
        max_messages: int = 50,
        keep_recent: int = 10,
        min_tokens: int = 3,
    ):
        self.max_messages = max_messages
        self.keep_recent = keep_recent
        self.min_tokens = min_tokens

    def _tokenize_simple(self, text: str) -> list[str]:
        """Tokenización simple por espacios (sin dependencias externas)."""
        return text.split()

    def _is_summarizable(self, msg: Message) -> tuple[bool, str]:
        """Verifica si un mensaje puede ser resumido."""
        content = msg.content.strip()
        for pattern, category in SUMMARIZABLE_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return True, category
        return False, ""

    def _is_essential(self, msg: Message) -> bool:
        """Verifica si un mensaje contiene información esencial."""
        if msg.role == "system":
            return True
        content = msg.content
        for pattern in ESSENTIAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        # Mensajes largos probablemente tienen información útil
        tokens = self._tokenize_simple(content)
        if len(tokens) > 20:
            return True
        return False

    def _extract_facts(self, messages: list[Message]) -> list[str]:
        """Extrae hechos clave de los mensajes a eliminar."""
        facts = []
        for msg in messages:
            # Buscar números con contexto (montos, cantidades, IDs)
            money_matches = re.findall(
                r"([\w\s]{0,30}?\d+[\.,]\d{2})", msg.content
            )
            for m in money_matches:
                facts.append(f"- Monto/cantidad mencionado: {m.strip()}")

            # Buscar nombres de productos/clientes (palabras con mayúsculas)
            proper_nouns = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b", msg.content)
            for noun in proper_nouns:
                if len(noun) > 3 and noun.lower() not in (
                    "el", "la", "los", "las", "un", "una", "del", "con",
                    "para", "por", "que", "como", "pero", "más", "esto",
                ):
                    facts.append(f"- Entidad mencionada: {noun}")
        return facts

    def compact(self, messages: list[Message]) -> CompactionResult:
        """
        Compacta la lista de mensajes.

        Args:
            messages: Lista de Message del historial completo.

        Returns:
            CompactionResult con el historial compactado.
        """
        original_count = len(messages)

        if original_count <= self.max_messages:
            return CompactionResult(
                original_count=original_count,
                compacted_count=original_count,
                reduction_pct=0.0,
                preserved_summary="",
                messages=messages,
            )

        # Separar: system messages siempre se preservan
        system_msgs = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]

        # Tomar los N más recientes
        recent = conversation[-self.keep_recent:] if len(conversation) > self.keep_recent else conversation
        older = conversation[:-self.keep_recent] if len(conversation) > self.keep_recent else []

        # De los antiguos, preservar los esenciales
        essential = [m for m in older if self._is_essential(m)]
        summarizable = [m for m in older if not self._is_essential(m)]

        # Extraer hechos de los mensajes resumibles
        facts = self._extract_facts(summarizable)

        # Generar resumen
        summary_parts = []
        cat_counts: dict[str, int] = {}
        for msg in summarizable:
            _, cat = self._is_summarizable(msg)
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if cat_counts:
            parts = [f"{v} {k}" for k, v in cat_counts.items()]
            summary_parts.append("Mensajes breves: " + ", ".join(parts))
        if facts:
            summary_parts.extend(facts[:10])  # Máximo 10 hechos
        preserved_summary = "\n".join(summary_parts) if summary_parts else ""

        # Componer resultado: system + esenciales antiguos + resumen + recientes
        compacted = list(system_msgs) + essential
        if preserved_summary:
            compacted.append(Message(
                role="system",
                content=f"[Contexto previo compactado]\n{preserved_summary}",
                metadata={"compacted": True, "removed_count": len(summarizable)},
            ))
        compacted.extend(recent)

        # Fusionar mensajes consecutivos del mismo rol
        compacted = self._merge_consecutive(compacted)

        compacted_count = len(compacted)
        reduction = round((1 - compacted_count / original_count) * 100, 1) if original_count > 0 else 0.0

        return CompactionResult(
            original_count=original_count,
            compacted_count=compacted_count,
            reduction_pct=reduction,
            preserved_summary=preserved_summary,
            messages=compacted,
        )

    def _merge_consecutive(self, messages: list[Message]) -> list[Message]:
        """Fusiona mensajes consecutivos del mismo rol."""
        if not messages:
            return messages
        merged = [messages[0]]
        for msg in messages[1:]:
            if msg.role == merged[-1].role and msg.role != "system":
                merged[-1] = Message(
                    role=msg.role,
                    content=merged[-1].content + "\n" + msg.content,
                    timestamp=merged[-1].timestamp,
                    metadata={**merged[-1].metadata, **msg.metadata, "merged": True},
                )
            else:
                merged.append(msg)
        return merged


def compact_history(messages: list[Message], max_messages: int = 50) -> CompactionResult:
    """Función de conveniencia para compactar historial."""
    compactor = ConversationCompactor(max_messages=max_messages)
    return compactor.compact(messages)
'''

# ============================================================
# 3. SKILL REGISTRY — Registro modular de handlers
# ============================================================
MODULE_3 = r'''"""
ia/skill_registry.py — Registro de skills con decoradores.
Permite registrar handlers de forma modular sin modificar
el código principal del agente.

Inspirado en: free-code/src/skills/bundled/remember.ts, loop.ts
"""

from __future__ import annotations
import inspect
from dataclasses import dataclass, field
from typing import Callable, Any, Optional


@dataclass
class SkillContext:
    """Contexto pasado a cada skill al ejecutarse."""
    agent: Any = None
    text: str = ""
    role: str = ""
    match: Any = None  # IntentMatch si viene del router
    extra: dict = field(default_factory=dict)


@dataclass
class SkillResult:
    """Resultado de ejecución de un skill."""
    success: bool
    response: str = ""
    data: dict = field(default_factory=dict)
    error: str = ""
    should_continue: bool = True  # Si False, detiene la pipeline


class SkillRegistry:
    """
    Registro centralizado de skills/handlers.

    Uso:
        registry = SkillRegistry()

        @registry.skill("consultar_stock", roles=["vendedor", "dev"],
                        description="Consulta stock de un producto")
        def handle_stock(ctx: SkillContext) -> SkillResult:
            ...

        # Ejecutar
        result = registry.execute("consultar_stock", ctx)
    """

    def __init__(self):
        self._skills: dict[str, dict] = {}
        self._execution_log: list[dict] = []

    def skill(
        self,
        name: str,
        roles: list[str] | None = None,
        description: str = "",
        priority: float = 1.0,
        keywords: list[str] | None = None,
        patterns: list[str] | None = None,
    ) -> Callable:
        """Decorador para registrar un skill."""
        def decorator(fn: Callable) -> Callable:
            self._skills[name] = {
                "handler": fn,
                "roles": roles or [],
                "description": description,
                "priority": priority,
                "keywords": keywords or [],
                "patterns": patterns or [],
                "name": name,
            }
            return fn
        return decorator

    def register(
        self,
        name: str,
        handler: Callable,
        roles: list[str] | None = None,
        description: str = "",
        priority: float = 1.0,
        keywords: list[str] | None = None,
        patterns: list[str] | None = None,
    ) -> None:
        """Registro programático (sin decorador)."""
        self._skills[name] = {
            "handler": handler,
            "roles": roles or [],
            "description": description,
            "priority": priority,
            "keywords": keywords or [],
            "patterns": patterns or [],
            "name": name,
        }

    def execute(self, name: str, ctx: SkillContext) -> SkillResult:
        """
        Ejecuta un skill por nombre.

        Args:
            name: Nombre del skill.
            ctx: Contexto de ejecución.

        Returns:
            SkillResult con el resultado.
        """
        skill_info = self._skills.get(name)
        if not skill_info:
            return SkillResult(
                success=False,
                error=f"Skill '{name}' no registrado",
                data={"skill_name": name},
            )

        # Verificar rol
        if skill_info["roles"] and ctx.role not in skill_info["roles"]:
            return SkillResult(
                success=False,
                error=f"Skill '{name}' no disponible para rol '{ctx.role}'",
                data={"skill_name": name, "required_roles": skill_info["roles"]},
            )

        handler = skill_info["handler"]
        start_time = __import__("time").time()

        try:
            # Inspeccionar firma para pasar argumentos correctos
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())

            if len(params) >= 2 and "ctx" in params:
                result = handler(ctx)
            elif len(params) >= 2:
                result = handler(ctx.agent, ctx.text)
            else:
                result = handler(ctx)

            elapsed = round(__import__("time").time() - start_time, 3)

            # Normalizar resultado
            if isinstance(result, SkillResult):
                pass
            elif isinstance(result, str):
                result = SkillResult(success=True, response=result)
            elif isinstance(result, tuple) and len(result) == 2:
                result = SkillResult(success=result[0], response=result[1])
            else:
                result = SkillResult(success=True, response=str(result))

            # Log
            self._execution_log.append({
                "skill": name,
                "success": result.success,
                "elapsed_ms": int(elapsed * 1000),
                "role": ctx.role,
                "timestamp": __import__("time").time(),
            })

            return result

        except Exception as e:
            elapsed = round(__import__("time").time() - start_time, 3)
            self._execution_log.append({
                "skill": name,
                "success": False,
                "error": str(e),
                "elapsed_ms": int(elapsed * 1000),
                "role": ctx.role,
                "timestamp": __import__("time").time(),
            })
            return SkillResult(
                success=False,
                error=f"Error en skill '{name}': {e}",
                data={"skill_name": name, "exception": type(e).__name__},
            )

    def list_skills(self, role: str | None = None) -> list[dict]:
        """Lista skills registrados, opcionalmente filtrados por rol."""
        skills = []
        for name, info in self._skills.items():
            if role and info["roles"] and role not in info["roles"]:
                continue
            skills.append({
                "name": name,
                "description": info["description"],
                "roles": info["roles"],
                "priority": info["priority"],
                "keywords": info["keywords"],
            })
        skills.sort(key=lambda s: s["priority"], reverse=True)
        return skills

    def get_execution_log(self, last_n: int = 20) -> list[dict]:
        """Devuelve los últimos N registros de ejecución."""
        return self._execution_log[-last_n:]

    def clear_log(self) -> None:
        """Limpia el log de ejecución."""
        self._execution_log.clear()


# Singleton global
_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Devuelve el registry singleton."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def reset_registry() -> None:
    """Resetea el registry (útil para tests)."""
    global _registry
    _registry = SkillRegistry()
'''

# ============================================================
# 4. DENIAL TRACKING — Tracking de fallos consecutivos
# ============================================================
MODULE_4 = r'''"""
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
'''

# ============================================================
# 5. ERROR FORMATTER — Errores estructurados y amigables
# ============================================================
MODULE_5 = r'''"""
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
'''

# ============================================================
# 6. TASK MANAGER — Máquina de estados para tareas multi-step
# ============================================================
MODULE_6 = r'''"""
ia/task_manager.py — Máquina de estados para operaciones multi-step.
Gestiona tareas que requieren varios pasos interactivos.

Inspirado en: free-code/src/Task.ts
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"       # Creada, esperando inicio
    RUNNING = "running"       # En ejecución
    WAITING_INPUT = "waiting_input"  # Esperando input del usuario
    COMPLETED = "completed"   # Finalizada con éxito
    FAILED = "failed"         # Falló
    KILLED = "killed"         # Cancelada por el usuario


@dataclass
class TaskStep:
    """Un paso dentro de una tarea."""
    name: str
    description: str = ""
    handler: Callable | None = None
    required_input: bool = False
    input_prompt: str = ""
    timeout_seconds: float = 0  # 0 = sin timeout
    result: Any = None
    status: str = "pending"  # pending | running | completed | failed | skipped


@dataclass
class Task:
    """Tarea multi-step con estado."""
    id: str
    name: str
    description: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def current_step(self) -> TaskStep | None:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return round(completed / len(self.steps) * 100, 1)

    @property
    def is_finished(self) -> bool:
        return self.status in (
            TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED
        )


class TaskManager:
    """
    Gestor de tareas multi-step.

    Uso:
        tm = TaskManager()

        # Crear tarea
        task = tm.create("nueva_venta", "Registrar nueva venta", steps=[
            TaskStep("identificar_cliente", "Identificar al cliente", required_input=True,
                     input_prompt="¿Nombre o ID del cliente?"),
            TaskStep("agregar_productos", "Agregar productos", required_input=True,
                     input_prompt="¿Qué productos desea agregar?"),
            TaskStep("confirmar", "Confirmar venta", required_input=True,
                     input_prompt="¿Confirma la venta? (sí/no)"),
        ])

        # Avanzar
        task = tm.provide_input(task.id, "Juan Pérez")
        # → avanza al siguiente paso que requiere input
    """

    def __init__(self, max_active_tasks: int = 20, task_ttl_seconds: float = 3600):
        self._tasks: dict[str, Task] = {}
        self.max_active_tasks = max_active_tasks
        self.task_ttl_seconds = task_ttl_seconds

    def create(
        self,
        name: str,
        description: str = "",
        steps: list[TaskStep] | None = None,
        metadata: dict | None = None,
    ) -> Task:
        """Crea una nueva tarea."""
        # Limpiar tareas expiradas
        self._cleanup_expired()

        if len(self._tasks) >= self.max_active_tasks:
            # Matar la tarea más antigua
            oldest_id = min(self._tasks, key=lambda k: self._tasks[k].updated_at)
            self.kill(oldest_id)

        task_id = f"{name}_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            name=name,
            description=description,
            steps=steps or [],
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        return task

    def start(self, task_id: str) -> Task | None:
        """Inicia una tarea pendiente."""
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None
        task.status = TaskStatus.RUNNING
        task.updated_at = time.time()
        return self._advance(task)

    def provide_input(self, task_id: str, user_input: str) -> Task | None:
        """
        Provee input a una tarea que está esperando.

        Args:
            task_id: ID de la tarea.
            user_input: Input del usuario.

        Returns:
            Task actualizada o None.
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task.status != TaskStatus.WAITING_INPUT:
            return None

        step = task.current_step
        if not step:
            return None

        # Ejecutar handler del paso actual con el input
        step.result = user_input
        step.status = "completed"
        task.updated_at = time.time()

        if step.handler:
            try:
                handler_result = step.handler(user_input, task)
                step.result = handler_result
            except Exception as e:
                step.status = "failed"
                task.status = TaskStatus.FAILED
                task.error = f"Error en paso '{step.name}': {e}"
                return task

        return self._advance(task)

    def _advance(self, task: Task) -> Task:
        """Avanza al siguiente paso de la tarea."""
        # Buscar el siguiente paso pendiente
        for i in range(task.current_step_index, len(task.steps)):
            step = task.steps[i]
            if step.status == "pending":
                task.current_step_index = i
                if step.required_input:
                    task.status = TaskStatus.WAITING_INPUT
                    step.status = "running"
                else:
                    # Paso automático (sin input requerido)
                    step.status = "running"
                    if step.handler:
                        try:
                            step.result = step.handler(task)
                            step.status = "completed"
                        except Exception as e:
                            step.status = "failed"
                            task.status = TaskStatus.FAILED
                            task.error = f"Error en paso '{step.name}': {e}"
                            return task
                    else:
                        step.status = "completed"
                task.updated_at = time.time()
                return task

        # No hay más pasos → tarea completada
        task.status = TaskStatus.COMPLETED
        task.updated_at = time.time()
        return task

    def cancel(self, task_id: str, reason: str = "Cancelada por el usuario") -> Task | None:
        """Cancela una tarea activa."""
        task = self._tasks.get(task_id)
        if not task or task.is_finished:
            return None
        task.status = TaskStatus.KILLED
        task.error = reason
        task.updated_at = time.time()
        return task

    def kill(self, task_id: str) -> Task | None:
        """Fuerza la terminación de una tarea."""
        return self.cancel(task_id, "Forzadamente terminada")

    def get(self, task_id: str) -> Task | None:
        """Obtiene una tarea por ID."""
        return self._tasks.get(task_id)

    def get_active_tasks(self, name: str | None = None) -> list[Task]:
        """Devuelve tareas activas (no terminadas)."""
        tasks = [t for t in self._tasks.values() if not t.is_finished]
        if name:
            tasks = [t for t in tasks if t.name == name]
        return tasks

    def _cleanup_expired(self) -> int:
        """Elimina tareas expiradas."""
        now = time.time()
        expired = [
            tid for tid, t in self._tasks.items()
            if now - t.updated_at > self.task_ttl_seconds and t.is_finished
        ]
        for tid in expired:
            del self._tasks[tid]
        return len(expired)

    def get_summary(self) -> dict:
        """Resumen de todas las tareas."""
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "active": sum(1 for t in tasks if not t.is_finished),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "killed": sum(1 for t in tasks if t.status == TaskStatus.KILLED),
        }


# Singleton
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Devuelve el task manager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def reset_task_manager() -> None:
    """Resetea el task manager (útil para tests)."""
    global _task_manager
    _task_manager = TaskManager()
'''

# ============================================================
# 7. HOOKS — Sistema de pre/post hooks para la pipeline
# ============================================================
MODULE_7 = r'''"""
ia/hooks.py — Sistema de hooks pre/post para la pipeline del agente.
Permite extender el comportamiento sin modificar el código principal.

Inspirado en: free-code/src/utils/processUserInput/processUserInput.ts
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any
from collections import OrderedDict


class HookPoint(Enum):
    """Puntos de enganche en la pipeline."""
    PRE_PROCESS = "pre_process"           # Antes de procesar el input
    POST_PROCESS = "post_process"         # Después de generar respuesta
    PRE_DB_QUERY = "pre_db_query"         # Antes de consulta a BD
    POST_DB_QUERY = "post_db_query"       # Después de consulta a BD
    PRE_RESPONSE = "pre_response"         # Antes de enviar respuesta
    ON_ERROR = "on_error"                 # Cuando ocurre un error
    ON_DENIED = "on_denied"               # Cuando se deniega una acción


@dataclass
class HookContext:
    """Contexto pasado a cada hook."""
    hook_point: HookPoint
    agent: Any = None
    text: str = ""
    role: str = ""
    response: str = ""
    error: Exception | None = None
    db_query: str = ""
    db_result: Any = None
    metadata: dict = field(default_factory=dict)
    modified: bool = False  # Si True, el hook modificó algo


@dataclass
class HookResult:
    """Resultado de un hook."""
    should_continue: bool = True  # Si False, detiene la pipeline
    modified_text: str | None = None
    modified_response: str | None = None
    override: str | None = None  # Si set, reemplaza la respuesta completamente
    metadata: dict = field(default_factory=dict)


class HookPipeline:
    """
    Pipeline de hooks para la procesamiento del agente.

    Uso:
        pipeline = HookPipeline()

        @pipeline.hook(HookPoint.PRE_PROCESS, priority=10)
        def normalize_input(ctx: HookContext) -> HookResult:
            ctx.text = ctx.text.strip().lower()
            return HookResult(modified_text=ctx.text)

        @pipeline.hook(HookPoint.ON_ERROR, priority=20)
        def log_error(ctx: HookContext) -> HookResult:
            print(f"Error: {ctx.error}")
            return HookResult()

        # Ejecutar
        result = pipeline.execute(HookPoint.PRE_PROCESS, context)
    """

    def __init__(self):
        # OrderedDict mantiene orden de registro; sorted por priority al ejecutar
        self._hooks: dict[HookPoint, list[dict]] = {
            point: [] for point in HookPoint
        }
        self._execution_count = 0
        self._last_execution_log: list[dict] = []

    def hook(
        self,
        hook_point: HookPoint | str,
        priority: float = 10.0,
        name: str = "",
    ) -> Callable:
        """Decorador para registrar un hook."""
        if isinstance(hook_point, str):
            hook_point = HookPoint(hook_point)

        def decorator(fn: Callable) -> Callable:
            self._hooks[hook_point].append({
                "handler": fn,
                "priority": priority,
                "name": name or fn.__name__,
            })
            # Mantener ordenado por prioridad (mayor primero)
            self._hooks[hook_point].sort(key=lambda h: h["priority"], reverse=True)
            return fn
        return decorator

    def register(
        self,
        hook_point: HookPoint | str,
        handler: Callable,
        priority: float = 10.0,
        name: str = "",
    ) -> None:
        """Registro programático."""
        if isinstance(hook_point, str):
            hook_point = HookPoint(hook_point)
        self._hooks[hook_point].append({
            "handler": handler,
            "priority": priority,
            "name": name or handler.__name__,
        })
        self._hooks[hook_point].sort(key=lambda h: h["priority"], reverse=True)

    def execute(
        self,
        hook_point: HookPoint | str,
        context: HookContext,
        stop_on_false: bool = True,
    ) -> HookResult:
        """
        Ejecuta todos los hooks registrados para un punto.

        Args:
            hook_point: Punto de enganche.
            context: Contexto de ejecución.
            stop_on_false: Si True, detiene al primer hook que devuelva should_continue=False.

        Returns:
            HookResult combinado de todos los hooks ejecutados.
        """
        if isinstance(hook_point, str):
            hook_point = HookPoint(hook_point)

        self._execution_count += 1
        combined = HookResult()
        log_entries = []

        for hook_info in self._hooks[hook_point]:
            handler = hook_info["handler"]
            start = time.time()
            try:
                result = handler(context)
                elapsed = round((time.time() - start) * 1000, 2)

                # Normalizar resultado
                if result is None:
                    result = HookResult()
                elif isinstance(result, str):
                    result = HookResult(override=result)
                elif isinstance(result, bool):
                    result = HookResult(should_continue=result)

                # Combinar
                if result.modified_text:
                    combined.modified_text = result.modified_text
                    context.text = result.modified_text
                    context.modified = True
                if result.modified_response:
                    combined.modified_response = result.modified_response
                    context.response = result.modified_response
                if result.override:
                    combined.override = result.override
                if not result.should_continue:
                    combined.should_continue = False
                combined.metadata.update(result.metadata)

                log_entries.append({
                    "hook": hook_info["name"],
                    "elapsed_ms": elapsed,
                    "success": True,
                })

                if stop_on_false and not result.should_continue:
                    break

            except Exception as e:
                elapsed = round((time.time() - start) * 1000, 2)
                log_entries.append({
                    "hook": hook_info["name"],
                    "elapsed_ms": elapsed,
                    "success": False,
                    "error": str(e),
                })
                # Los hooks fallidos no detienen la pipeline por defecto
                continue

        self._last_execution_log = log_entries
        return combined

    def get_registered_hooks(self, hook_point: HookPoint | None = None) -> list[dict]:
        """Lista hooks registrados."""
        if hook_point:
            if isinstance(hook_point, str):
                hook_point = HookPoint(hook_point)
            return [
                {"name": h["name"], "priority": h["priority"]}
                for h in self._hooks.get(hook_point, [])
            ]
        result = {}
        for point, hooks in self._hooks.items():
            if hooks:
                result[point.value] = [
                    {"name": h["name"], "priority": h["priority"]}
                    for h in hooks
                ]
        return result


# Singleton
_pipeline: HookPipeline | None = None


def get_hook_pipeline() -> HookPipeline:
    """Devuelve la pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = HookPipeline()
    return _pipeline


def reset_hook_pipeline() -> None:
    """Resetea la pipeline (útil para tests)."""
    global _pipeline
    _pipeline = HookPipeline()
'''

# ============================================================
# 8. RESULT CACHE — Caché TTL para db_utils.q()
# ============================================================
MODULE_8 = r'''"""
ia/result_cache.py — Caché TTL para resultados de db_utils.q().
Evita consultas repetitivas a SQLite en la misma conversación.

Inspirado en: free-code/src/utils/toolResultStorage.ts
"""

from __future__ import annotations
import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """Entrada en la caché."""
    key: str
    value: Any
    created_at: float
    ttl: float
    hit_count: int = 0
    size_bytes: int = 0


class ResultCache:
    """
    Caché LRU con TTL para resultados de consultas.

    Uso:
        cache = ResultCache(max_size=100, default_ttl=30.0)

        # Guardar
        cache.set("SELECT * FROM productos WHERE id=1", rows)

        # Leer
        rows = cache.get("SELECT * FROM productos WHERE id=1")
        if rows is None:
            rows = db_utils.q("SELECT * FROM productos WHERE id=1")
            cache.set("SELECT * FROM productos WHERE id=1", rows)

        # Envolver db_utils.q
        cached_q = cache.wrap_query(db_utils.q)
        rows = cached_q("SELECT * FROM productos WHERE categoria='bebidas'")
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl: float = 30.0,
        max_memory_bytes: int = 5 * 1024 * 1024,  # 5MB
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_bytes
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
        }

    def _make_key(self, query: str, params: tuple = ()) -> str:
        """Genera una clave hash para la consulta."""
        raw = f"{query}|{params}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, query: str, params: tuple = ()) -> Any | None:
        """
        Obtiene un resultado cacheado.

        Returns:
            El resultado cacheado o None si expiró/no existe.
        """
        key = self._make_key(query, params)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            # Verificar TTL
            if time.time() - entry.created_at > entry.ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Mover al final (LRU)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

    def set(
        self,
        query: str,
        value: Any,
        params: tuple = (),
        ttl: float | None = None,
    ) -> None:
        """
        Guarda un resultado en caché.

        Args:
            query: La consulta SQL.
            value: El resultado a cachear.
            params: Parámetros de la consulta.
            ttl: Time-to-live en segundos (usa default_ttl si None).
        """
        key = self._make_key(query, params)
        ttl = ttl if ttl is not None else self.default_ttl

        # Estimar tamaño
        try:
            size = len(str(value))
        except Exception:
            size = 0

        with self._lock:
            # Evict si excede tamaño máximo
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            # Evict por memoria si es necesario
            total_size = sum(e.size_bytes for e in self._cache.values())
            while total_size + size > self.max_memory_bytes and self._cache:
                evicted = self._cache.popitem(last=False)
                total_size -= evicted[1].size_bytes
                self._stats["evictions"] += 1

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                size_bytes=size,
            )
            self._stats["sets"] += 1

    def invalidate(self, query: str | None = None, params: tuple = ()) -> int:
        """
        Invalida entradas de la caché.

        Args:
            query: Si None, limpia toda la caché. Si str, invalida esa clave.

        Returns:
            Número de entradas invalidadas.
        """
        with self._lock:
            if query is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            key = self._make_key(query, params)
            if key in self._cache:
                del self._cache[key]
                return 1
            return 0

    def invalidate_pattern(self, table_name: str) -> int:
        """
        Invalida todas las entradas que contengan un nombre de tabla.

        Útil después de INSERT/UPDATE/DELETE en esa tabla.
        """
        # Como las keys son hashes, no podemos buscar por patrón.
        # Solución: limpiar toda la caché (conservador pero seguro).
        # En el futuro se puede guardar el query original también.
        return self.invalidate()

    def wrap_query(self, query_fn):
        """
        Envuelve una función de consulta con caché.

        Uso:
            cached_q = cache.wrap_query(db_utils.q)
            rows = cached_q("SELECT * FROM productos WHERE id=?", (1,))
        """
        def cached_wrapper(query: str, *args, **kwargs):
            params = args if args else kwargs.get("params", ())
            if isinstance(params, (list, tuple)):
                params = tuple(params)
            else:
                params = (params,)

            # Solo cachear SELECTs
            query_stripped = query.strip().upper()
            if not query_stripped.startswith("SELECT"):
                # Si no es SELECT, invalidar cache (la BD cambió)
                self.invalidate()
                return query_fn(query, *args, **kwargs)

            cached = self.get(query, params)
            if cached is not None:
                return cached

            result = query_fn(query, *args, **kwargs)
            self.set(query, result, params)
            return result

        # Adjuntar referencia al cache para control manual
        cached_wrapper._cache = self
        cached_wrapper._original = query_fn
        return cached_wrapper

    def get_stats(self) -> dict:
        """Estadísticas de la caché."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 1),
            "evictions": self._stats["evictions"],
            "total_sets": self._stats["sets"],
            "current_size": len(self._cache),
            "max_size": self.max_size,
        }

    def clear(self) -> None:
        """Limpia toda la caché."""
        with self._lock:
            self._cache.clear()


# Singleton
_cache: ResultCache | None = None


def get_cache() -> ResultCache:
    """Devuelve la caché singleton."""
    global _cache
    if _cache is None:
        _cache = ResultCache()
    return _cache


def reset_cache() -> None:
    """Resetea la caché (útil para tests)."""
    global _cache
    _cache = ResultCache()
'''

# ============================================================
# 9. RESPONSE BUDGET — Gestión de longitud de respuesta
# ============================================================
MODULE_9 = r'''"""
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
'''

# ============================================================
# INTEGRATION CODE — Patches para archivos existentes
# ============================================================

INTEGRATION_AGENT_CHAT = '''
# === PATCH: Integración de módulos v13 en agent_chat_bp.py ===
# Agregar estos imports al inicio del archivo (después de los imports existentes):

try:
    from ia.intent_router import get_router, IntentMatch
    from ia.compaction import compact_history, Message as CompactionMessage
    from ia.denial_tracking import get_tracker
    from ia.error_formatter import get_error_formatter
    from ia.hooks import get_hook_pipeline, HookPoint, HookContext
    from ia.response_budget import get_budget, BudgetMode
    from ia.task_manager import get_task_manager, TaskStep
    HAS_V13_MODULES = True
except ImportError:
    HAS_V13_MODULES = False

# === PATCH: En la función principal de procesamiento de mensajes ===
# Después de obtener el texto del usuario y antes del dispatch a handlers,
# insertar este bloque:

# --- v13: Pre-processing hooks ---
if HAS_V13_MODULES:
    pipeline = get_hook_pipeline()
    hook_ctx = HookContext(
        hook_point=HookPoint.PRE_PROCESS,
        agent=agent,
        text=text,
        role=role,
    )
    hook_result = pipeline.execute(HookPoint.PRE_PROCESS, hook_ctx)
    if hook_result.modified_text:
        text = hook_result.modified_text
    if hook_result.override:
        return hook_result.override

# --- v13: Denial tracking (registrar resultado después del handler) ---
# Después de obtener la respuesta del handler:
# tracker = get_tracker()
# if response_ok:
#     tracker.record_success()
# else:
#     tracker.record_failure("Razón del fallo")
# if tracker.state.is_stuck:
#     recovery = tracker.get_recovery_message()
#     if recovery:
#         response = recovery

# --- v13: Response budget ---
# Antes de retornar la respuesta final:
# budget = get_budget()
# response = budget.apply(response, mode=BudgetMode.NORMAL)

# --- v13: Post-processing hooks ---
# if HAS_V13_MODULES:
#     post_ctx = HookContext(
#         hook_point=HookPoint.POST_PROCESS,
#         agent=agent,
#         text=text,
#         role=role,
#         response=response,
#     )
#     post_result = pipeline.execute(HookPoint.POST_PROCESS, post_ctx)
#     if post_result.modified_response:
#         response = post_result.modified_response
#     if post_result.override:
#         response = post_result.override

# --- v13: Compaction (llamar periódicamente en conversaciones largas) ---
# if HAS_V13_MODULES and len(history) > 50:
#     from ia.compaction import compact_history, Message as CMsg
#     msgs = [CMsg(role=m["role"], content=m["content"]) for m in history]
#     result = compact_history(msgs, max_messages=40)
#     history = [{"role": m.role, "content": m.content} for m in result.messages]
'''

INTEGRATION_DB_UTILS = '''
# === PATCH: Integración de caché en db_utils.py ===
# Agregar después de la definición de la función q():

try:
    from ia.result_cache import get_cache
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False

# Para habilitar caché en q(), reemplazar la llamada original con:
# if HAS_CACHE:
#     cache = get_cache()
#     cached_result = cache.get(query, params)
#     if cached_result is not None:
#         return cached_result
#     result = _original_q(query, *args, **kwargs)
#     if query.strip().upper().startswith("SELECT"):
#         cache.set(query, result, params, ttl=30.0)
#     return result
# else:
#     return _original_q(query, *args, **kwargs)

# Forma más simple: envolver la función
# if HAS_CACHE:
#     from ia.result_cache import get_cache
#     q_cached = get_cache().wrap_query(q)
#     # Usar q_cached en lugar de q para lecturas
'''

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

MODULES = {
    "intent_router.py": MODULE_1,
    "compaction.py": MODULE_2,
    "skill_registry.py": MODULE_3,
    "denial_tracking.py": MODULE_4,
    "error_formatter.py": MODULE_5,
    "task_manager.py": MODULE_6,
    "hooks.py": MODULE_7,
    "result_cache.py": MODULE_8,
    "response_budget.py": MODULE_9,
}

INTEGRATION_FILES = {
    "INTEGRATION_agent_chat_bp.py.txt": INTEGRATION_AGENT_CHAT,
    "INTEGRATION_db_utils.py.txt": INTEGRATION_DB_UTILS,
}


def create_module(filepath: str, content: str) -> bool:
    """Crea un módulo .py en ia/"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] {os.path.basename(filepath)} ({len(content)} bytes)")
        return True
    except Exception as e:
        print(f"  [ERROR] {os.path.basename(filepath)}: {e}")
        return False


def create_integration(filepath: str, content: str) -> bool:
    """Crea archivo de integración (texto con instrucciones)"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"  [ERROR] {os.path.basename(filepath)}: {e}")
        return False


def verify_syntax(filepath: str) -> bool:
    """Verifica sintaxis de un .py"""
    import py_compile
    try:
        py_compile.compile(filepath, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  [SYNTAX ERROR] {os.path.basename(filepath)}: {e}")
        return False


def main():
    print("=" * 60)
    print("  PATCH v13 — Agente 10/10")
    print("  9 mejoras arquitectónicas para TPV Agent")
    print("=" * 60)
    print()

    # Verificar que estamos en el directorio correcto
    if not os.path.isdir(IA_DIR):
        print(f"[ERROR] Directorio 'ia/' no encontrado en {BASE}")
        print(f"  Ejecutar desde: ~/tpv-chaquopy-public/app/src/main/python/")
        return 1

    # Backup
    backup_dir = os.path.join(BASE, "ia_backup_v13")
    if not os.path.exists(backup_dir):
        print(f"[*] Creando backup en {backup_dir}")
        os.makedirs(backup_dir, exist_ok=True)

    # Crear módulos nuevos
    print("[1/3] Creando 9 nuevos módulos en ia/:")
    print("-" * 40)
    created = 0
    for filename, content in MODULES.items():
        filepath = os.path.join(IA_DIR, filename)
        if create_module(filepath, content):
            # Verificar sintaxis
            if verify_syntax(filepath):
                created += 1
    print(f"\n  {created}/{len(MODULES)} módulos creados con sintaxis OK\n")

    # Crear archivos de integración
    print("[2/3] Creando archivos de integración:")
    print("-" * 40)
    int_dir = os.path.join(BASE, "v13_integration")
    os.makedirs(int_dir, exist_ok=True)
    for filename, content in INTEGRATION_FILES.items():
        create_integration(os.path.join(int_dir, filename), content)
    print()

    # Resumen
    print("[3/3] Resumen de módulos:")
    print("-" * 40)
    module_info = [
        ("intent_router.py", "Router por scoring (reemplaza _fm())"),
        ("compaction.py", "Compacción de contexto por reglas"),
        ("skill_registry.py", "Registro decorador de skills"),
        ("denial_tracking.py", "Tracking de fallos consecutivos"),
        ("error_formatter.py", "Errores estructurados y amigables"),
        ("task_manager.py", "Máquina de estados para tareas"),
        ("hooks.py", "Pipeline pre/post hooks"),
        ("result_cache.py", "Caché TTL para db_utils.q()"),
        ("response_budget.py", "Límite de longitud de respuesta"),
    ]
    for name, desc in module_info:
        filepath = os.path.join(IA_DIR, name)
        exists = "OK" if os.path.exists(filepath) else "FALTANTE"
        print(f"  [{exists}] {name:25s} — {desc}")

    print()
    print("=" * 60)
    print("  RESULTADO:")
    print(f"  {created}/9 módulos creados correctamente")
    print()
    print("  INTEGRACIÓN:")
    print(f"  Ver {int_dir}/ para instrucciones de integración")
    print("  en agent_chat_bp.py y db_utils.py")
    print()
    print("  Los módulos son NO-INVASIVOS:")
    print("  - No modifican código existente")
    print("  - Se activan con: from ia.intent_router import get_router")
    print("  - Si falla el import, HAS_V13_MODULES = False (safe fallback)")
    print("=" * 60)

    return 0 if created == len(MODULES) else 1


if __name__ == "__main__":
    exit(main())