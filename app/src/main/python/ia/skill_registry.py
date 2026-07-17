"""
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
