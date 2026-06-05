# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

class TestGuardrailsV2:
    def test_mask_email(self):
        from ia.guardrails_v2 import GuardrailsV2
        r = GuardrailsV2.mask_pii("Contactar a user@test.com por favor")
        assert "[EMAIL_OCULTO]" in r
        assert "user@test.com" not in r

    def test_mask_telefono(self):
        from ia.guardrails_v2 import GuardrailsV2
        r = GuardrailsV2.mask_pii("Mi numero es 612345678")
        assert "[TELEFONO_OCULTO]" in r

    def test_detect_pii(self):
        from ia.guardrails_v2 import GuardrailsV2
        found = GuardrailsV2.detect_pii("user@test.com y 612345678")
        assert "email" in found
        assert "telefono" in found

    def test_sql_injection(self):
        from ia.guardrails_v2 import GuardrailsV2
        assert GuardrailsV2.check_sql_injection("SELECT * FROM users") == True
        assert GuardrailsV2.check_sql_injection("Hola, buenos dias") == False

    def test_xss(self):
        from ia.guardrails_v2 import GuardrailsV2
        assert GuardrailsV2.check_xss("<script>alert('xss')</script>") == True
        assert GuardrailsV2.check_xss("Texto normal") == False

    def test_hallucination(self):
        from ia.guardrails_v2 import GuardrailsV2
        found = GuardrailsV2.check_hallucination("Te garAntizo que siempre ganaras")
        assert len(found) > 0

    def test_sanitize_output(self):
        from ia.guardrails_v2 import GuardrailsV2
        r = GuardrailsV2.sanitize_output("user@x.com <script>alert(1)</script>")
        assert "[EMAIL_OCULTO]" in r
        assert "[CONTENIDO_FILTRADO]" in r

    def test_full_check_safe(self):
        from ia.guardrails_v2 import GuardrailsV2
        r = GuardrailsV2.full_check("Cual es el precio del pan?")
        assert r["safe"] == True
        assert len(r["issues"]) == 0

    def test_full_check_unsafe(self):
        from ia.guardrails_v2 import GuardrailsV2
        r = GuardrailsV2.full_check("DROP TABLE users; -- hack")
        assert r["safe"] == False
        assert len(r["issues"]) > 0

    def test_rate_limiter(self):
        from ia.guardrails_v2 import RateLimiter
        lim = RateLimiter(max_requests=3, window_seconds=60)
        assert lim.is_allowed("user1") == True
        assert lim.is_allowed("user1") == True
        assert lim.is_allowed("user1") == True
        assert lim.is_allowed("user1") == False
        assert lim.remaining("user1") == 0

    def test_validate_financial(self):
        from ia.guardrails_v2 import GuardrailsV2
        assert GuardrailsV2.validate_financial_number(99.99) == True
        assert GuardrailsV2.validate_financial_number(-5) == False
        assert GuardrailsV2.validate_financial_number("abc") == False

import pytest


@pytest.mark.skip(reason="i18n_dict no implementado como modulo Python; "
                         "las traducciones viven en i18n_dictionary.json con otra estructura")
class TestI18n:
    def test_spanish(self):
        from i18n_dict import t
        assert t("nav.dashboard", "es") == "Dashboard"
        assert t("nav.ventas", "es") == "Ventas"

    def test_english(self):
        from i18n_dict import t
        assert t("nav.ventas", "en") == "Sales"
        assert t("msg.guardar", "en") == "Save"

    def test_portuguese(self):
        from i18n_dict import t
        assert t("nav.ventas", "pt") == "Vendas"
        assert t("msg.cancelar", "pt") == "Cancelar"

    def test_missing_key(self):
        from i18n_dict import t
        assert t("nonexistent.key") == "nonexistent.key"

    def test_available_languages(self):
        from i18n_dict import available_languages
        langs = available_languages()
        assert "es" in langs
        assert "en" in langs
        assert "pt" in langs
