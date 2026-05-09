"""
reasoning_engine.py — Motor de razonamiento ReAct para la IA Agéntica.
Implementa el ciclo Think -> Act -> Observe con descomposicion de metas,
seleccion autonoma de herramientas y auto-correccion.

Industrialization v5 — Agentic AI Layer
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from tool_registry import (
    get_tool, search_tools, get_tools_by_category,
    get_tool_summary, TOOL_CATALOG,
)
from agent_state import (
    create_session, get_session, update_step,
    complete_session, get_active_sessions,
)
from output_validator import validate_response, format_validation_message


# ══════════════════════════════════════════════════════════
#  PLANES PREDEFINIDOS PARA METAS COMPLEJAS
# ══════════════════════════════════════════════════════════

PLANS: Dict[str, Dict[str, Any]] = {
    "optimizar_inventario": {
        "description": "Analiza ventas recientes, identifica tendencias y sugiere compras",
        "steps": [
            {"tool": "estadisticas_ventas", "params": {"dias": 30}, "thought": "Analizar ventas del ultimo mes"},
            {"tool": "analisis_abc", "params": {}, "thought": "Clasificar productos por importancia"},
            {"tool": "obtener_inventario", "params": {}, "thought": "Revisar stock actual"},
            {"tool": "productos_mas_vendidos", "params": {"dias": 14, "limite": 20}, "thought": "Top productos recientes"},
        ],
    },
    "cierre_fin_semana": {
        "description": "Genera reporte completo de fin de semana",
        "steps": [
            {"tool": "estadisticas_ventas", "params": {"dias": 3}, "thought": "Ventas del fin de semana"},
            {"tool": "estado_caja", "params": {}, "thought": "Estado de caja"},
            {"tool": "corte_caja", "params": {}, "thought": "Corte de caja"},
        ],
    },
    "diagnostico_negocio": {
        "description": "Diagnostico completo del estado del negocio",
        "steps": [
            {"tool": "estadisticas_ventas", "params": {"dias": 7}, "thought": "Ventas de la semana"},
            {"tool": "analisis_abc", "params": {}, "thought": "Analisis ABC de productos"},
            {"tool": "obtener_inventario", "params": {}, "thought": "Estado del inventario"},
            {"tool": "estado_caja", "params": {}, "thought": "Estado de caja"},
            {"tool": "consultar_creditos", "params": {}, "thought": "Creditos pendientes"},
        ],
    },
    "status_clientes": {
        "description": "Reporte de clientes con creditos y compras recientes",
        "steps": [
            {"tool": "buscar_clientes", "params": {}, "thought": "Listar todos los clientes"},
            {"tool": "consultar_creditos", "params": {}, "thought": "Creditos pendientes"},
            {"tool": "estadisticas_ventas", "params": {"dias": 30}, "thought": "Ventas del mes"},
        ],
    },
}


# ══════════════════════════════════════════════════════════
#  MOTORES DE PLANIFICACION Y RAZONAMIENTO
# ══════════════════════════════════════════════════════════

def _detect_plan(user_message: str) -> Optional[str]:
    """Detecta si el mensaje del usuario corresponde a un plan predefinido."""
    msg = user_message.lower()
    plan_keywords = {
        "optimizar_inventario": [
            "optimiza", "optimizar", "inventario", "que comprar",
            "reabastecer", "stock bajo", "pedido", "proveedor",
            "que me falta", "que falto", "proximo fin de semana",
        ],
        "cierre_fin_semana": [
            "cierre", "cerrar", "fin de semana", "resumen del dia",
            "reporte del dia", "corte",
        ],
        "diagnostico_negocio": [
            "diagnostico", "como va", "estado del negocio",
            "resumen general", "reporte completo", "como estamos",
            "situacion", "panorama",
        ],
        "status_clientes": [
            "clientes", "creditos", "quien me debe", "cuentas por cobrar",
            "estado de clientes", "reporte clientes",
        ],
    }
    for plan_id, keywords in plan_keywords.items():
        if any(kw in msg for kw in keywords):
            return plan_id
    return None


def _select_single_tool(user_message: str) -> Optional[str]:
    """Selecciona una herramienta para un objetivo simple (no necesita plan)."""
    msg = user_message.lower()
    single_tool_keywords = {
        "buscar_productos": ["busca", "buscar", "producto", "precio de", "cuanto cuesta"],
        "obtener_inventario": ["stock", "inventario", "cuantos hay", "existencia"],
        "consultar_ventas": ["ventas", "vendido", "venta del dia", "facturas"],
        "estado_caja": ["caja", "dinero", "cuanto hay en caja", "efectivo"],
        "buscar_clientes": ["cliente", "telefono", "contacto"],
        "productos_mas_vendidos": ["mas vendido", "top", "ranking", "popular"],
        "analisis_abc": ["abc", "clasificacion", "categorias de productos"],
        "consultar_creditos": ["credito", "debe", "deuda", "cuentas"],
        "config_sistema": ["configuracion", "configurar", "ajustes", "impuesto"],
        "health_check": ["estado", "sistema", "servidor", "funciona"],
    }
    for tool_name, keywords in single_tool_keywords.items():
        if any(kw in msg for kw in keywords):
            return tool_name
    return None


def _extract_params(tool_name: str, user_message: str) -> Dict[str, Any]:
    """Extrae parametros de un mensaje para una herramienta dada."""
    params: Dict[str, Any] = {}
    msg = user_message.lower()

    # Extraer numeros del mensaje
    import re
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', msg)

    if tool_name in ("estadisticas_ventas", "productos_mas_vendidos") and numbers:
        params["dias"] = int(numbers[0]) if numbers else 7
        if tool_name == "productos_mas_vendidos" and len(numbers) > 1:
            params["limite"] = int(numbers[1])
    elif tool_name == "obtener_inventario":
        # Buscar posibles IDs de producto
        words = msg.split()
        for w in words:
            if w.isalnum() and len(w) >= 2:
                params["producto_id"] = w
                break
    elif tool_name == "buscar_productos":
        query = user_message.strip()
        # Remover verbos comunes
        for verb in ["busca", "buscar", "producto", "encuentra", "dime"]:
            query = query.replace(verb, "", 1)
        params["query"] = query.strip()

    return params


# ══════════════════════════════════════════════════════════
#  CLASE PRINCIPAL: ReActEngine
# ══════════════════════════════════════════════════════════

class ReActEngine:
    """
    Motor de razonamiento ReAct para la IA Agéntica del TPV.
    
    Flujo:
    1. THINK: Analiza el mensaje del usuario y detecta la meta
    2. PLAN: Descompone la meta en pasos (usa planes predefinidos o selecciona herramienta)
    3. ACT: Ejecuta cada paso usando tool_registry
    4. OBSERVE: Valida el resultado con output_validator
    5. CORRECT: Si hay errores, ajusta y reintenta
    6. RESPOND: Compila la respuesta final
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.max_steps = 10
        self.conversation_log: List[Dict[str, str]] = []

    def _log(self, phase: str, content: str):
        """Registra una fase del razonamiento."""
        entry = {
            "phase": phase,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.conversation_log.append(entry)

    def reason(self, user_message: str) -> Dict[str, Any]:
        """
        Punto de entrada principal. Analiza el mensaje y ejecuta el ciclo ReAct.
        Retorna un dict con: response, reasoning_log, tools_used, validation.
        """
        # ── THINK ──
        self._log("THINK", f"Analizando: '{user_message}'")

        plan_id = _detect_plan(user_message)
        single_tool = _select_single_tool(user_message)

        if plan_id:
            return self._execute_plan(plan_id, user_message)
        elif single_tool:
            return self._execute_single_tool(single_tool, user_message)
        else:
            return self._execute_general(user_message)

    def _execute_plan(self, plan_id: str, user_message: str) -> Dict[str, Any]:
        """Ejecuta un plan predefinido multi-paso."""
        plan = PLANS[plan_id]
        session_id = str(uuid.uuid4())[:8]
        tools_used: List[str] = []

        self._log("PLAN", f"Plan detectado: {plan_id} ({len(plan['steps'])} pasos)")

        # Crear sesion persistente
        create_session(session_id, self.user_id, plan["description"], len(plan["steps"]))

        step_results: List[Dict[str, Any]] = []
        for i, step in enumerate(plan["steps"]):
            self._log("THINK", f"Paso {i+1}/{len(plan['steps'])}: {step['thought']}")

            tool_def = get_tool(step["tool"])
            if not tool_def:
                self._log("OBSERVE", f"Herramienta {step['tool']} no encontrada, saltando")
                continue

            self._log("ACT", f"Llamando: {step['tool']}")
            result = self._call_tool(step["tool"], step.get("params", {}))
            tools_used.append(step["tool"])

            # ── OBSERVE ──
            validation = validate_response(result)
            if not validation.is_valid:
                self._log("OBSERVE", f"Problema en paso {i+1}: {format_validation_message(validation)}")

            step_results.append({
                "step": i + 1,
                "tool": step["tool"],
                "thought": step["thought"],
                "result": result,
                "validation": {
                    "is_valid": validation.is_valid,
                    "issues_count": len(validation.issues),
                },
            })

            # Guardar progreso
            update_step(session_id, i + 1, step_results[-1])

        # ── RESPOND ──
        complete_session(session_id, {"steps": len(step_results)})
        response = self._compile_plan_response(plan_id, step_results)

        return {
            "response": response,
            "plan_id": plan_id,
            "session_id": session_id,
            "tools_used": tools_used,
            "steps_completed": len(step_results),
            "reasoning_log": self.conversation_log,
        }

    def _execute_single_tool(self, tool_name: str, user_message: str) -> Dict[str, Any]:
        """Ejecuta una sola herramienta para un objetivo simple."""
        tool_def = get_tool(tool_name)
        if not tool_def:
            return {
                "response": "No encontre una herramienta adecuada para tu consulta.",
                "tools_used": [],
                "reasoning_log": self.conversation_log,
            }

        self._log("PLAN", f"Herramienta directa: {tool_name}")
        params = _extract_params(tool_name, user_message)

        self._log("ACT", f"Llamando: {tool_name}({params})")
        result = self._call_tool(tool_name, params)

        # ── OBSERVE ──
        validation = validate_response(result)
        if not validation.is_valid:
            self._log("OBSERVE", format_validation_message(validation))

        self._log("RESPOND", "Compilando respuesta")

        return {
            "response": self._compile_tool_response(tool_name, result, params),
            "tool_used": tool_name,
            "validation": {"is_valid": validation.is_valid, "issues_count": len(validation.issues)},
            "tools_used": [tool_name],
            "reasoning_log": self.conversation_log,
        }

    def _execute_general(self, user_message: str) -> Dict[str, Any]:
        """Maneja mensajes que no coinciden con planes ni herramientas especificas."""
        self._log("PLAN", "Consulta general, sin herramienta especifica")

        # Buscar herramientas relevantes por texto
        relevant = search_tools(user_message)
        tools_info = [get_tool_summary(t) for t in relevant[:5]]

        response = (
            "Entiendo tu consulta. Estas son las herramientas disponibles "
            "que podrian ayudarte:\n\n"
        )
        if tools_info:
            response += "\n".join(tools_info)
        else:
            response += "No encontre herramientas especificas para tu consulta. "
            response += "Puedo ayudarte con: inventario, ventas, clientes, caja y reportes."

        return {
            "response": response,
            "tools_used": [],
            "reasoning_log": self.conversation_log,
        }

    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta usando funciones internas de database.py"""
        try:
            from database import obtener_conexion

            conn = obtener_conexion()
            conn.row_factory = None
            cursor = conn.cursor()

            if tool_name == "estadisticas_ventas":
                dias = params.get("dias", 7)
                fecha = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
                cursor.execute(
                    "SELECT COUNT(*) as total_ventas, COALESCE(SUM(total),0) as monto_total, "
                    "COALESCE(AVG(total),0) as promedio FROM ventas WHERE fecha >= ?", (fecha,)
                )
                row = cursor.fetchone()
                conn.close()
                return {"total_ventas": row[0], "monto_total": float(row[1] or 0),
                        "promedio": round(float(row[2] or 0), 2), "periodo_dias": dias}

            elif tool_name == "analisis_abc":
                cursor.execute("""
                    SELECT p.nombre, p.categoria, COALESCE(SUM(dv.cantidad),0) as unidades_vendidas,
                           COALESCE(SUM(dv.subtotal),0) as ingreso_total
                    FROM productos p
                    LEFT JOIN detalle_venta dv ON p.producto_id = dv.producto_id
                    LEFT JOIN ventas v ON dv.venta_id = v.venta_id
                    WHERE p.activo = 1 AND v.estado = 'completada'
                    GROUP BY p.producto_id ORDER BY ingreso_total DESC LIMIT 50
                """)
                rows = cursor.fetchall()
                conn.close()
                total_ingreso = sum(r[3] for r in rows) or 1
                clasificacion = []
                acumulado = 0.0
                for r in rows:
                    acumulado += r[3]
                    pct = (acumulado / total_ingreso) * 100
                    cat = "A" if pct <= 80 else ("B" if pct <= 95 else "C")
                    clasificacion.append({
                        "nombre": r[0], "categoria": r[1],
                        "unidades": r[2], "ingreso": float(r[3]),
                        "clasificacion": cat,
                    })
                return {"productos": clasificacion, "total_ingreso": total_ingreso}

            elif tool_name == "obtener_inventario":
                producto_id = params.get("producto_id")
                if producto_id:
                    cursor.execute(
                        "SELECT * FROM inventario_general WHERE producto_id=?", (producto_id,)
                    )
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        cols = [d[0] for d in cursor.description]
                        return dict(zip(cols, row))
                    return {"error": "Producto no encontrado en inventario"}
                else:
                    cursor.execute(
                        "SELECT * FROM inventario_general ORDER BY stock_actual ASC LIMIT 100"
                    )
                    rows = cursor.fetchall()
                    cols = [d[0] for d in cursor.description]
                    conn.close()
                    return {"productos": [dict(zip(cols, r)) for r in rows], "total": len(rows)}

            elif tool_name == "productos_mas_vendidos":
                dias = params.get("dias", 30)
                limite = params.get("limite", 20)
                fecha = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
                cursor.execute("""
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_unidades,
                           SUM(dv.subtotal) as ingreso
                    FROM detalle_venta dv
                    JOIN ventas v ON dv.venta_id = v.venta_id
                    WHERE v.estado = 'completada' AND v.fecha >= ?
                    GROUP BY dv.producto_id ORDER BY total_unidades DESC LIMIT ?
                """, (fecha, limite))
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"top": [dict(zip(cols, r)) for r in rows], "dias": dias}

            elif tool_name == "estado_caja":
                cursor.execute("""
                    SELECT estado, monto_inicial, monto_actual, total_ventas,
                           total_retiros, total_ingresos, fecha_apertura
                    FROM caja WHERE estado = 'abierta' ORDER BY caja_id DESC LIMIT 1
                """)
                row = cursor.fetchone()
                conn.close()
                if row:
                    cols = [d[0] for d in cursor.description]
                    return dict(zip(cols, row))
                return {"estado": "cerrada", "mensaje": "No hay caja abierta"}

            elif tool_name == "consultar_creditos":
                cliente_id = params.get("cliente_id")
                if cliente_id:
                    cursor.execute(
                        "SELECT * FROM creditos WHERE cliente_id=? AND estado='pendiente'",
                        (cliente_id,),
                    )
                else:
                    cursor.execute(
                        "SELECT c.*, cl.nombre as cliente_nombre FROM creditos c "
                        "JOIN clientes cl ON c.cliente_id = cl.cliente_id "
                        "WHERE c.estado = 'pendiente' ORDER BY c.fecha_vencimiento ASC"
                    )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"creditos": [dict(zip(cols, r)) for r in rows], "total": len(rows)}

            elif tool_name == "buscar_productos":
                query = params.get("query", "%")
                cursor.execute(
                    "SELECT producto_id, nombre, precio, categoria, imagen "
                    "FROM productos WHERE activo=1 AND nombre LIKE ? LIMIT 20",
                    (f"%{query}%",),
                )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"productos": [dict(zip(cols, r)) for r in rows], "total": len(rows)}

            elif tool_name == "consultar_ventas":
                dias = params.get("dias", 7)
                fecha = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
                cursor.execute(
                    "SELECT venta_id, total, metodo_pago, estado, fecha "
                    "FROM ventas WHERE fecha >= ? ORDER BY fecha DESC LIMIT 50",
                    (fecha,),
                )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"ventas": [dict(zip(cols, r)) for r in rows], "periodo_dias": dias}

            elif tool_name == "buscar_clientes":
                query = params.get("query", "%")
                cursor.execute(
                    "SELECT cliente_id, nombre, telefono, email "
                    "FROM clientes WHERE nombre LIKE ? OR telefono LIKE ? LIMIT 30",
                    (f"%{query}%", f"%{query}%"),
                )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"clientes": [dict(zip(cols, r)) for r in rows], "total": len(rows)}

            elif tool_name == "corte_caja":
                hoy = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""
                    SELECT metodo_pago, COUNT(*) as num_ventas, SUM(total) as monto
                    FROM ventas WHERE fecha LIKE ? AND estado='completada'
                    GROUP BY metodo_pago
                """, (f"{hoy}%",))
                por_metodo = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"fecha": hoy, "por_metodo": [dict(zip(cols, r)) for r in por_metodo]}

            elif tool_name == "config_sistema":
                clave = params.get("clave")
                if clave:
                    cursor.execute("SELECT clave, valor FROM configuracion WHERE clave=?", (clave,))
                else:
                    cursor.execute("SELECT clave, valor FROM configuracion LIMIT 20")
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                conn.close()
                return {"config": [dict(zip(cols, r)) for r in rows]}

            elif tool_name == "health_check":
                conn.close()
                import os
                from database import DB_PATH
                db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
                return {
                    "status": "ok",
                    "database": "conectada",
                    "db_size_mb": round(db_size / 1024 / 1024, 2),
                    "version": "1.0.0",
                }

            else:
                conn.close()
                return {"error": f"Herramienta no implementada: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _compile_plan_response(
        self, plan_id: str, step_results: List[Dict[str, Any]]
    ) -> str:
        """Compila una respuesta legible a partir de los resultados de un plan."""
        plan = PLANS[plan_id]
        lines = [f"**{plan['description'].upper()}**\n"]

        for sr in step_results:
            tool_name = sr["tool"]
            result = sr["result"]
            valid = sr["validation"]["is_valid"]

            # Formatear resultado segun la herramienta
            if "error" in result:
                lines.append(f"  x Paso {sr['step']} ({tool_name}): Error - {result['error']}")
                continue

            if tool_name == "estadisticas_ventas":
                lines.append(
                    f"  Ventas ({result.get('periodo_dias', 7)} dias): "
                    f"{result.get('total_ventas', 0)} ventas, "
                    f"${result.get('monto_total', 0):,.2f} total, "
                    f"${result.get('promedio', 0):,.2f} promedio"
                )

            elif tool_name == "analisis_abc":
                productos = result.get("productos", [])
                cat_a = [p for p in productos if p.get("clasificacion") == "A"]
                cat_b = [p for p in productos if p.get("clasificacion") == "B"]
                cat_c = [p for p in productos if p.get("clasificacion") == "C"]
                lines.append(
                    f"  Analisis ABC: {len(cat_a)} tipo A, {len(cat_b)} tipo B, {len(cat_c)} tipo C"
                )
                if cat_a:
                    lines.append(f"    Top A: {', '.join(p['nombre'] for p in cat_a[:5])}")

            elif tool_name == "obtener_inventario":
                productos = result.get("productos", [])
                if productos:
                    low_stock = [p for p in productos if p.get("stock_actual", 0) < 5]
                    lines.append(f"  Inventario: {len(productos)} productos, {len(low_stock)} con stock bajo")
                    if low_stock[:5]:
                        for p in low_stock[:5]:
                            lines.append(f"    - {p.get('nombre', '?')}: {p.get('stock_actual', 0)} uds")

            elif tool_name == "productos_mas_vendidos":
                top = result.get("top", [])
                if top:
                    lines.append(f"  Mas vendidos ({result.get('dias', 14)} dias):")
                    for p in top[:5]:
                        lines.append(f"    {p.get('nombre_producto', '?')}: {p.get('total_unidades', 0)} uds")

            elif tool_name == "estado_caja":
                if result.get("estado") == "abierta":
                    lines.append(
                        f"  Caja abierta: ${result.get('monto_actual', 0):,.2f}, "
                        f"ventas ${result.get('total_ventas', 0):,.2f}"
                    )
                else:
                    lines.append("  Caja cerrada")

            elif tool_name == "consultar_creditos":
                creditos = result.get("creditos", [])
                total_cred = sum(c.get("saldo_pendiente", 0) for c in creditos)
                lines.append(f"  Creditos pendientes: {len(creditos)}, ${total_cred:,.2f} total")

            elif tool_name == "corte_caja":
                por_metodo = result.get("por_metodo", [])
                total = sum(m.get("monto", 0) for m in por_metodo)
                lines.append(f"  Corte de caja - Total: ${total:,.2f}")
                for m in por_metodo:
                    lines.append(f"    {m.get('metodo_pago', '?')}: {m.get('num_ventas', 0)} ventas, ${m.get('monto', 0):,.2f}")

            if not valid:
                lines.append("    [!] Datos con advertencias de validacion")

        return "\n".join(lines)

    def _compile_tool_response(
        self, tool_name: str, result: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Compila una respuesta legible para una herramienta individual."""
        if "error" in result:
            return f"No pude obtener la informacion: {result['error']}"

        if tool_name == "buscar_productos":
            productos = result.get("productos", [])
            if not productos:
                return "No encontre productos con esa busqueda."
            lines = [f"Encontre {len(productos)} producto(s):"]
            for p in productos[:10]:
                lines.append(f"  - {p.get('nombre', '?')}: ${p.get('precio', 0):,.2f}")
            if len(productos) > 10:
                lines.append(f"  ... y {len(productos) - 10} mas")
            return "\n".join(lines)

        elif tool_name == "obtener_inventario":
            if "productos" in result:
                productos = result["productos"]
                lines = [f"Inventario ({result.get('total', 0)} productos):"]
                for p in productos[:15]:
                    lines.append(f"  - {p.get('nombre', '?')}: {p.get('stock_actual', 0)} uds")
                return "\n".join(lines)
            else:
                p = result
                return f"{p.get('nombre', '?')}: {p.get('stock_actual', 0)} unidades en stock"

        elif tool_name == "estado_caja":
            if result.get("estado") == "abierta":
                return (
                    f"Caja abierta desde {result.get('fecha_apertura', '?')}\n"
                    f"Monto inicial: ${result.get('monto_inicial', 0):,.2f}\n"
                    f"Ventas del dia: ${result.get('total_ventas', 0):,.2f}\n"
                    f"Retiros: ${result.get('total_retiros', 0):,.2f}\n"
                    f"Ingresos: ${result.get('total_ingresos', 0):,.2f}\n"
                    f"Saldo actual: ${result.get('monto_actual', 0):,.2f}"
                )
            return "La caja esta cerrada. Necesitas abrirla para iniciar ventas."

        elif tool_name == "estadisticas_ventas":
            return (
                f"Estadisticas de ventas ({result.get('periodo_dias', 7)} dias):\n"
                f"  Total ventas: {result.get('total_ventas', 0)}\n"
                f"  Monto total: ${result.get('monto_total', 0):,.2f}\n"
                f"  Promedio por venta: ${result.get('promedio', 0):,.2f}"
            )

        elif tool_name == "consultar_ventas":
            ventas = result.get("ventas", [])
            total = sum(v.get("total", 0) for v in ventas)
            return f"Ventas recientes ({result.get('periodo_dias', 7)} dias): {len(ventas)} ventas, ${total:,.2f} total"

        elif tool_name == "analisis_abc":
            productos = result.get("productos", [])
            a = [p for p in productos if p.get("clasificacion") == "A"]
            lines = [f"Analisis ABC ({len(productos)} productos):"]
            lines.append(f"  Tipo A (alto valor): {len(a)} productos")
            for p in a[:5]:
                lines.append(f"    - {p['nombre']}: ${p['ingreso']:,.2f}")
            return "\n".join(lines)

        elif tool_name == "productos_mas_vendidos":
            top = result.get("top", [])
            lines = [f"Top {len(top)} productos mas vendidos ({result.get('dias', 30)} dias):"]
            for i, p in enumerate(top, 1):
                lines.append(f"  {i}. {p.get('nombre_producto', '?')}: {p.get('total_unidades', 0)} uds - ${p.get('ingreso', 0):,.2f}")
            return "\n".join(lines)

        elif tool_name == "consultar_creditos":
            creditos = result.get("creditos", [])
            if not creditos:
                return "No hay creditos pendientes."
            total = sum(c.get("saldo_pendiente", 0) for c in creditos)
            lines = [f"Creditos pendientes: {len(creditos)}, total ${total:,.2f}"]
            for c in creditos[:10]:
                lines.append(f"  - {c.get('cliente_nombre', '?')}: ${c.get('saldo_pendiente', 0):,.2f}")
            return "\n".join(lines)

        elif tool_name == "health_check":
            return f"Sistema OK. BD: {result.get('database', '?')} ({result.get('db_size_mb', 0)} MB)"

        elif tool_name == "corte_caja":
            por_metodo = result.get("por_metodo", [])
            total = sum(m.get("monto", 0) for m in por_metodo)
            lines = [f"Corte de caja ({result.get('fecha', '')}): Total ${total:,.2f}"]
            for m in por_metodo:
                lines.append(f"  {m.get('metodo_pago', '?')}: {m.get('num_ventas', 0)} ventas = ${m.get('monto', 0):,.2f}")
            return "\n".join(lines)

        else:
            return str(result)
