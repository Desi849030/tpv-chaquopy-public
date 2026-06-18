import os
import sys
import uuid
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)

os.environ["TPV_TESTING"] = "1"

from db.users import (
    login_usuario,
    crear_usuario,
    cambiar_password,
    resetear_password,
    listar_usuarios,
    desactivar_usuario,
)


class TestDbUsersDirect(unittest.TestCase):

    def test_login_usuario_ok(self):
        r = login_usuario("desarrollador", "123456")
        self.assertTrue(r)
        self.assertEqual(r["rol"], "desarrollador")

    def test_login_usuario_fail(self):
        r = login_usuario("desarrollador", "incorrecta")
        self.assertIsNone(r)

    def test_crear_usuario_ok(self):
        username = f"dao_{uuid.uuid4().hex[:8]}"
        r = crear_usuario(
            {
                "username": username,
                "password": "123456",
                "nombre": "DAO User",
                "rol": "vendedor",
            },
            creado_por_rol="desarrollador",
            creado_por_id="dev-001",
        )
        self.assertTrue(r["ok"])

    def test_crear_usuario_duplicate(self):
        username = f"dupdao_{uuid.uuid4().hex[:8]}"
        r1 = crear_usuario(
            {
                "username": username,
                "password": "123456",
                "nombre": "Dup DAO",
                "rol": "vendedor",
            },
            creado_por_rol="desarrollador",
            creado_por_id="dev-001",
        )
        self.assertTrue(r1["ok"])

        r2 = crear_usuario(
            {
                "username": username,
                "password": "123456",
                "nombre": "Dup DAO 2",
                "rol": "vendedor",
            },
            creado_por_rol="desarrollador",
            creado_por_id="dev-001",
        )
        self.assertFalse(r2["ok"])

    def test_crear_usuario_invalid_role(self):
        username = f"badrole_{uuid.uuid4().hex[:8]}"
        r = crear_usuario(
            {
                "username": username,
                "password": "123456",
                "nombre": "Bad Role",
                "rol": "desarrollador",
            },
            creado_por_rol="administrador",
            creado_por_id="usr-001",
        )
        self.assertFalse(r["ok"])

    def test_crear_usuario_missing_fields(self):
        r = crear_usuario(
            {
                "username": "",
                "password": "",
                "nombre": "",
                "rol": "vendedor",
            },
            creado_por_rol="desarrollador",
            creado_por_id="dev-001",
        )
        self.assertFalse(r["ok"])

    def test_listar_usuarios_dev(self):
        rows = listar_usuarios("desarrollador", "dev-001")
        self.assertTrue(isinstance(rows, list))

    def test_listar_usuarios_admin(self):
        rows = listar_usuarios("administrador", "usr-001")
        self.assertTrue(isinstance(rows, list))

    def test_reset_password_no_permission(self):
        r = resetear_password("usr-001", "123456", "usr-003")
        self.assertFalse(r["ok"])

    def test_reset_password_admin_ok(self):
        r = resetear_password("usr-003", "123456", "usr-001")
        self.assertTrue(isinstance(r, dict))

    def test_cambiar_password_wrong_current(self):
        r = cambiar_password("dev-001", "incorrecta", "654321")
        self.assertFalse(r["ok"])

    def test_desactivar_usuario(self):
        username = f"del_{uuid.uuid4().hex[:8]}"
        created = crear_usuario(
            {
                "username": username,
                "password": "123456",
                "nombre": "Delete Me",
                "rol": "vendedor",
            },
            creado_por_rol="desarrollador",
            creado_por_id="dev-001",
        )
        self.assertTrue(created["ok"])
        uid = created["usuario_id"]

        r = desactivar_usuario(uid, "dev-001")
        self.assertTrue(r["ok"])

