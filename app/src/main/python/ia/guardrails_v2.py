# -*- coding: utf-8 -*-
"""guardrails_v2.py - Guardrails avanzados para IA TPV Ultra Smart
Extiende guardrails.py con: PII filtering, hallucination detection,
rate limiting, output validation, injection prevention.
"""
import re
import time
import hashlib
from functools import wraps

# ─── PII Patterns ───
PII_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "telefono": re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
    "dni": re.compile(r'\b\d{7,8}[A-Za-z]?\b'),
    "tarjeta": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    "cuenta_bancaria": re.compile(r'\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\d{10}\b'),
}

# ─── SQL Injection Patterns ───
SQL_INJECTION = re.compile(
    r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|UNION)\b.*"
    r"(FROM|INTO|TABLE|DATABASE|WHERE)\b)|"
    r"(--|;|/\*|\*/|xp_|sp_|0x[0-9a-f]{6,})",
)

# ─── XSS Patterns ───
XSS_PATTERN = re.compile(
    r'<script[^>]*>.*?</script>|'
    r'on(error|load|click|mouseover|focus|blur)\s*=|'
    r'javascript\s*:|'
    r'<iframe[^>]*>|'
    r'<object[^>]*>|'
    r'<embed[^>]*>',
    re.IGNORECASE
)

# ─── Hallucination keywords (financial domain) ───
HALLUCINATION_TRIGGERS = [
    "garantizo que", "siempre ganaras", "nunca pierdes",
    "100% seguro", "sin riesgo alguno", "te prometo",
    "datos confidenciales de", "clave secreta es",
]

# ─── Rate Limiter ───
class RateLimiter:
    def __init__(self, max_requests=20, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._history = {}

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        ts = int(now // self.window)
        key = f"{user_id}:{ts}"
        self._history[key] = self._history.get(key, 0) + 1
        count = self._history[key]
        if count > self.max_requests:
            return False
        self._cleanup(now)
        return True

    def _cleanup(self, now):
        cutoff = int(now // self.window) - 2
        for key in list(self._history.keys()):
            user_ts = key.split(":")[-1]
            if int(user_ts) < cutoff:
                del self._history[key]

    def remaining(self, user_id: str) -> int:
        ts = int(time.time() // self.window)
        key = f"{user_id}:{ts}"
        return max(0, self.max_requests - self._history.get(key, 0))

# ─── Singleton rate limiter ───
_ai_limiter = RateLimiter(max_requests=30, window_seconds=60)
_query_limiter = RateLimiter(max_requests=60, window_seconds=60)

# ─── Guardrails V2 ───
class GuardrailsV2:
    @staticmethod
    def mask_pii(text: str) -> str:
        text = PII_PATTERNS["email"].sub("[EMAIL_OCULTO]", text)
        text = PII_PATTERNS["telefono"].sub("[TELEFONO_OCULTO]", text)
        text = PII_PATTERNS["dni"].sub("[DNI_OCULTO]", text)
        text = PII_PATTERNS["tarjeta"].sub("[TARJETA_OCULTA]", text)
        text = PII_PATTERNS["cuenta_bancaria"].sub("[CUENTA_OCULTA]", text)
        return text

    @staticmethod
    def detect_pii(text: str) -> list:
        found = []
        for name, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                found.append(name)
        return found

    @staticmethod
    def check_sql_injection(text: str) -> bool:
        return bool(SQL_INJECTION.search(text))

    @staticmethod
    def check_xss(text: str) -> bool:
        return bool(XSS_PATTERN.search(text))

    @staticmethod
    def check_hallucination(text: str) -> list:
        text_lower = text.lower()
        return [t for t in HALLUCINATION_TRIGGERS if t in text_lower]

    @staticmethod
    def sanitize_output(text: str) -> str:
        if not text:
            return ""
        text = GuardrailsV2.mask_pii(text)
        text = XSS_PATTERN.sub("[CONTENIDO_FILTRADO]", text)
        text = text.replace("<?", "&lt;?")
        text = text.replace("?>", "?&gt;")
        return text.strip()[:2000]

    @staticmethod
    def validate_financial_number(value, min_val=0, max_val=99999999.99):
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def check_ai_rate_limit(user_id: str) -> tuple:
        allowed = _ai_limiter.is_allowed(user_id)
        return allowed, _ai_limiter.remaining(user_id)

    @staticmethod
    def check_query_rate_limit(user_id: str) -> tuple:
        allowed = _query_limiter.is_allowed(user_id)
        return allowed, _query_limiter.remaining(user_id)

    @staticmethod
    def full_check(text: str, role: str = "cliente") -> dict:
        issues = []
        pii = GuardrailsV2.detect_pii(text)
        if pii:
            issues.append(f"PII detectado: {', '.join(pii)}")
        if GuardrailsV2.check_sql_injection(text):
            issues.append("Posible SQL injection detectado")
        if GuardrailsV2.check_xss(text):
            issues.append("Posible XSS detectado")
        hallucinations = GuardrailsV2.check_hallucination(text)
        if hallucinations:
            issues.append(f"Posible alucinacion: {hallucinations[0]}")
        blocked = ["hack", "exploit", "injection", "drop table", "delete from",
                    "shutdown", "reboot", "sudo", "root", "rm -rf", "format c:"]
        for word in blocked:
            if word in text.lower():
                issues.append(f"Palabra bloqueada: {word}")
                break
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "sanitized": GuardrailsV2.sanitize_output(text),
            "pii_found": pii,
        }
