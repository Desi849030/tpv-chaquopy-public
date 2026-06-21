import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"


class TestTelecomDiag:
    def test_medir_dns_ok(self):
        from modules.telecom_diag import medir_dns
        result = medir_dns()
        assert result["ok"] == True
        assert "ip_principal" in result

    def test_info_red_local_ok(self):
        from modules.telecom_diag import info_red_local
        result = info_red_local()
        assert result["ok"] == True
        assert "ip_local" in result

    def test_velocidad_sqlite_ok(self):
        from modules.telecom_diag import velocidad_sqlite
        result = velocidad_sqlite()
        assert result["ok"] == True
        assert result["ops_por_segundo"] > 0

    def test_diagnostico_completo_ok(self):
        from modules.telecom_diag import diagnostico_completo
        result = diagnostico_completo()
        assert result["ok"] == True
        assert "dns" in result
        assert "sqlite" in result

    def test_formato_humano_diagnostico(self):
        from modules.telecom_diag import formato_humano_diagnostico
        result = formato_humano_diagnostico()
        assert isinstance(result, str)
        assert len(result) > 0
