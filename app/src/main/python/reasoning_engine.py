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
    from tool_registry import get_tool, list_tools_by_category, search_tools, get_catalog_stats
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

CATEGORY_SUMMARIES = {
    "inventario": "productos stock categorias alertas inventario",
    "ventas": "ventas carrito facturacion transacciones historial",
    "clientes": "clientes compras contacto datos",
    "analytics": "estadisticas metricas vendidos negocio",
    "admin": "administracion usuarios permisos sistema",
    "auth": "autenticacion login logout tokens",
    "tienda": "tienda negocio horarios metodos pago",
    "licencia": "licencia activacion renovacion limites",
    "lealtad": "puntos recompensas frecuente",
    "seguridad": "auditoria logs bloqueos acceso",
    "websocket": "tiempo real notificaciones sincronizacion",
    "settings": "configuracion preferencias tema idioma",
    "validacion": "validacion importacion datos sanitizacion",
    "ia_assistant": "asistente conversacion contexto herramientas",
    "general": "salud sistema api utilidades",
}

PREDEFINED_PLANS = {
    "optimizar_inventario": {
        "description": "Analiza stock bajo y sugiere reorden",
        "steps": [
            {"action": "search_and_call", "query": "inventario alerta stock", "purpose": "Alertas de stock bajo"},
            {"action": "search_and_call", "query": "analytics vendido", "purpose": "Productos mas vendidos"},
            {"action": "search_and_call", "query": "inventario producto listar", "purpose": "Inventario actual"},
            {"action": "compile_response", "template": "inventory_optimization"},
        ],
    },
    "cierre_fin_semana": {
        "description": "Resumen financiero para cierre de caja",
        "steps": [
            {"action": "search_and_call", "query": "ventas resumen total", "purpose": "Resumen de ventas"},
            {"action": "search_and_call", "query": "analytics estadistica", "purpose": "Estadisticas"},
            {"action": "search_and_call", "query": "finanza reporte", "purpose": "Reporte financiero"},
            {"action": "compile_response", "template": "closing_summary"},
        ],
    },
    "diagnostico_negocio": {
        "description": "Diagnostico completo del negocio",
        "steps": [
            {"action": "search_and_call", "query": "analytics", "purpose": "Metricas de negocio"},
            {"action": "search_and_call", "query": "inventario", "purpose": "Estado inventario"},
            {"action": "search_and_call", "query": "ventas", "purpose": "Actividad ventas"},
            {"action": "search_and_call", "query": "cliente", "purpose": "Base de clientes"},
            {"action": "compile_response", "template": "business_diagnosis"},
        ],
    },
    "status_clientes": {
        "description": "Reporte de clientes y lealtad",
        "steps": [
            {"action": "search_and_call", "query": "cliente listar", "purpose": "Lista de clientes"},
            {"action": "search_and_call", "query": "lealtad puntos", "purpose": "Puntos de lealtad"},
            {"action": "search_and_call", "query": "analytics cliente", "purpose": "Metricas clientes"},
            {"action": "compile_response", "template": "client_status"},
        ],
    },
    "auditoria_seguridad": {
        "description": "Revision de logs y politicas de seguridad",
        "steps": [
            {"action": "search_and_call", "query": "seguridad auditoria log", "purpose": "Logs de auditoria"},
            {"action": "search_and_call", "query": "admin usuario", "purpose": "Usuarios del sistema"},
            {"action": "search_and_call", "query": "seguridad politica", "purpose": "Politicas seguridad"},
            {"action": "compile_response", "template": "security_audit"},
        ],
    },
    "reporte_ventas_periodo": {
        "description": "Reporte de ventas para un periodo",
        "steps": [
            {"action": "search_and_call", "query": "ventas historial", "purpose": "Historial ventas"},
            {"action": "search_and_call", "query": "analytics producto", "purpose": "Mas vendidos"},
            {"action": "search_and_call", "query": "analytics estadistica", "purpose": "Estadisticas"},
            {"action": "compile_response", "template": "sales_report"},
        ],
    },
}


