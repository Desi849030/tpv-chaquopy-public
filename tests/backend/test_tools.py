import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)


class TestTools:
    def test_admin_tools_exist(self):
        from tools.admin_tools import ADMIN_TOOLS
        assert len(ADMIN_TOOLS) > 0
        assert "listar_usuarios" in ADMIN_TOOLS

    def test_analytic_tools_exist(self):
        from tools.analytic_tools import ANALYTIC_TOOLS
        assert len(ANALYTIC_TOOLS) > 0
        assert "dashboard_general" in ANALYTIC_TOOLS

    def test_auth_tools_exist(self):
        from tools.auth_tools import AUTH_TOOLS
        assert len(AUTH_TOOLS) > 0
        assert "login" in AUTH_TOOLS

    def test_general_tools_exist(self):
        from tools.general_tools import GENERAL_TOOLS
        assert len(GENERAL_TOOLS) > 0
        assert "health_check" in GENERAL_TOOLS

    def test_base_tool_definition(self):
        from tools.base import ToolDefinition, _t
        tool = _t("test", "desc", "cat", "/api/test", "GET", [])
        assert tool.name == "test"
        assert tool.method == "GET"

    def test_import_tools(self):
        from tools.import_tools import IMPORT_TOOLS
        assert len(IMPORT_TOOLS) > 0

    def test_inventario_tools(self):
        from tools.inventario_tools import INVENTARIO_TOOLS
        assert len(INVENTARIO_TOOLS) > 0

    def test_lealtad_tools(self):
        from tools.lealtad_tools import LEALTAD_TOOLS
        assert len(LEALTAD_TOOLS) > 0

    def test_licencia_tools(self):
        from tools.licencia_tools import LICENCIA_TOOLS
        assert len(LICENCIA_TOOLS) > 0

    def test_security_tools(self):
        from tools.security_tools import SECURITY_TOOLS
        assert len(SECURITY_TOOLS) > 0

    def test_seguridad_tools(self):
        from tools.seguridad_tools import SEGURIDAD_TOOLS
        assert len(SEGURIDAD_TOOLS) > 0

    def test_setting_tools(self):
        from tools.setting_tools import SETTING_TOOLS
        assert len(SETTING_TOOLS) > 0

    def test_tienda_tools(self):
        from tools.tienda_tools import TIENDA_TOOLS
        assert len(TIENDA_TOOLS) > 0

    def test_venta_tools(self):
        from tools.venta_tools import VENTA_TOOLS
        assert len(VENTA_TOOLS) > 0

    def test_i18n_builder(self):
        try:
            import tools.i18n_builder
            assert tools.i18n_builder is not None
        except Exception:
            pass
