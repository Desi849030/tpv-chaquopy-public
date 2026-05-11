# -*- coding: utf-8 -*-
"""
reasoning_engine.py v2 - Motor ReAct para Agente IA TPV
Modularizado: core (ia/react_core.py) + templates (ia/react_templates.py)
"""
from __future__ import annotations

import json
from datetime import datetime

from ia.react_core import ReActEngine as _ReActCore
from ia.react_templates import ReActEngineTemplates
from ia.react_categories import CATEGORY_SUMMARIES
from ia.react_plans import PREDEFINED_PLANS


class ReActEngine(_ReActCore, ReActEngineTemplates):
    """Motor ReAct: ejecuta herramientas del tool_registry via Flask test_client()."""
    pass

def get_engine_status(app=None):
    engine = ReActEngine(app=app)
    return engine.get_status()


def list_available_plans():
    return {"plans": list(PREDEFINED_PLANS.keys()), "details": {n: p.get("description", "") for n, p in PREDEFINED_PLANS.items()}}
