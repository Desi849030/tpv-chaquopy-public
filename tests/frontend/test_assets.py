"""assets tests"""
import os, json
F=os.path.join(os.path.dirname(__file__),"..","..","app","src","main","assets","frontend")
S=os.path.join(F,"static")
def test_idx(): p=os.path.join(F,"templates","index.html"); assert os.path.exists(p) and os.path.getsize(p)>1000
def test_sw(): assert os.path.exists(os.path.join(S,"service-worker.js"))
def test_css(): d=os.path.join(S,"css"); assert len([f for f in os.listdir(d) if f.endswith(".css")])>=1
