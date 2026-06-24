"""Fixture global - backup/restore de BD + PYTHONPATH."""
import pytest, os, sys, shutil
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
PY=os.path.join(ROOT,"app","src","main","python")
sys.path.insert(0,PY)
os.environ["TPV_TESTING"]="1"
os.environ.setdefault("TPV_SECRET_KEY","test")
os.environ.setdefault("TPV_DEMO_PASSWORD","test")
DB=os.path.join(PY,"tpv_datos.db")
BK=DB+".clean"
def pytest_sessionstart(session):
    if not os.path.exists(BK) and os.path.exists(DB): shutil.copy2(DB,BK)
def pytest_sessionfinish(session, exitstatus):
    if os.path.exists(BK): shutil.copy2(BK,DB)
