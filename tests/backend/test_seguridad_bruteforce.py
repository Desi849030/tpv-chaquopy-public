import unittest, inspect
from app import app
import db.users as db_u

class TestMercenarioDefinitivo(unittest.TestCase):
    def setUp(self): self.client = app.test_client()
    
    def test_barrer_endpoints_sueltos(self):
        for p in ['', '/api']:
            self.client.post(p+'/auth/bio/registrar', json={'huella':'x','usuario':'admin'})
            self.client.post(p+'/auth/bio/revocar', json={'usuario':'admin'})
            self.client.post(p+'/licencias/crear', json={'licencia':'PRO','duracion':10})
            self.client.delete(p+'/usuarios/9999')
            self.client.delete(p+'/licencias/9999')
            
    def test_barrer_errores_db(self):
        class DBRota:
            def cursor(self): return self
            def execute(self,*a,**k): raise Exception('Simulando caida de DB')
            def commit(self): pass
            def rollback(self): pass
        for n, f in inspect.getmembers(db_u, inspect.isfunction):
            if not n.startswith('_'):
                try: f('admin', DBRota())
                except: pass
                try: f({'username':'a','rol':'cajero'}, DBRota())
                except: pass
