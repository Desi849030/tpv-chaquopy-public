#!/usr/bin/env python3
"""SIMULACION COMPLETA TPV APK — Todos los roles y flujos"""
import os, sys, json, tempfile, shutil

BASE = "app/src/main/python"
APP_DIR = os.path.abspath(BASE)
sys.path.insert(0, APP_DIR)
os.environ["TPV_TESTING"] = "1"
os.environ["TPV_FRONTEND_DIR"] = os.path.join(APP_DIR, "..", "assets", "frontend")

tmpd = tempfile.mkdtemp(prefix="tpv_sim_")
os.environ["TPV_FILES_DIR"] = tmpd

for f in [".tpv_secret", ".tpv_hmac_secret"]:
    p = os.path.join(BASE, f)
    if os.path.exists(p): os.remove(p)

print("Inicializando BD...")
from database import crear_tablas, obtener_conexion
crear_tablas()

# Insertar usuarios de prueba en la BD
conn = obtener_conexion()
for uid, uname, rol in [
    ("dev-001","dev","desarrollador"),
    ("admin-001","admin","administrador"),
    ("vend-001","vendedor1","vendedor"),
    ("sup-001","supervisor1","supervisor"),
]:
    conn.execute(
        "INSERT OR IGNORE INTO usuarios(usuario_id,username,nombre,rol,password_hash,password_salt,activo) VALUES(?,?,?,?,?,?,1)",
        (uid, uname, f"Test {rol}", rol, "hash_test", "salt_test")
    )
conn.commit()
conn.close()
print("Usuarios de prueba insertados")

print("Importando app...")
from app import app as _app
_app.config["TESTING"] = True
_app.config["DEBUG"] = False

P = F = 0
ERRORES = []

def ok(label, cond, extra=""):
    global P, F
    if cond:
        P += 1; print(f"  OK   {label}")
    else:
        F += 1; msg = f"{label} -- {extra}"; print(f"  FAIL {msg}")
        ERRORES.append(msg)
    return cond

def login_as(client, user_id, username, rol, nombre="Test"):
    with client.session_transaction() as sess:
        sess["usuario"] = {"usuario_id": user_id, "username": username, "rol": rol, "nombre": nombre}
        sess.permanent = True

def post(client, path, data=None):
    r = client.post(path, json=data)
    try: j = r.get_json()
    except: j = {}
    return r, j

def get(client, path):
    r = client.get(path)
    try: j = r.get_json()
    except: j = {}
    return r, j

