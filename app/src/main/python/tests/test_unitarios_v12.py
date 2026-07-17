# -*- coding: utf-8 -*-
"""Tests unitarios puros — NO necesitan BD.
Ejecutar:  python -m pytest tests/test_unitarios_v12.py -v
"""
import os, sys, math

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TEST_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class TestMatematicas:
    """Modelos matemáticos puros (sin BD)."""

    def test_regresion_lineal_perfecta(self):
        from ia.metrics import M
        m, b = M.regresion([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        assert abs(m - 2.0) < 0.01
        assert abs(b - 0.0) < 0.01

    def test_regresion_con_intercepto(self):
        from ia.metrics import M
        m, b = M.regresion([1, 2, 3], [5, 7, 9])
        assert abs(m - 2.0) < 0.01
        assert abs(b - 3.0) < 0.01

    def test_regresion_un_punto(self):
        from ia.metrics import M
        m, b = M.regresion([1], [5])
        assert m == 0
        assert b == 0

    def test_eoq_formula(self):
        from ia.metrics import M
        # EOQ = sqrt(2*D*P/M)
        # D=3600, P=50, M=2 => EOQ = sqrt(180000) = 424.26
        result = M.eoq(3600, 50, 2)
        expected = math.sqrt(2 * 3600 * 50 / 2)
        assert abs(result - expected) < 0.01

    def test_eoq_cero_costo(self):
        from ia.metrics import M
        assert M.eoq(100, 50, 0) == 0

    def test_punto_equilibrio_normal(self):
        from ia.metrics import M
        # CF=10000, P=100, CV=60 => PE = 10000/40 = 250
        assert M.punto_eq(10000, 100, 60) == 250

    def test_punto_equilibrio_loss(self):
        from ia.metrics import M
        # P < CV => infinito
        assert M.punto_eq(1000, 10, 15) == float('inf')

    def test_punto_equilibrio_zero_cv(self):
        from ia.metrics import M
        assert M.punto_eq(1000, 100, 0) == 10

    def test_roi_positivo(self):
        from ia.metrics import M
        assert M.roi(1000, 1500) == 50.0

    def test_roi_negativo(self):
        from ia.metrics import M
        assert M.roi(1000, 500) == -50.0

    def test_roi_cero_inversion(self):
        from ia.metrics import M
        assert M.roi(0, 500) == 0


class TestFormatters:
    """Formateadores de dinero y porcentaje."""

    def test_fmt_money_entero(self):
        from ia.db_utils import fmt_money
        assert fmt_money(100) == "$100.00"

    def test_fmt_money_decimal(self):
        from ia.db_utils import fmt_money
        assert fmt_money(1234.56) == "$1,234.56"

    def test_fmt_money_cero(self):
        from ia.db_utils import fmt_money
        assert fmt_money(0) == "$0.00"

    def test_fmt_money_none(self):
        from ia.db_utils import fmt_money
        assert fmt_money(None) == "$0.00"

    def test_pct_normal(self):
        from ia.db_utils import pct
        assert pct(85.5) == "85.5%"

    def test_pct_cero(self):
        from ia.db_utils import pct
        assert pct(0) == "0.0%"


class TestNormalizar:
    """Normalización de texto para búsqueda."""

    def test_quita_tildes(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("Café") == "cafe"
        assert _normalizar("Acción") == "accion"
        assert _normalizar("Información") == "informacion"

    def test_minusculas(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("CAFÉ MOLIDO") == "cafe molido"

    def test_vacio(self):
        from ia.handlers_cliente import _normalizar
        assert _normalizar("") == ""
        assert _normalizar(None) == ""


class TestRolesRegistry:
    """Registro de roles del agente."""

    def test_roles_existentes(self):
        from ia.agent import ROLES
        roles_requeridos = ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']
        for r in roles_requeridos:
            assert r in ROLES, f"Falta rol: {r}"

    def test_roles_tienen_label(self):
        from ia.agent import ROLES
        for r, data in ROLES.items():
            assert 'label' in data, f"Rol {r} sin label"
            assert 'color' in data, f"Rol {r} sin color"

    def test_roles_unicos(self):
        from ia.agent import ROLES
        labels = [d['label'] for d in ROLES.values()]
        assert len(labels) == len(set(labels)), "Labels duplicados"


class TestAgentGetStatus:
    """Status del agente."""

    def test_status_fields(self):
        from ia.agent import get_status
        s = get_status()
        assert 'status' in s
        assert 'version' in s or 'versión' in s

    def test_status_active(self):
        from ia.agent import get_status
        s = get_status()
        assert s['status'] == 'active'

    def test_features_list(self):
        from ia.agent import get_status
        s = get_status()
        assert 'features' in s
        assert len(s['features']) > 0


class TestHandlersBase:
    """Funciones base sin BD."""

    def test_follow_todos_roles(self):
        from ia.handlers_base import _follow
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = _follow(rol)
            assert isinstance(r, str)
            assert len(r) > 5

    def test_get_sug_todos_roles(self):
        from ia.handlers_base import _get_sug
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = _get_sug(rol)
            assert isinstance(r, list)

    def test_greet_todos_roles(self):
        from ia.handlers_base import greet
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = greet(rol, "Test")
            assert isinstance(r, str)
            assert len(r) > 3

    def test_help_text_todos_roles(self):
        from ia.handlers_base import help_text
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = help_text(rol)
            assert isinstance(r, str)
            assert len(r) > 3

    def test_handle_unknown(self):
        from ia.handlers_base import handle_unknown
        r = handle_unknown("xyz")
        assert "No entendí" in r


class TestProactiveAlerts:
    """Alertas proactivas del agente."""

    def test_alerts_structure(self):
        from ia.agent import get_proactive_alerts
        a = get_proactive_alerts("test-session")
        assert 'alerts' in a
        assert isinstance(a['alerts'], list)


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    sys.exit(result.returncode)
