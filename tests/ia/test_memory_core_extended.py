"""memory_core tests"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))
class T:
    def test_sr(self): from ia.memory_core import MemoryCore; m=MemoryCore(); m.save("u",{"r":"t"}); assert m.recall("u")
    def test_s(self): from ia.memory_core import MemoryCore; assert isinstance(MemoryCore().search("cafe",5),list)
    def test_c(self): from ia.memory_core import MemoryCore; m=MemoryCore(); m.save("x",{"t":1}); assert m.clear("x") is not None
    def test_eu(self): from ia.memory_core import MemoryCore; r=MemoryCore().recall("no"); assert r is None or isinstance(r,dict)
