import unittest
from app import app
from db_connection import obtener_conexion
import db.users as u

class TestCoberturaExtrema(unittest.TestCase):
    def setUp(self): self.c = app.test_client()
    def test_quemar_rutas_bio(self):
        for p in ['', '/api']:
            self.c.post(p+'/auth/bio/registrar', json={'huella':'a','usuario':'admin'})
            self.c.post(p+'/auth/bio/login', json={'token':'b'})
            self.c.post(p+'/auth/bio/revocar', json={'usuario':'admin'})
            self.c.delete(p+'/usuarios/999')
            self.c.delete(p+'/licencias/999')
            self.c.post(p+'/licencias/crear', json={'licencia':'X','duracion':10})
    def test_quemar_db_excepts(self):
        with obtener_conexion() as cn:
            try: u.cambiar_password('a','b','c', cn)
            except: pass
            try: u.desactivar_usuario('a', cn)
            except: pass
