"""Tests: identidad persistente para cliente anónimo."""
import os
import sys

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestAnonimoPersistente:
    def test_agent_identity_persiste_en_mismo_cliente_anon(self, client_anon):
        r1 = client_anon.get('/api/agent/identity')
        assert r1.status_code == 200
        d1 = r1.get_json()
        assert d1['ok'] is True
        assert d1['autenticado'] is False
        assert d1['cliente_tipo'] == 'anonimo'
        assert d1['anon_client_id'].startswith('anon-')
        assert d1['usuario_id'] == d1['anon_client_id']
        assert d1['request_id'].startswith('req-')

        r2 = client_anon.get('/api/agent/identity')
        assert r2.status_code == 200
        d2 = r2.get_json()
        assert d2['anon_client_id'] == d1['anon_client_id']
        assert d2['usuario_id'] == d1['usuario_id']
        assert d2['request_id'] != d1['request_id']

    def test_publico_identity_reutiliza_mismo_anon_id(self, client_anon):
        r1 = client_anon.get('/api/agent/identity')
        anon_id = r1.get_json()['anon_client_id']

        r2 = client_anon.get('/api/publico/identity')
        assert r2.status_code == 200
        d2 = r2.get_json()
        assert d2['ok'] is True
        assert d2['anon_client_id'] == anon_id
        assert d2['cliente_tipo'] == 'anonimo'

    def test_chat_anonimo_acepta_id_y_request_id(self, client_anon):
        payload = {
            'mensaje': 'hola',
            'nombre': 'Visitante',
            'anon_client_id': 'anon-front-001xyz',
            'request_id': 'req-front-001xyz',
        }
        r = client_anon.post('/api/agent/chat', json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d['ok'] is True
        assert d['anon_client_id'] == 'anon-front-001xyz'
        assert d['request_id'] == 'req-front-001xyz'
        assert d['autenticado'] is False

    def test_publico_catalogo_incluye_meta_anonima(self, client_anon):
        r = client_anon.get('/api/publico/catalogo')
        assert r.status_code == 200
        d = r.get_json()
        assert d['ok'] is True
        assert 'meta' in d
        assert d['meta']['anon_client_id'].startswith('anon-')
        assert d['meta']['request_id'].startswith('req-')