def run_role_tests(role_name, uid, uname, rol, can_admin=False, can_dev=False):
    global P, F
    c = _app.test_client()
    login_as(c, uid, uname, rol)
    S = "\n" + "="*60
    tag = f"[{role_name}]"

    print(f"\n{S}\n{tag} 1. SESION Y AUTH")
    r, j = get(c, "/api/auth/me")
    ok(f"{tag} /auth/me", r.status_code==200 and j.get("autenticado"), f"{r.status_code}")
    r, j = get(c, "/api/status")
    ok(f"{tag} /status", r.status_code==200, f"{r.status_code}")
    r, j = get(c, "/api/health/full")
    ok(f"{tag} /health/full", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 2. INVENTARIO Y CATALOGO")
    r, j = get(c, "/api/catalogo")
    ok(f"{tag} /catalogo", r.status_code==200, f"{r.status_code}")
    if can_admin or can_dev:
        r, j = get(c, "/api/inventario/general")
        ok(f"{tag} /inv/general", r.status_code==200, f"{r.status_code}")
    else:
        r, j = get(c, "/api/inventario/general")
        ok(f"{tag} /inv/general denegado", r.status_code==403, f"got {r.status_code}")

    print(f"\n{S}\n{tag} 3. CREAR PRODUCTO (solo admin/dev)")
    if can_admin or can_dev:
        r, j = post(c, "/api/inventario/entrada", {
            "producto_id":"SIM01","nombre":"Producto Sim","precio_compra":10,
            "precio_venta":25,"cantidad":50,"categoria":"Test"
        })
        ok(f"{tag} crear producto", r.status_code==200 and j.get("ok"), f"{r.status_code} {json.dumps(j,ensure_ascii=False)[:80]}")
    else:
        r, j = post(c, "/api/inventario/entrada", {"producto_id":"X","nombre":"X","precio_compra":1,"precio_venta":2,"cantidad":1,"categoria":"X"})
        ok(f"{tag} crear producto denegado", r.status_code==403, f"esperaba 403, got {r.status_code}")

    print(f"\n{S}\n{tag} 4. ASIGNAR INVENTARIO DIARIO (solo admin/dev)")
    if can_admin or can_dev:
        asig = {"vendedor_id":uid,"productos":[
            {"producto_id":"SIM01","nombre":"Producto Sim","cant_asignada":10,"precio_venta":25,"precio_costo":10}
        ]}
        r, j = post(c, "/api/inventario/asignar-diario", asig)
        ok(f"{tag} asignar inv", r.status_code==200 and j.get("ok"), f"{r.status_code}")

    print(f"\n{S}\n{tag} 5. INVENTARIO DIARIO DEL VENDEDOR")
    r, j = get(c, f"/api/inventario/diario/{uid}")
    ok(f"{tag} /inv/diario/{uid}", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 6. CONTEO VENDEDOR")
    r, j = post(c, "/api/inventario/diario/conteo", {"vendedor_id":uid,"producto_id":"SIM01","cant_final":7})
    ok(f"{tag} conteo", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 7. SNAPSHOT HISTORIAL (solo admin/dev)")
    if can_admin or can_dev:
        from datetime import datetime as _dt
        fh = _dt.now().strftime("%Y-%m-%d")
        snap = {"fecha":fh,"total_ventas":500.0,"num_transacciones":10,"productos_activos":1,
            "inventario_items":1,"ventas_data":[],"inventario_data":[],
            "ts_guardado":_dt.now().strftime("%Y-%m-%d %H:%M:%S")}
        r, j = post(c, "/api/historial/diario", snap)
        ok(f"{tag} snapshot", r.status_code==200 and j.get("ok"), f"{r.status_code}")

    print(f"\n{S}\n{tag} 8. CIERRE DE CAJA")
    from datetime import datetime as _dt
    fh = _dt.now().strftime("%Y-%m-%d")
    cierre = {"vendedor_id":uid,"fecha":fh,"total_ventas":500.0,"total_costo":200.0,"ganancia_neta":300.0,
        "items":[{"producto_id":"SIM01","nombre":"Producto Sim","cant_asignada":10,"cant_final":3,"precio_venta":25,"precio_costo":10}]}
    r, j = post(c, "/api/inventario/diario/cierre", cierre)
    ok(f"{tag} cierre caja", r.status_code==200 and j.get("ok"), f"{r.status_code} {json.dumps(j,ensure_ascii=False)[:100]}")

    print(f"\n{S}\n{tag} 9. HISTORIAL CIERRES")
    r, j = get(c, f"/api/inventario/diario/historial/{uid}")
    ok(f"{tag} hist cierres", r.status_code==200, f"{r.status_code}")
    ok(f"{tag} >=1 cierre", len(j.get("historial",[]))>=1, f"{len(j.get('historial',[]))} cierres")

    print(f"\n{S}\n{tag} 10. REPORTES")
    r, j = get(c, "/api/reportes/ventas?fecha_inicio=2024-01-01&fecha_fin=2030-12-31")
    ok(f"{tag} rep ventas", r.status_code in (200,403), f"{r.status_code}")
    r, j = get(c, "/api/reportes/resumen")
    ok(f"{tag} rep resumen", r.status_code in (200,403), f"{r.status_code}")

    print(f"\n{S}\n{tag} 11. DASHBOARD")
    r, j = get(c, "/api/dashboard/data")
    ok(f"{tag} dashboard", r.status_code in (200,403), f"{r.status_code}")

    print(f"\n{S}\n{tag} 12. AGENTE IA")
    r, j = post(c, "/api/ia/chat/secure", {"query":"como voy hoy"})
    ok(f"{tag} IA como voy", r.status_code==200, f"{r.status_code} {json.dumps(j,ensure_ascii=False)[:120]}")
    r, j = post(c, "/api/ia/chat/secure", {"query":"categorias"})
    ok(f"{tag} IA categorias", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 13. GASTOS Y DESCUENTOS")
    r, j = get(c, "/api/gastos")
    ok(f"{tag} gastos", r.status_code==403 if tag=="VENDEDOR" else 200, f"{r.status_code}")
    r, j = get(c, "/api/descuentos")
    ok(f"{tag} descuentos", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 14. ADMIN")
    if can_admin or can_dev:
        r, j = get(c, "/api/usuarios")
        ok(f"{tag} usuarios", r.status_code==200, f"{r.status_code}")
        r, j = get(c, "/api/licencias")
        ok(f"{tag} licencias", r.status_code==200, f"{r.status_code}")
        r, j = get(c, "/api/privilegios/vendedor")
        ok(f"{tag} privilegios", r.status_code==200, f"{r.status_code}")
        r, j = get(c, "/api/backup")
        ok(f"{tag} backup", r.status_code==200, f"{r.status_code}")
    elif rol == "supervisor":
        # Supervisor puede ver usuarios, licencias, privilegios, pero NO backup
        r, j = get(c, "/api/usuarios")
        ok(f"{tag} usuarios denegado (sup)", r.status_code==403, f"{r.status_code}")
        r, j = get(c, "/api/licencias")
        ok(f"{tag} licencias denegado (sup)", r.status_code==403, f"{r.status_code}")
        r, j = get(c, "/api/privilegios/vendedor")
        ok(f"{tag} privilegios (sup puede ver)", r.status_code==200, f"{r.status_code}")
        r, j = get(c, "/api/backup")
        ok(f"{tag} backup denegado", r.status_code==403, f"got {r.status_code}")
    else:
        for ep in ["/api/usuarios","/api/licencias","/api/privilegios/vendedor","/api/backup"]:
            r, j = get(c, ep)
            ok(f"{tag} {ep} denegado", r.status_code in (403,401), f"esperaba 403/401, got {r.status_code}")

    print(f"\n{S}\n{tag} 15. STATE / CONFIG")
    r, j = get(c, "/api/state")
    ok(f"{tag} state", r.status_code in (200,404), f"{r.status_code}")
    r, j = get(c, "/api/config/publica")
    ok(f"{tag} config publica", r.status_code==200, f"{r.status_code}")

    print(f"\n{S}\n{tag} 16. LOGOUT")
    r, j = post(c, "/api/auth/logout", {})
    ok(f"{tag} logout", r.status_code==200, f"{r.status_code}")
    r, j = get(c, "/api/auth/me")
    ok(f"{tag} sesion cerrada", r.status_code==401, f"{r.status_code}")


print("\n" + "#"*60)
print("#  SIMULACION COMPLETA TPV APK — TODOS LOS ROLES")
print("#"*60)

run_role_tests("DESARROLLADOR", "dev-001", "dev", "desarrollador", can_dev=True)
run_role_tests("ADMINISTRADOR", "admin-001", "admin", "administrador", can_admin=True)
run_role_tests("VENDEDOR", "vend-001", "vendedor1", "vendedor")
run_role_tests("SUPERVISOR", "sup-001", "supervisor1", "supervisor")

print("\n" + "="*60)
print(f"RESULTADO FINAL: {P} OK | {F} FALLAS")
if ERRORES:
    print(f"\nERRORES ({len(ERRORES)}):")
    for e in ERRORES:
        print(f"  - {e}")
print("="*60)

shutil.rmtree(tmpd, ignore_errors=True)
sys.exit(1 if F > 0 else 0)
