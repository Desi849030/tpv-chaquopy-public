"""react_core tests"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))
class T:
    def test_i(self): from ia.react_core import ReactCore; assert ReactCore
    def test_t(self): from ia.react_core import ReactCore; assert ReactCore().think("cafe")
    def test_e(self): from ia.react_core import ReactCore; assert ReactCore().think("")
    def test_a(self): from ia.react_core import ReactCore; assert ReactCore().act("noop",{}) is not None
    def test_o(self): from ia.react_core import ReactCore; assert ReactCore().observe("a",{"s":"ok"}) is not None
