"""Resetear BD a estado limpio para tests"""
import os, sys, shutil

# Buscar DB_FILE sin importar
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
sys.path.insert(0, PY_PATH)
os.environ["TPV_TESTING"] = "1"

DB_FILE = os.path.join(PY_PATH, "tpv_datos.db")
BACKUP = DB_FILE + ".clean_backup"

def backup_clean():
    if not os.path.exists(BACKUP):
        shutil.copy2(DB_FILE, BACKUP)
        print(f"✅ Backup limpio creado: {BACKUP}")
    else:
        print(f"ℹ️ Backup ya existe: {BACKUP}")

def restore_clean():
    if os.path.exists(BACKUP):
        shutil.copy2(BACKUP, DB_FILE)
        print(f"✅ BD restaurada de: {BACKUP}")
    else:
        print("❌ No hay backup limpio")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "backup":
        backup_clean()
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_clean()
    else:
        print("Uso: python reset_bd.py [backup|restore]")
