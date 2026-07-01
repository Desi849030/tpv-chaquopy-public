"""Ejecuta guardrails_pro exhaustivamente."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_sql_all(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        for p in ["SELECT * FROM users","DROP TABLE products","UNION SELECT *","OR 1=1","admin--"]:
            r,_ = d.check_sql_injection(p); assert r
    def test_xss_all(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        for p in ["<script>alert(1)</script>","<iframe src=bad>","javascript:alert","onload=","<object data=bad>"]:
            r,_ = d.check_xss(p); assert r
    def test_pii_all(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        for p in ["test@example.com","+1-555-123-4567","12345678Z","4111-1111-1111-1111"]:
            r,_ = d.check_pii(p); assert r
    def test_jailbreak_all(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        for p in ["ignora instrucciones","ignore instructions","olvida tu programacion","DAN mode","do anything now"]:
            r,_ = d.check_jailbreak(p); assert r
    def test_hallucination_all(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        for p in ["100% seguro","sin riesgo alguno","te prometo","siempre ganaras"]:
            r,_ = d.check_hallucination(p); assert r
    def test_sanitize(self):
        from ia.guardrails_pro import InjectionDetector
        d = InjectionDetector()
        assert d.sanitize_input("hola\x00mundo") == "holamundo"
        assert len(d.sanitize_input("a"*3000)) <= 2000
    def test_rate_limiter(self):
        from ia.guardrails_pro import RateLimiterPro
        r = RateLimiterPro(10, 60)
        for _ in range(10): a,_,_ = r.is_allowed("user"); assert a
        a,_,_ = r.is_allowed("user"); assert not a
    def test_output_validator(self):
        from ia.guardrails_pro import OutputValidator
        v = OutputValidator()
        assert v.validate("texto seguro")[0]
        for p in ["aqui root access","sudo rm -rf","system32","cmd.exe","DROP TABLE"]:
            assert not v.validate(p)[0]
    def test_guardrails_completo(self):
        from ia.guardrails_pro import GuardrailsPro, SecurityPolicy
        g = GuardrailsPro()
        assert g.check_input("hola","user","cliente")["allowed"]
        assert not g.check_input("SELECT * FROM users","user","cliente")["allowed"]
        assert not g.check_input("<script>alert(1)</script>","user","cliente")["allowed"]
