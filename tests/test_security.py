"""Tests de seguridad."""
import pytest

class TestPassword:
    def test_hash_tuple(self):
        from database import _hash_password
        h, s = _hash_password("test")
        assert isinstance(h, str) and len(h) == 64
    def test_verify_ok(self):
        from database import _hash_password, verificar_password
        h, s = _hash_password("pass")
        assert verificar_password("pass", h, s) is True
    def test_verify_fail(self):
        from database import _hash_password, verificar_password
        h, s = _hash_password("pass")
        assert verificar_password("wrong", h, s) is False

class TestSQLi:
    def test_clean(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection("texto normal") is False
    def test_union(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection("UNION SELECT") is True
    def test_dict(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection({"q": "DROP TABLE"}) is True

class TestTokenizer:
    def test_tokenize(self):
        from payment_tokenizer import tokenize
        r = tokenize("1234")
        assert isinstance(r, dict)
        assert "token" in r
        assert "signature" in r
    def test_verify(self):
        from payment_tokenizer import tokenize, verify_token
        r = tokenize("9999")
        assert verify_token(r["token"], r["signature"]) is True
    def test_verify_wrong_sig(self):
        from payment_tokenizer import tokenize, verify_token
        r = tokenize("9999")
        assert verify_token(r["token"], "wrong") is False
    def test_verify_wrong_token(self):
        from payment_tokenizer import tokenize, verify_token
        r = tokenize("9999")
        assert verify_token("falsotoken", r["signature"]) is False
    def test_mask(self):
        from payment_tokenizer import mask_card
        assert mask_card("4242424242424242") == "****-****-****-4242"
        assert mask_card(None) == "****"
