"""test_sqli_deteccion.py — Detección de SQL injection reforzada (#11)."""
import os, sys, pytest

os.environ["TPV_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

ATAQUES = [
    "' OR '1'='1", "1 OR 1=1", "admin'--", "'; DROP TABLE usuarios;--",
    "UNION SELECT password FROM usuarios", "1; DELETE FROM ventas",
    "' OR 'a'='a", "1 UNION SELECT * FROM clientes",
]
LEGITIMOS = [
    "Coca-Cola 2L", "Mesa de selección de madera", "Camiseta talla M",
    "Producto and oferta especial", "Update de precios enero",
    "Café molido premium", "juan@correo.com", "Combo 2x1",
]


class TestDeteccionSQLi:
    @pytest.mark.parametrize("ataque", ATAQUES)
    def test_ataques_bloqueados(self, ataque):
        from security_het import detect_sql_injection
        safe, _ = detect_sql_injection(ataque)
        assert safe is False, f"NO detectó ataque: {ataque!r}"

    @pytest.mark.parametrize("texto", LEGITIMOS)
    def test_legitimos_pasan(self, texto):
        from security_het import detect_sql_injection
        safe, _ = detect_sql_injection(texto)
        assert safe is True, f"Falso positivo en: {texto!r}"


class TestSanitizeInput:
    def test_escapa_html(self):
        from security_het import sanitize_input
        out = sanitize_input("<script>alert(1)</script>")
        assert "<script>" not in out
        assert "&lt;" in out

    def test_elimina_null_bytes(self):
        from security_het import sanitize_input
        assert "\x00" not in sanitize_input("abc\x00def")

    def test_no_corrompe_texto_normal(self):
        from security_het import sanitize_input
        out = sanitize_input("Mesa de selección")
        assert "selección" in out
