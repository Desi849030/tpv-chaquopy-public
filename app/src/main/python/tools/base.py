"""
tool_registry.py — Catalogo COMPLETO de herramientas para la IA Agéntica.
Registra las 144 rutas API del TPV como "tools" con descripcion,
parametros y tipo de acceso. El reasoning_engine consulta este
catalogo para decidir que herramienta usar.

Industrialization v5 — Agentic AI Layer (147 herramientas)
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definicion de una herramienta disponible para el agente."""
    name: str
    description: str
    category: str
    route: str
    method: str
    params: List[Dict[str, str]]
    requires_auth: bool = True
    requires_role: Optional[str] = None


def _t(name, desc, cat, route, method, params, role=None, auth=True):
    """Helper rapido para crear ToolDefinition."""
    return ToolDefinition(name, desc, cat, route, method, params, auth, role)
