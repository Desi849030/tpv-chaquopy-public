# -*- coding: utf-8 -*-
"""
react_templates.py - ReActEngine template compilers + query processor (Mixin)
"""
from __future__ import annotations

import json
from datetime import datetime

from ia.react_categories import CATEGORY_SUMMARIES
from ia.react_plans import PREDEFINED_PLANS

class ReActEngineTemplates:
    """Mixin: _compile_* methods + process_query para ReActEngine."""

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


    pass

