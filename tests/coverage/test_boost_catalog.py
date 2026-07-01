"""Ejecuta catalog real."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_catalog_all(self):
        from ia.catalog import ProductCatalog, catalog_cache
        assert ProductCatalog
        for q in ["cafe","arroz","leche","pan","aceite","azucar","huevos",""]:
            r = catalog_cache.search(q)
            if r is not None: assert isinstance(r, list)
        r = catalog_cache.get_categories()
        if r is not None: assert isinstance(r, list)
