"""test_sync_seguridad.py — La sincronización NUNCA envía credenciales a Supabase (#14)."""
import os, sys, pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestSyncBlocklist:
    def test_sin_secretos_elimina_credenciales(self):
        from sync.supabase_sync import _sin_secretos
        entrada = {"usuario_id": "u1", "username": "admin",
                   "password_hash": "AAA", "password_salt": "BBB", "activo": 1}
        salida = _sin_secretos(entrada)
        assert "password_hash" not in salida
        assert "password_salt" not in salida
        assert salida["usuario_id"] == "u1"
        assert salida["username"] == "admin"
        assert salida["activo"] == 1

    def test_blocklist_cubre_campos_sensibles(self):
        from sync.supabase_sync import SYNC_BLOCKLIST
        for campo in ("password_hash", "password_salt", "totp_secret", "pin_hash"):
            assert campo in SYNC_BLOCKLIST

    def test_sin_secretos_dict_vacio(self):
        from sync.supabase_sync import _sin_secretos
        assert _sin_secretos({}) == {}

    def test_sin_secretos_solo_datos_limpios(self):
        from sync.supabase_sync import _sin_secretos
        d = {"nombre": "Cliente", "email": "a@b.com", "telefono": "555"}
        assert _sin_secretos(d) == d
