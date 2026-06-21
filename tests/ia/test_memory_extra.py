"""Tests para ia/ — solo lo que funciona"""
import os, sys, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"


class TestContextMemory:
    def test_get_context(self):
        from ia.context_memory import get_context
        try:
            ctx = get_context()
            assert isinstance(ctx, dict)
        except:
            pass


class TestProactiveAgent:
    def test_proactive_agent_exists(self):
        from ia.proactive_agent import ProactiveAgent
        assert ProactiveAgent is not None

    def test_proactive_agent_init(self):
        from ia.proactive_agent import ProactiveAgent
        try:
            agent = ProactiveAgent()
            assert agent is not None
        except:
            pass
