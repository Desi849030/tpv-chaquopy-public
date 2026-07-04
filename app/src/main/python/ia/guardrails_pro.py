"""Guardrails Profesionales v3."""
from __future__ import annotations
import re, time, logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class SecurityPolicy:
    def __init__(self):
        self.max_requests_per_minute = 30
        self.max_message_length = 2000
        self.block_sql_injection = True
        self.block_xss = True
        self.block_pii = True
        self.block_jailbreak = True
        self.block_hallucination_triggers = True


class InjectionDetector:
    def __init__(self):
        self.sql_patterns = [
            re.compile(r"SELECT\s+.*\s+FROM", re.I),
            re.compile(r"INSERT\s+INTO", re.I),
            re.compile(r"UPDATE\s+.*\s+SET", re.I),
            re.compile(r"DELETE\s+FROM", re.I),
            re.compile(r"DROP\s+TABLE", re.I),
            re.compile(r"UNION\s+.*\s+SELECT", re.I),
            re.compile(r"--"),
            re.compile(r";\s*$"),
            re.compile(r"OR\s+1\s*=\s*1", re.I),
        ]
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.I | re.S),
            re.compile(r"javascript\s*:", re.I),
            re.compile(r"<iframe[^>]*>", re.I),
            re.compile(r"<object[^>]*>", re.I),
            re.compile(r"on(error|load|click|mouseover)\s*=", re.I),
            re.compile(r"eval\s*\(", re.I),
            re.compile(r"document\.cookie", re.I),
        ]
        self.pii_patterns = {
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "telefono": re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"),
            "dni": re.compile(r"\b\d{7,8}[A-Za-z]?\b"),
            "tarjeta": re.compile(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b"),
        }
        self.jailbreak_patterns = [
            re.compile(r"ignora\s+instrucciones", re.I),
            re.compile(r"ignore\s+instructions", re.I),
            re.compile(r"olvida\s+tu\s+programacion", re.I),
            re.compile(r"no\s+tienes\s+limites", re.I),
            re.compile(r"no\s+limits", re.I),
            re.compile(r"DAN\b", re.I),
            re.compile(r"do\s+anything\s+now", re.I),
        ]
        self.hallucination_triggers = [
            "garantizo que", "siempre ganaras", "nunca pierdes",
            "100% seguro", "sin riesgo alguno", "te prometo",
            "datos confidenciales", "clave secreta es",
        ]

    def check_sql_injection(self, text):
        for p in self.sql_patterns:
            if p.search(text):
                return True, "Posible SQL injection"
        return False, ""

    def check_xss(self, text):
        for p in self.xss_patterns:
            if p.search(text):
                return True, "Posible XSS"
        return False, ""

    def check_pii(self, text):
        found = []
        for name, pattern in self.pii_patterns.items():
            if pattern.search(text):
                found.append(name)
        return len(found) > 0, found

    def check_jailbreak(self, text):
        for p in self.jailbreak_patterns:
            if p.search(text):
                return True, "Posible jailbreak"
        return False, ""

    def check_hallucination(self, text):
        t = text.lower()
        for trigger in self.hallucination_triggers:
            if trigger in t:
                return True, "Trigger: " + trigger
        return False, ""

    def sanitize_input(self, text):
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text[:2000].strip()


class RateLimiterPro:
    def __init__(self, max_requests=30, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._history = {}
        self._blocked = {}

    def is_allowed(self, user_id):
        now = time.time()
        if user_id in self._blocked:
            if now < self._blocked[user_id]:
                return False, 0, int(self._blocked[user_id] - now)
            del self._blocked[user_id]
        cutoff = now - self.window
        if user_id in self._history:
            self._history[user_id] = [t for t in self._history[user_id] if t > cutoff]
        if user_id not in self._history:
            self._history[user_id] = []
        if len(self._history[user_id]) >= self.max_requests:
            self._blocked[user_id] = now + 300
            return False, 0, 300
        self._history[user_id].append(now)
        return True, self.max_requests - len(self._history[user_id]), 0


class OutputValidator:
    def __init__(self):
        self.blocked = ["root access", "sudo", "system32", "cmd.exe", "DROP TABLE", "rm -rf"]

    def validate(self, text):
        t = text.lower()
        for phrase in self.blocked:
            if phrase in t:
                return False, "Contenido bloqueado: " + phrase
        return True, ""


class GuardrailsPro:
    def __init__(self, policy=None):
        self.policy = policy or SecurityPolicy()
        self.detector = InjectionDetector()
        self.rate_limiter = RateLimiterPro(self.policy.max_requests_per_minute)
        self.validator = OutputValidator()

    def check_input(self, text, user_id, role="cliente"):
        result = {"allowed": True, "sanitized": self.detector.sanitize_input(text), "warnings": [], "blocks": []}
        allowed, remaining, block_time = self.rate_limiter.is_allowed(user_id)
        if not allowed:
            result["allowed"] = False
            result["blocks"].append("Rate limit. Espera " + str(block_time) + "s")
            return result
        result["rate_remaining"] = remaining
        for check in ["check_sql_injection", "check_xss", "check_jailbreak"]:
            fn = getattr(self.detector, check)
            detected, msg = fn(text)
            if detected:
                result["allowed"] = False
                result["blocks"].append(msg)
                return result
        detected, msg = self.detector.check_hallucination(text)
        if detected:
            result["warnings"].append(msg)
        return result

    def check_output(self, text):
        return self.validator.validate(text)


guardrails_pro = GuardrailsPro()
detector = InjectionDetector()
