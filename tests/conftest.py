"""Fixture global — backup/restore automático de BD en tests E2E"""
import pytest
import os, sys, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

DB_FILE = os.path.join(PY_PATH, "tpv_datos.db")
BACKUP = DB_FILE + ".clean_backup"

def pytest_sessionstart(session):
    """Crear backup limpio al iniciar los tests"""
    if not os.path.exists(BACKUP):
        shutil.copy2(DB_FILE, BACKUP)
        print("\n📦 Backup limpio creado")

def pytest_sessionfinish(session, exitstatus):
    """Restaurar BD al finalizar TODOS los tests"""
    if os.path.exists(BACKUP):
        shutil.copy2(BACKUP, DB_FILE)
        print("\n🧹 BD restaurada a estado limpio")
