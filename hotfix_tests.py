#!/usr/bin/env python3
"""Hotfix: tpv_validate_db usa sqlite3 directamente en vez de get_connection"""
import os

app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app/src/main/python/app.py")
with open(app_path, 'r') as f:
    content = f.read()

old = """def tpv_validate_db():
    \"\"\"Verificar que la BD existe y tiene datos al arrancar.\"\"\"
    from database import DB_FILE, get_connection
    import os
    if not os.path.exists(DB_FILE):
        print("[v24] ADVERTENCIA: BD no encontrada en", DB_FILE)
        return False
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        conn.close()
        print(f"[v24] BD OK: {count} productos encontrados")
        return count > 0
    except Exception as e:
        print(f"[v24] ERROR BD: {e}")
        return False"""

new = """def tpv_validate_db():
    \"\"\"Verificar que la BD existe y tiene datos al arrancar.\"\"\"
    import sqlite3, os
    from database import DB_FILE
    if not os.path.exists(DB_FILE):
        print("[v24] ADVERTENCIA: BD no encontrada en", DB_FILE)
        return False
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        conn.close()
        print(f"[v24] BD OK: {count} productos encontrados")
        return count > 0
    except Exception as e:
        print(f"[v24] ERROR BD: {e}")
        return False"""

if old in content:
    content = content.replace(old, new)
    with open(app_path, 'w') as f:
        f.write(content)
    print("[OK] tpv_validate_db corregido: sqlite3 directo (sin get_connection)")
else:
    print("[SKIP] Bloque no encontrado, buscando alternativa...")
    # Alternativa: hacer la funcion tolerante a errores
    alt_old = "tpv_validate_db()\n"
    alt_new = "try:\n    tpv_validate_db()\nexcept Exception as e:\n    print(f'[v24] Validacion BD omitida: {e}')\n"
    if alt_old in content:
        content = content.replace(alt_old, alt_new)
        with open(app_path, 'w') as f:
            f.write(content)
        print("[OK] tpv_validate_db() envuelto en try/except")
    else:
        print("[WARN] No se pudo parchear automaticamente")
