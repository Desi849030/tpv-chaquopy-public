"""test_import_excel.py — Tests para importacion inteligente Excel"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))


class TestDBProductosImport:
    """Tests de funciones de importacion en db_products."""

    def test_sincronizar_productos_vacia(self):
        """Sincronizar lista vacia retorna dict con ok."""
        from db_products import sincronizar_productos_catalogo
        r = sincronizar_productos_catalogo([], 'system')
        assert r is not None
        assert isinstance(r, dict)
        assert 'ok' in r

    def test_obtener_productos_catalogo(self):
        """Obtener productos del catalogo retorna lista."""
        from db_products import obtener_productos_catalogo
        prods = obtener_productos_catalogo()
        assert prods is not None
        assert isinstance(prods, list)


class TestToolRegistryImport:
    """Tests del registry de herramientas para el agente IA."""

    def test_reconstruir_productos_herramienta(self):
        from tool_registry import get_tool
        t = get_tool('reconstruir_productos')
        assert t is not None
        assert t.route == '/api/reconstruir-desde-productos'
        assert t.method == 'POST'

    def test_importar_catalogo_herramienta(self):
        from tool_registry import get_tool
        t = get_tool('importar_catalogo_inventario')
        assert t is not None
        assert t.route == '/api/inventario/importar-catalogo'

    def test_obtener_productos_herramienta(self):
        from tool_registry import get_tool
        t = get_tool('obtener_productos_catalogo')
        assert t is not None
        assert t.route == '/api/productos'
        assert t.method == 'GET'

    def test_categoria_importacion(self):
        from tool_registry import get_tools_by_category
        tools = get_tools_by_category('importacion')
        assert len(tools) >= 3
        names = [t.name for t in tools]
        assert 'reconstruir_productos' in names
        assert 'importar_catalogo_inventario' in names
        assert 'obtener_productos_catalogo' in names

    def test_busqueda_importar(self):
        from tool_registry import search_tools
        results = search_tools('importar')
        assert len(results) >= 2

    def test_busqueda_importacion(self):
        from tool_registry import search_tools
        results = search_tools('importacion')
        assert len(results) >= 3

    def test_busqueda_catalogo(self):
        from tool_registry import search_tools
        results = search_tools('catalogo')
        assert len(results) >= 2


class TestAPIRoutesPublicas:
    """Tests de endpoints publicos (sin auth)."""

    def test_api_productos_retorna_dict(self):
        """GET /api/productos retorna dict con productos y total."""
        from app import app
        with app.test_client() as c:
            r = c.get('/api/productos')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'productos' in data
            assert 'total' in data
            assert isinstance(data['productos'], list)

    def test_api_health(self):
        """GET /api/health retorna 200."""
        from app import app
        with app.test_client() as c:
            r = c.get('/api/health')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None

    def test_catalog_stats_importacion(self):
        """El catalogo incluye la categoria importacion."""
        from tool_registry import get_catalog_stats
        stats = get_catalog_stats()
        assert 'importacion' in stats['categories']
        assert stats['categories']['importacion'] >= 3