class ReActEngine:
    """Motor ReAct: ejecuta herramientas del tool_registry via Flask test_client()."""

    def __init__(self, app=None, session_id=None):
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


    def _compile_response(self, template, observations):
        compiler = getattr(self, "_compile_" + template, self._compile_general)
        try:
            return compiler(observations)
        except Exception:
            return self._compile_general(observations)

    def _compile_general(self, observations):
        if not observations:
            return "No se obtuvieron resultados."
        parts = []
        for obs in observations:
            purpose = obs.get("purpose", "")
            data = obs.get("data", {})
            if purpose:
                parts.append("## " + purpose)
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, float):
                        parts.append("- %s: %0.2f" % (key, value))
                    elif isinstance(value, int):
                        parts.append("- %s: %d" % (key, value))
                    elif isinstance(value, list):
                        parts.append("- %s: %d items" % (key, len(value)))
                    else:
                        parts.append("- %s: %s" % (key, str(value)))
            elif isinstance(data, list):
                parts.append("- %d registros" % len(data))
        return "\n".join(parts)

    def _compile_inventory_optimization(self, obs_list):
        lines = ["=== OPTIMIZACION INVENTARIO ===", ""]
        for obs in obs_list:
            purpose = obs.get("purpose", "")
            data = obs.get("data", {})
            if not isinstance(data, dict):
                continue
            if "alerta" in purpose.lower() or "stock" in purpose.lower():
                lines.append("[!] ALERTAS STOCK")
                prods = data.get("productos", data.get("data", data.get("alertas", [])))
                if isinstance(prods, list):
                    for p in prods[:10]:
                        if isinstance(p, dict):
                            lines.append("  - %s: %s uds" % (p.get("nombre", p.get("name", "?")), p.get("stock", p.get("cantidad", "?"))))
                lines.append("")
            elif "vendido" in purpose.lower():
                lines.append("[*] MAS VENDIDOS")
                prods = data.get("productos", data.get("data", []))
                if isinstance(prods, list):
                    for i, p in enumerate(prods[:5], 1):
                        if isinstance(p, dict):
                            lines.append("  %d. %s: %s ventas" % (i, p.get("nombre", "?"), p.get("total_vendido", "?")))
                lines.append("")
        if len(lines) <= 2:
            lines.append("No se pudo generar el reporte.")
        return "\n".join(lines)

    def _compile_closing_summary(self, obs_list):
        lines = ["=== CIERRE CAJA ===", "Fecha: " + datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
        tv = 0
        tt = 0
        for obs in obs_list:
            data = obs.get("data", {})
            if not isinstance(data, dict):
                continue
            tot = data.get("total", data.get("total_ventas", 0))
            cnt = data.get("transacciones", 0)
            if isinstance(tot, (int, float)):
                tv += tot
            if isinstance(cnt, (int, float)):
                tt += int(cnt)
        lines.append("[*] Total: $%0.2f" % tv)
        lines.append("[*] Transacciones: %d" % tt)
        if tt > 0:
            lines.append("[*] Ticket promedio: $%0.2f" % (tv / tt))
        return "\n".join(lines)

    def _compile_business_diagnosis(self, obs_list):
        lines = ["=== DIAGNOSTICO NEGOCIO ===", datetime.now().strftime("%Y-%m-%d"), ""]
        for obs in obs_list:
            data = obs.get("data", {})
            purpose = obs.get("purpose", "")
            if not isinstance(data, dict):
                continue
            lines.append("--- %s ---" % (purpose.upper() if purpose else "SECCION"))
            for k, v in data.items():
                if isinstance(v, float):
                    lines.append("  %s: %0.2f" % (k, v))
                elif isinstance(v, int):
                    lines.append("  %s: %d" % (k, v))
                elif isinstance(v, list):
                    lines.append("  %s: %d registros" % (k, len(v)))
            lines.append("")
        if len(lines) <= 3:
            lines.append("Datos insuficientes.")
        return "\n".join(lines)

    def _compile_client_status(self, obs_list):
        lines = ["=== ESTADO CLIENTES ===", ""]
        for obs in obs_list:
            data = obs.get("data", {})
            clients = data if isinstance(data, list) else data.get("clientes", data.get("data", []))
            if isinstance(clients, list):
                for c in clients[:8]:
                    if isinstance(c, dict):
                        nm = c.get("nombre", c.get("name", "?"))
                        pt = c.get("puntos", c.get("points", ""))
                        line = "  - " + nm
                        if pt:
                            line += " | " + str(pt) + " pts"
                        lines.append(line)
                lines.append("")
        return "\n".join(lines) if len(lines) > 1 else "Sin datos de clientes."

    def _compile_security_audit(self, obs_list):
        lines = ["=== AUDITORIA SEGURIDAD ===", datetime.now().strftime("%Y-%m-%d"), ""]
        for obs in obs_list:
            data = obs.get("data", {})
            if not isinstance(data, dict):
                continue
            logs = data.get("logs", data.get("data", data.get("auditoria", [])))
            if isinstance(logs, list):
                lines.append("  Registros: %d" % len(logs))
                for lg in logs[:5]:
                    if isinstance(lg, dict):
                        lines.append("  [%s] %s: %s" % (lg.get("timestamp", lg.get("fecha", "")), lg.get("usuario", lg.get("user", "?")), lg.get("accion", lg.get("action", "?"))))
            lines.append("")
        return "\n".join(lines) if len(lines) > 2 else "Sin datos."

    def _compile_sales_report(self, obs_list):
        lines = ["=== REPORTE VENTAS ===", datetime.now().strftime("%Y-%m-%d"), ""]
        for obs in obs_list:
            data = obs.get("data", {})
            if isinstance(data, dict) and "total" in data:
                lines.append("[*] Total: $%0.2f" % data["total"])
            elif isinstance(data, list):
                lines.append("[*] %d ventas" % len(data))
            lines.append("")
        return "\n".join(lines) if len(lines) > 2 else "Sin datos."

    def _compile_final_summary(self, results, errors, plan_name):
        ok = sum(1 for r in results if r.get("success"))
        fail = len(results) - ok
        lines = ["Plan: " + (plan_name or "custom"), "Resultado: " + ("EXITOSO" if fail == 0 else "CON ERRORES"), "Pasos: %d ok, %d fail" % (ok, fail)]
        if errors:
            lines.append("Errores:")
            for e in errors:
                lines.append("  - " + e)
        return "\n".join(lines)

    def process_query(self, user_query, session_id=None):
        if session_id and not self.session_id:
            self.session_id = session_id
        ql = user_query.lower()
        plan_kw = {
            "optimizar_inventario": ["inventario", "stock", "reorden", "optimizar"],
            "cierre_fin_semana": ["cierre", "caja", "resumen dia"],
            "diagnostico_negocio": ["diagnostico", "estado negocio", "metricas", "salud"],
            "status_clientes": ["cliente", "frecuente", "lealtad", "puntos"],
            "auditoria_seguridad": ["seguridad", "auditoria", "log", "acceso"],
            "reporte_ventas_periodo": ["reporte venta", "ventas periodo", "historial venta"],
        }
        for pname, kws in plan_kw.items():
            if any(kw in ql for kw in kws):
                return self.execute_plan(plan_name=pname)
        dynamic = self._build_dynamic_plan(user_query)
        if dynamic:
            return self.execute_plan(steps=dynamic)
        return {"success": False, "error": "No se determino plan. Pruebe: inventario, cierre, diagnostico, clientes, seguridad, ventas.", "query": user_query}

    def _build_dynamic_plan(self, query):
        ql = query.lower()
        steps = []
        for cat, summary in CATEGORY_SUMMARIES.items():
            if any(w in ql for w in summary.split() if len(w) > 3):
                for tool in self._find_tools_for_category(cat)[:2]:
                    steps.append({"action": "call_tool", "tool": tool.get("name", ""), "purpose": tool.get("description", "")})
        if not steps:
            tool = self._find_tool(query)
            if tool:
                steps.append({"action": "call_tool", "tool": tool.get("name", ""), "purpose": tool.get("description", "")})
        if steps:
            steps.append({"action": "compile_response", "template": "general"})
        return steps


def get_engine_status(app=None):
    engine = ReActEngine(app=app)
    return engine.get_status()


def list_available_plans():
    return {"plans": list(PREDEFINED_PLANS.keys()), "details": {n: p.get("description", "") for n, p in PREDEFINED_PLANS.items()}}
