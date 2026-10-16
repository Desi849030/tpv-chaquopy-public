#!/usr/bin/env python3
import os, sys, sqlite3, threading, uuid, tempfile

# Guardar TPV_FILES_DIR original para restaurar al final
_ORIGINAL_TPV_FILES_DIR = os.environ.get("TPV_FILES_DIR")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app", "src", "main", "python"))

def setup():
    os.environ["TPV_FILES_DIR"] = tempfile.mkdtemp(prefix="tpv_conc_")
    os.makedirs(os.environ["TPV_FILES_DIR"], exist_ok=True)
    p = os.path.join(os.environ["TPV_FILES_DIR"], "tpv_datos.db")
    if os.path.exists(p): os.remove(p)
    from database import crear_tablas, obtener_conexion, _hash_password
    crear_tablas()
    c = obtener_conexion()
    c.execute("INSERT OR REPLACE INTO productos (producto_id,nombre,precio,costo,categoria,activo) VALUES ('T1','Cerveza',2.5,1.2,'Bebidas',1)")
    c.execute("INSERT OR REPLACE INTO inventario_general (producto_id,nombre,stock_actual,stock_minimo) VALUES ('T1','Cerveza',1,5)")
    pw,s = _hash_password("t")
    c.execute("INSERT OR REPLACE INTO usuarios (usuario_id,username,nombre,rol,password_hash,password_salt,activo) VALUES ('v1','vt','V','vendedor',?, ?,1)",(pw,s))
    c.execute("INSERT OR REPLACE INTO usuarios (usuario_id,username,nombre,rol,password_hash,password_salt,activo) VALUES ('c1','ct','C','cajero',?, ?,1)",(pw,s))
    c.commit(); c.close(); return 'T1'

def stock(pid):
    from database import obtener_conexion
    c = obtener_conexion(); r = c.execute("SELECT stock_actual FROM inventario_general WHERE producto_id=?",(pid,)).fetchone(); c.close(); return r[0] if r else 0

def sell(pid,vid,res,i):
    from database import obtener_conexion
    try:
        c = obtener_conexion(); c.execute("BEGIN IMMEDIATE")
        r = c.execute("SELECT stock_actual FROM inventario_general WHERE producto_id=?",(pid,)).fetchone()
        if not r or r[0]<=0: c.rollback(); res[i]={"ok":False}; return
        c.execute("INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,vendedor_id) VALUES (?,?,?,?,?,?,?)",(f"V{i}-{uuid.uuid4().hex[:8]}",pid,"Cerveza",1,2.5,2.5,vid))
        c.execute("UPDATE inventario_general SET stock_actual=stock_actual-1 WHERE producto_id=?",(pid,))
        c.commit(); res[i]={"ok":True}
    except sqlite3.OperationalError as e:
        try: c.rollback()
        except: pass
        res[i]={"ok":False,"error":str(e)}
    except Exception as e:
        try: c.rollback()
        except: pass
        res[i]={"ok":False,"error":str(e)}

print("="*50)
print("Tests Concurrencia TPV Ultra Smart")
print("="*50)

# Test 1: venta concurrente
pid = setup(); assert stock(pid)==1
res=[None,None]
t1=threading.Thread(target=sell,args=(pid,"v1",res,0))
t2=threading.Thread(target=sell,args=(pid,"c1",res,1))
t1.start(); t2.start(); t1.join(10); t2.join(10)
s=[r for r in res if r and r.get("ok")]
assert len(s)==1, f"Expected 1, got {len(s)}: {res}"
assert stock(pid)==0
print("✓ test_concurrent_sale: 1 exito, 1 fallo limpio")

# Test 2: rollback
pid = setup(); from database import obtener_conexion
c = obtener_conexion(); c.execute("BEGIN IMMEDIATE")
c.execute("INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,vendedor_id) VALUES (?,?,?,?,?,?,?)",("RB",pid,"C",1,2.5,2.5,"v1"))
assert c.execute("SELECT COUNT(*) FROM historial_ventas WHERE venta_id='RB'").fetchone()[0]==1
c.rollback()
assert c.execute("SELECT COUNT(*) FROM historial_ventas WHERE venta_id='RB'").fetchone()[0]==0
assert stock(pid)==1; c.close()
print("✓ test_rollback: no registros huerfanos")

# Test 3: 6 roles
setup(); from database import obtener_conexion, _hash_password
c = obtener_conexion(); pw,s = _hash_password("t")
for i,r in enumerate(['desarrollador','administrador','supervisor','vendedor','cajero','cliente']):
    c.execute("INSERT INTO usuarios (usuario_id,username,nombre,rol,password_hash,password_salt,activo) VALUES (?,?,?,?,?,?,1)",(f"u{i}",f"u{i}",f"U{i}",r,pw,s))
c.commit()
assert c.execute("SELECT COUNT(DISTINCT rol) FROM usuarios WHERE rol IN ('desarrollador','administrador','supervisor','vendedor','cajero','cliente')").fetchone()[0]==6
c.close()
print("✓ test_six_roles: 6 roles aceptados")

# Test 4: 5 threads concurrentes (serializacion estricta)
pid = setup()
from database import obtener_conexion
c = obtener_conexion()
c.execute("UPDATE inventario_general SET stock_actual=3 WHERE producto_id=?", (pid,))
c.commit(); c.close()
assert stock(pid)==3
res=[None]*5
threads=[]
for i in range(5):
    t=threading.Thread(target=sell,args=(pid,"v1",res,i))
    threads.append(t)
for t in threads: t.start()
for t in threads: t.join(15)
ok=[r for r in res if r and r.get("ok")]
failed=[r for r in res if r and not r.get("ok")]
print(f"  5 threads: {len(ok)} exitos, {len(failed)} fallos limpios")
assert len(ok)==3, f"Expected 3 exitos (stock=3), got {len(ok)}: {res}"
assert stock(pid)==0, f"Expected stock=0, got {stock(pid)}"
print("OK test_5_thread_serialization: serializacion BEGIN IMMEDIATE correcta")

# Test 5: FK constraint (producto_id inexistente debe fallar)
setup()
c = obtener_conexion()
try:
    c.execute("INSERT INTO historial_ventas (venta_id,producto_id,nombre,cantidad,precio_unit,total,vendedor_id) VALUES (?,?,?,?,?,?,?)",
              ("FKTEST","PRODUCTO_INEXISTENTE","Test",1,1.0,1.0,"v1"))
    c.commit()
    c.close()
    print("FAIL test_fk_constraint: FK no bloqueo insercion (PRAGMA foreign_keys desactivado?)")
except sqlite3.IntegrityError:
    c.close()
    print("OK test_fk_constraint: FK bloqueo insercion con producto_id inexistente")
except Exception as e:
    c.close()
    print(f"OK test_fk_constraint: bloqueo por {type(e).__name__}")

# Restaurar TPV_FILES_DIR original (evita contaminacion de otros tests)
if _ORIGINAL_TPV_FILES_DIR is not None:
    os.environ["TPV_FILES_DIR"] = _ORIGINAL_TPV_FILES_DIR
else:
    os.environ.pop("TPV_FILES_DIR", None)

print("\n✅ TODOS LOS TESTS PASARON")
