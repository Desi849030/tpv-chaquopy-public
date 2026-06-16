"""Tests de limpieza de rutas duplicadas en ventas/reportes."""
import os
import sys

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestRutasSinDuplicados:
    def test_no_hay_blueprint_legacy_sales(self, app):
        reglas = list(app.url_map.iter_rules())
        sales_rules = [r.rule for r in reglas if r.endpoint.startswith("sales.")]
        assert sales_rules == []

    def test_resumen_ventas_no_esta_duplicado(self, app):
        reglas = [r.rule for r in app.url_map.iter_rules() if r.rule == "/api/reportes/resumen"]
        assert len(reglas) == 1

    def test_reportes_ventas_no_esta_duplicado(self, app):
        reglas = [r.rule for r in app.url_map.iter_rules() if r.rule == "/api/reportes/ventas"]
        assert len(reglas) == 1

    def test_reportes_ganancias_no_esta_duplicado(self, app):
        reglas = [r.rule for r in app.url_map.iter_rules() if r.rule == "/api/reportes/ganancias"]
        assert len(reglas) == 1
