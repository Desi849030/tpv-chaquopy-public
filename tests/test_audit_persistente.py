"""test_audit_persistente.py — Las alertas de seguridad se persisten en SQLite
y sobreviven al reinicio (antes solo vivían en memoria)."""
import os, sys, pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


@pytest.fixture(scope="module")
def _db(tmp_db_dir):
    from database import crear_tablas
    crear_tablas()
    return True


class TestAuditPersistente:
    def test_alerta_se_persiste(self, _db):
        import security_het as het
        het.add_alert("CRITICAL", "BRUTE_FORCE", "1.2.3.4", "5 intentos")
        pers = het.get_alerts(persisted=True)
        assert any(a["type"] == "BRUTE_FORCE" and a["source"] == "1.2.3.4" for a in pers)

    def test_filtro_por_nivel_persistido(self, _db):
        import security_het as het
        het.add_alert("WARN", "RATE_LIMIT", "9.9.9.9", "130/min")
        crit = het.get_alerts(level="CRITICAL", persisted=True)
        assert all(a["level"] == "CRITICAL" for a in crit)

    def test_sobrevive_reinicio_memoria(self, _db):
        import security_het as het
        het.add_alert("WARN", "SQL_SUSPICIOUS", "5.5.5.5", "patron")
        antes = len(het.get_alerts(persisted=True))
        het._threat_alerts.clear()
        despues = len(het.get_alerts(persisted=True))
        assert despues == antes and despues > 0

    def test_add_alert_no_rompe_sin_bd(self):
        import security_het as het
        het.add_alert("WARN", "TEST", "x", "y")
