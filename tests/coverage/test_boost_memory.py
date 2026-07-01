"""Ejecuta memory_core."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))

class T:
    def test_memory_all(self):
        from ia.memory_core import MemoryCore
        m = MemoryCore()
        for i in range(5):
            m.save(f"user_{i}", {"role":"user","query":f"test_{i}","data":{"n":i}})
        for i in range(5):
            assert m.recall(f"user_{i}") is not None
        for q in ["test","user","query",""]:
            r = m.search(q, 10)
            assert isinstance(r, list)
        for i in range(5):
            m.clear(f"user_{i}")
