"""
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
