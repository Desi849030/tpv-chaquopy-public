# -*- coding: utf-8 -*-
"""
reasoning_engine.py v2 - Motor ReAct para Agente IA TPV
v2: Integracion dinamica con tool_registry.py (141+ herramientas) via test_client()
"""
from __future__ import annotations

import json
import re
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from tool_registry import get_tool, get_tools_by_category as list_tools_by_category, search_tools, get_catalog_stats
except ImportError:
    get_tool = None
    list_tools_by_category = None
    search_tools = None
    get_catalog_stats = None

try:
    from agent_state import AgentStateManager
except ImportError:
    AgentStateManager = None

try:
    from output_validator import OutputValidator
except ImportError:
    OutputValidator = None

MAX_STEPS = 15
MAX_CORRECTIONS = 3

from ia.react_categories import CATEGORY_SUMMARIES


from ia.react_plans import PREDEFINED_PLANS



class ReActEngine:
    """Motor ReAct: ejecuta herramientas del tool_registry via Flask test_client()."""

    def __init__(self, app=None, session_id=None, user_session=None):
        self.app = app
        self.session_id = session_id
        self.client = None
        self.tool_catalog = {}
        self.category_index = {}
        self.state_manager = None
        self.validator = None
        if app is not None:
            try:
                self.client = app.test_client()
                if self._user_session:
                    with self.client.session_transaction() as sess:
                        sess['usuario'] = self._user_session
            except Exception as exc:
                print("[ReActEngine] test_client error: %s" % exc)
        self._load_catalog()
        if AgentStateManager is not None and session_id:
            try:
                self.state_manager = AgentStateManager(session_id)
            except Exception:
                pass
        if OutputValidator is not None:
            try:
                self.validator = OutputValidator()
            except Exception:
                pass

    def _load_catalog(self):
        self.tool_catalog = {}
        self.category_index = {}
        if list_tools_by_category is None:
            return
        try:
            catalog = list_tools_by_category()
            for category, tools in catalog.items():
                self.category_index[category] = []
                for tool in tools:
                    name = tool.get("name", "")
                    if name:
                        self.tool_catalog[name] = tool
                        self.category_index[category].append(name)
        except Exception as exc:
            print("[ReActEngine] catalog error: %s" % exc)

    def get_status(self):
        stats = {}
        if get_catalog_stats:
            try:
                stats = get_catalog_stats()
            except Exception:
                pass
        return {
            "engine_ready": self.client is not None,
            "tools_loaded": len(self.tool_catalog),
            "categories_loaded": len(self.category_index),
            "state_manager": self.state_manager is not None,
            "validator": self.validator is not None,
            "registry_stats": stats,
        }

    def _find_tool(self, query):
        if not query:
            return None
        q = query.lower().strip()
        if q in self.tool_catalog:
            return self.tool_catalog[q]
        for name, tool in self.tool_catalog.items():
            if q in name.lower():
                return tool
        if search_tools is not None:
            try:
                results = search_tools(query)
                if results:
                    return results[0]
            except Exception:
                pass
        for cat in CATEGORY_SUMMARIES:
            if cat in q:
                names = self.category_index.get(cat, [])
                if names:
                    return self.tool_catalog.get(names[0])
        keywords = q.split()
        best = None
        best_score = 0
        for name, tool in self.tool_catalog.items():
            desc = (tool.get("description", "") + " " + name).lower()
            score = sum(1 for kw in keywords if kw in desc)
            if score > best_score:
                best_score = score
                best = tool
        return best if best_score >= 1 else None

    def _find_tools_for_category(self, category):
        names = self.category_index.get(category, [])
        return [self.tool_catalog.get(n) for n in names if n in self.tool_catalog]

    def _call_tool(self, tool_name, params=None):
        if not self.client:
            return {"success": False, "tool": tool_name, "error": "Sin cliente Flask"}
        tool = self.tool_catalog.get(tool_name)
        if tool is None:
            tool = self._find_tool(tool_name)
        if tool is None:
            avail = sorted(self.tool_catalog.keys())
            return {"success": False, "tool": tool_name, "error": "No encontrada. Top: %s" % str(avail[:10])}
        tool_name = tool.get("name", tool_name)
        method = tool.get("method", "GET").upper()
        endpoint = tool.get("endpoint", "")
        tool_params = tool.get("parameters", {})
        params = params or {}
        filtered = {}
        for key, value in params.items():
            if key in tool_params or not tool_params:
                filtered[key] = value
        try:
            if method == "GET":
                resp = self.client.get(endpoint, query_string=filtered)
            elif method == "POST":
                resp = self.client.post(endpoint, json=filtered)
            elif method == "PUT":
                resp = self.client.put(endpoint, json=filtered)
            elif method == "DELETE":
                resp = self.client.delete(endpoint, json=filtered)
            elif method == "PATCH":
                resp = self.client.patch(endpoint, json=filtered)
            else:
                return {"success": False, "tool": tool_name, "error": "Metodo no soportado: %s" % method}
            data = resp.get_json(silent=True)
            if data is None:
                data = {"raw": resp.get_data(as_text=True)[:500]}
            return {"success": resp.status_code < 400, "status": resp.status_code, "data": data, "tool": tool_name, "endpoint": endpoint, "method": method}
        except Exception as exc:
            return {"success": False, "tool": tool_name, "error": "%s: %s" % (type(exc).__name__, exc)}

    def _call_by_search(self, query, params=None):
        tool = self._find_tool(query)
        if tool is None:
            return {"success": False, "error": "Sin herramienta para: %s" % query, "query": query}
        return self._call_tool(tool.get("name", ""), params)


    def execute_plan(self, plan_name=None, steps=None, context=None):
        if steps is None:
            if plan_name and plan_name in PREDEFINED_PLANS:
                steps = PREDEFINED_PLANS[plan_name].get("steps", [])
            else:
                return {"success": False, "error": "Plan no encontrado: %s. Disponibles: %s" % (plan_name, list(PREDEFINED_PLANS.keys()))}
        context = context or {}
        results = []
        errors = []
        observations = []
        corrections = 0
        for i, step in enumerate(steps):
            if corrections >= MAX_CORRECTIONS:
                errors.append("Max correcciones (%d)" % MAX_CORRECTIONS)
                break
            if i + 1 > MAX_STEPS:
                errors.append("Max pasos (%d)" % MAX_STEPS)
                break
            try:
                result = self._execute_step(step, context, observations, i + 1)
                results.append(result)
                if not result.get("success", True):
                    fix = self._attempt_correction(step, result, context)
                    if fix:
                        results.append(fix)
                        observations.append(fix)
                        corrections += 1
                    else:
                        errors.append("Paso %d fallo" % (i + 1))
                else:
                    observations.append(result)
            except Exception as exc:
                err = "Paso %d: %s: %s" % (i + 1, type(exc).__name__, exc)
                errors.append(err)
                results.append({"success": False, "error": err, "step": i + 1})
        summary = self._compile_final_summary(results, errors, plan_name)
        if self.state_manager:
            try:
                self.state_manager.update_progress(steps_total=len(steps), steps_done=len(results), result=json.dumps(summary, default=str, ensure_ascii=False)[:2000])
            except Exception:
                pass
        return {"success": len(errors) == 0, "plan": plan_name, "steps_executed": len(results), "steps_total": len(steps), "results": results, "errors": errors, "summary": summary, "timestamp": datetime.now().isoformat()}

    def _execute_step(self, step, context, observations, step_num):
        action = step.get("action", "")
        if action == "search_and_call":
            query = step.get("query", "")
            params = dict(context)
            params.update(step.get("params", {}))
            result = self._call_by_search(query, params)
            result["purpose"] = step.get("purpose", "")
            result["step"] = step_num
            return result
        elif action == "call_tool":
            tool_name = step.get("tool", "")
            params = dict(context)
            params.update(step.get("params", {}))
            result = self._call_tool(tool_name, params)
            result["purpose"] = step.get("purpose", "")
            result["step"] = step_num
            return result
        elif action == "compile_response":
            template = step.get("template", "general")
            compiled = self._compile_response(template, observations)
            return {"success": True, "action": "compile_response", "template": template, "response": compiled, "step": step_num}
        elif action == "condition":
            return self._evaluate_condition(observations, step.get("field", ""), step.get("operator", "gt"), step.get("value", 0), step_num)
        return {"success": False, "error": "Accion desconocida: %s" % action, "step": step_num}

    def _attempt_correction(self, step, failed_result, context):
        error = failed_result.get("error", "")
        if "no encontrada" in error.lower() or "not found" in error.lower():
            query = step.get("query", step.get("tool", ""))
            if query:
                alt = self._call_by_search(query, context)
                if alt.get("success"):
                    alt["correction"] = "herramienta_alternativa"
                    return alt
        if step.get("params"):
            retry = dict(step)
            retry["params"] = {}
            r = self._execute_step(retry, {}, [], 0)
            if r.get("success"):
                r["correction"] = "reintento_sin_filtros"
                return r
        query = step.get("query", "")
        if query:
            for cat in CATEGORY_SUMMARIES:
                if cat in query.lower():
                    for t in self._find_tools_for_category(cat):
                        result = self._call_tool(t.get("name", ""), context)
                        if result.get("success"):
                            result["correction"] = "alt_cat_%s" % cat
                            return result
                    break
        return None

    def _evaluate_condition(self, observations, field, operator, value, step_num):
        ops = {"gt": lambda a, v: a > v, "lt": lambda a, v: a < v, "eq": lambda a, v: a == v, "gte": lambda a, v: a >= v, "lte": lambda a, v: a <= v, "ne": lambda a, v: a != v}
        for obs in reversed(observations):
            data = obs.get("data", {})
            if isinstance(data, dict) and field in data:
                actual = data[field]
                fn = ops.get(operator)
                met = fn(actual, value) if fn else False
                return {"success": True, "action": "condition", "field": field, "operator": operator, "expected": value, "actual": actual, "met": met, "step": step_num}
        return {"success": False, "action": "condition", "error": "Campo no encontrado: %s" % field, "step": step_num}


    pass

