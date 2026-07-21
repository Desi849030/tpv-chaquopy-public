"""High-value behaviour tests for ReAct execution, templates, and IA memory."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FakeTool:
    name: str
    description: str
    category: str
    route: str
    method: str = "GET"
    params: list | None = None


class FakeResponse:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self._data = data

    def get_json(self, silent=True):
        return self._data

    def get_data(self, as_text=False):
        return "raw response"


class FakeClient:
    def get(self, endpoint, **kwargs):
        return FakeResponse(200, {"total": 25, "items": [1, 2]})

    def post(self, endpoint, **kwargs):
        return FakeResponse(201, {"ok": True})

    def put(self, endpoint, **kwargs):
        return FakeResponse(200, {"updated": True})

    def delete(self, endpoint, **kwargs):
        return FakeResponse(204, None)

    def patch(self, endpoint, **kwargs):
        return FakeResponse(200, {"patched": True})


def _react_engine():
    from ia.react_core import ReActEngine
    from ia.react_templates import ReActEngineTemplates

    class Engine(ReActEngine, ReActEngineTemplates):
        pass

    engine = Engine(app=None, session_id="react-coverage")
    engine.client = FakeClient()
    tools = [
        FakeTool("sales_get", "Consultar ventas", "ventas", "/sales", "GET", [{"name": "q"}]),
        FakeTool("item_post", "Crear producto", "productos", "/items", "POST", []),
        FakeTool("item_put", "Actualizar producto", "productos", "/items", "PUT", []),
        FakeTool("item_delete", "Eliminar producto", "productos", "/items", "DELETE", []),
        FakeTool("item_patch", "Editar producto", "productos", "/items", "PATCH", []),
        FakeTool("unsupported", "Metodo invalido", "otros", "/bad", "TRACE", []),
    ]
    engine.tool_catalog = {tool.name: tool for tool in tools}
    engine.category_index = {
        "ventas": ["sales_get"],
        "productos": ["item_post", "item_put", "item_delete", "item_patch"],
    }
    return engine


def test_react_tool_resolution_and_http_methods(monkeypatch):
    import ia.react_core as core

    engine = _react_engine()
    assert engine._find_tool("sales_get").name == "sales_get"
    assert engine._find_tool("sales").name == "sales_get"
    assert engine._find_tool("consultar ventas").name == "sales_get"
    assert engine._find_tool("") is None
    assert engine._find_tools_for_category("productos")

    for name in ("sales_get", "item_post", "item_put", "item_delete", "item_patch"):
        result = engine._call_tool(name, {"q": "hoy", "ignored": True})
        assert result["success"]
    assert not engine._call_tool("unsupported")["success"]
    assert not engine._call_tool("missing")["success"]
    assert engine._call_by_search("consultar ventas")["success"]

    monkeypatch.setattr(core, "search_tools", lambda query: [])
    assert engine._find_tool("sin coincidencia") is None


def test_react_steps_conditions_corrections_and_plans(monkeypatch):
    engine = _react_engine()
    steps = [
        {"action": "call_tool", "tool": "sales_get", "purpose": "ventas", "params": {"q": "hoy"}},
        {"action": "search_and_call", "query": "consultar ventas", "purpose": "busqueda"},
        {"action": "condition", "field": "total", "operator": "gte", "value": 20},
        {"action": "compile_response", "template": "general"},
    ]
    result = engine.execute_plan(plan_name="custom", steps=steps, context={"store": "one"})
    assert result["success"]
    assert result["steps_executed"] == 4
    assert result["summary"]

    unknown = engine._execute_step({"action": "unknown"}, {}, [], 1)
    assert not unknown["success"]
    missing = engine._evaluate_condition([], "total", "gt", 0, 1)
    assert not missing["success"]
    for op in ("gt", "lt", "eq", "gte", "lte", "ne"):
        checked = engine._evaluate_condition([{"data": {"n": 2}}], "n", op, 1, 1)
        assert checked["success"]

    monkeypatch.setattr(engine, "_call_by_search", lambda query, params=None: {"success": True})
    fixed = engine._attempt_correction(
        {"query": "ventas"}, {"error": "No encontrada"}, {}
    )
    assert fixed and fixed["correction"] == "herramienta_alternativa"
    assert not engine.execute_plan(plan_name="does-not-exist")["success"]


def test_all_response_template_compilers():
    engine = _react_engine()
    inventory = [
        {"purpose": "alerta stock", "data": {"alertas": [{"nombre": "Cafe", "stock": 1}]}},
        {"purpose": "mas vendido", "data": {"productos": [{"nombre": "Pan", "total_vendido": 8}]}},
    ]
    assert "OPTIMIZACION" in engine._compile_inventory_optimization(inventory)
    assert "No se pudo" in engine._compile_inventory_optimization([])
    assert "Ticket promedio" in engine._compile_closing_summary([
        {"data": {"total": 100.0, "transacciones": 4}}
    ])
    assert "DIAGNOSTICO" in engine._compile_business_diagnosis([
        {"purpose": "ventas", "data": {"total": 100.0, "cantidad": 4, "items": [1]}}
    ])
    assert "insuficientes" in engine._compile_business_diagnosis([])
    assert "Ana" in engine._compile_client_status([
        {"data": {"clientes": [{"nombre": "Ana", "puntos": 20}]}}
    ])
    assert "admin" in engine._compile_security_audit([
        {"data": {"logs": [{"timestamp": "2026", "usuario": "admin", "accion": "login"}]}}
    ])
    assert "$50.00" in engine._compile_sales_report([{"data": {"total": 50.0}}])
    assert "2 ventas" in engine._compile_sales_report([{"data": [1, 2]}])
    assert "CON ERRORES" in engine._compile_final_summary(
        [{"success": True}, {"success": False}], ["fallo"], "plan"
    )
    general = engine._compile_general([
        {"purpose": "datos", "data": {"total": 2.5, "count": 2, "rows": [1, 2]}},
        {"data": [1, 2, 3]},
    ])
    assert "datos" in general and "3 registros" in general
    assert engine._compile_response("nonexistent", [{"data": {"ok": 1}}])


def test_memory_complete_lifecycle():
    from ia import memory_core as memory

    memory._DB_PATH = None
    assert memory.init()
    assert not memory.save(key="", value="")
    assert memory.save(
        session_id="s1", category="prefs", key="drink", value="cafe",
        metadata={"source": "test"}, confidence=0.9, expires_days=2,
    )
    # Exercise the update/upsert branch.
    assert memory.save(
        session_id="s1", category="prefs", key="drink", value="espresso",
        metadata={"updated": True}, confidence=1.0,
    )
    assert memory.save(session_id="s1", category="sales", key="product", value="pan integral")

    assert memory.recall("s1", key="drink")[0]["value"] == "espresso"
    assert memory.recall("s1", category="prefs")
    assert len(memory.recall("s1")) == 2
    assert memory.search("espresso", session_id="s1", category="prefs")
    assert memory.search("pan integral", session_id="s1")
    assert memory.search("x") == []
    summary = memory.get_summary("s1")
    assert summary["total"] == 2
    assert "prefs" in summary["categories"]

    assert memory.forget("s1", category="prefs", key="drink")
    assert memory.forget("s1", category="sales")
    assert memory.save(session_id="s1", category="one", key="a", value="1")
    assert memory.forget("s1", key="a")
    assert memory.save(session_id="s1", category="all", key="b", value="2")
    assert memory.forget("s1")
    assert memory.recall("s1") == []
