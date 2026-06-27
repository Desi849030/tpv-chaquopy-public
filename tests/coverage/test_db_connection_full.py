"""Cobertura completa de db_connection.py"""
import pytest, sys, os, sqlite3, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class TestDbConnectionFull:
    def test_get_connection(self):
        from db_connection import get_connection
        c = get_connection()
        assert c is not None
        c.execute("SELECT 1")
        c.close()

    def test_wal_mode(self):
        from db_connection import get_connection
        c = get_connection()
        r = c.execute("PRAGMA journal_mode").fetchone()
        c.close()
        assert r[0] == "wal"

    def test_foreign_keys(self):
        from db_connection import get_connection
        c = get_connection()
        r = c.execute("PRAGMA foreign_keys").fetchone()
        c.close()
        assert r[0] == 1

    def test_hash_password(self):
        from db_connection import _hash_password, verify_password
        h, s = _hash_password("test_password_123")
        assert verify_password("test_password_123", h, s)
        assert not verify_password("wrong", h, s)

    def test_hash_different_salts(self):
        from db_connection import _hash_password
        h1, s1 = _hash_password("same")
        h2, s2 = _hash_password("same")
        assert h1 != h2
        assert s1 != s2

    def test_create_audit_table(self):
        from db_connection import create_audit_table
        create_audit_table()
        assert True

    def test_audit_log(self):
        from db_connection import create_audit_table, log_event, get_connection
        create_audit_table()
        log_event("test_user", "test_action", "productos", "p1", "{'precio':10}", "{'precio':15}")
        c = get_connection()
        r = c.execute("SELECT * FROM audit_logs WHERE usuario='test_user'").fetchone()
        c.close()
        assert r is not None
        assert r["accion"] == "test_action"
        assert r["tabla"] == "productos"

    def test_audit_log_edge_cases(self):
        from db_connection import create_audit_table, log_event
        create_audit_table()
        log_event(None, None, None)
        log_event("", "", "")
        log_event("a"*100, "b"*100, "c"*100, "d"*100, "e"*1000, "f"*1000)
        assert True

    def test_get_db_info(self):
        from db_connection import get_db_info, TABLAS_PERMITIDAS
        info = get_db_info()
        assert isinstance(info, dict)
        assert "archivo" in info
        assert "tablas" in info
        for t in info["tablas"]:
            assert t in TABLAS_PERMITIDAS

    def test_tablas_permitidas(self):
        from db_connection import TABLAS_PERMITIDAS
        assert len(TABLAS_PERMITIDAS) > 5
        assert "usuarios" in TABLAS_PERMITIDAS
        assert "productos" in TABLAS_PERMITIDAS
        assert "historial_ventas" in TABLAS_PERMITIDAS
        assert isinstance(TABLAS_PERMITIDAS, frozenset)
