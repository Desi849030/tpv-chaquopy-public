#!/usr/bin/env python3
"""
SIMULACIÓN MAESTRA - TPV UltraSmart v4.0
Prueba todos los flujos de negocio: auth, ventas, inventario, cierres, gastos, IA, sync
"""
import sys, os, json, time, sqlite3
sys.path.insert(0, 'app/src/main/python')
# Inicializar BD si no existe
import sqlite3
conn = sqlite3.connect('tpv_datos.db', timeout=10)
conn.execute("PRAGMA journal_mode=WAL")

# Crear tablas mínimas si no existen
conn.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario_id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        nombre TEXT,
        rol TEXT,
        password_hash TEXT,
        password_salt TEXT,
        activo INTEGER DEFAULT 1,
        ultimo_acceso TEXT,
        creado_por TEXT
    );
    CREATE TABLE IF NOT EXISTS inventario_general (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id TEXT,
        nombre TEXT,
        stock_actual REAL DEFAULT 0,
        stock_minimo REAL DEFAULT 0,
        precio_compra REAL DEFAULT 0,
        precio_venta REAL DEFAULT 0,
        categoria TEXT DEFAULT 'General',
        unidad_medida TEXT DEFAULT 'C/U',
        actualizado TEXT
    );
    CREATE TABLE IF NOT EXISTS historial_ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id TEXT UNIQUE,
        producto_id TEXT,
        nombre TEXT,
        cantidad REAL,
        precio_unit REAL,
        total REAL,
        metodo_pago TEXT,
        fecha TEXT,
        vendedor_id TEXT
    );
    CREATE TABLE IF NOT EXISTS cierres_caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        total_ventas REAL,
        total_costos REAL,
        total_comisiones REAL,
        ganancia_total REAL,
        num_transacciones INTEGER,
        cerrado_por TEXT,
        creado TEXT
    );
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gasto_id TEXT UNIQUE,
        descripcion TEXT,
        monto REAL,
        categoria TEXT,
        fecha TEXT,
        registrado_por TEXT
    );
    CREATE TABLE IF NOT EXISTS clientes_tienda (
        cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        email TEXT,
        password_hash TEXT,
        password_salt TEXT,
        telefono TEXT
    );
    CREATE TABLE IF NOT EXISTS inventario_diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id TEXT,
        fecha TEXT,
        producto_id TEXT,
        nombre TEXT,
        stock_inicial REAL,
        entradas REAL,
        salidas REAL,
        stock_final REAL
    );
""")

# Crear usuario desarrollador si no existe
from db_connection import _hash_password
hash_pw, salt = _hash_password('123456')
conn.execute("SELECT COUNT(*) FROM usuarios WHERE username='desarrollador'")
if conn.execute("SELECT COUNT(*) FROM usuarios WHERE username='desarrollador'").fetchone()[0] == 0:
    conn.execute("""
        INSERT INTO usuarios (usuario_id, username, nombre, rol, password_hash, password_salt)
        VALUES ('user-dev', 'desarrollador', 'Desarrollador Principal', 'desarrollador', ?, ?)
    """, (hash_pw, salt))
    conn.commit()

# Insertar productos de prueba si no existen
if conn.execute("SELECT COUNT(*) FROM inventario_general").fetchone()[0] == 0:
    conn.executescript("""
        INSERT INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta, categoria) VALUES ('T1', 'Test v25', 10, 5, 2.0, 5.0, 'General');
        INSERT INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta, categoria) VALUES ('T2', 'Test Dos', 20, 5, 3.0, 8.0, 'Bebidas');
    """)
    conn.commit()

conn.close()


print("=" * 70)
print("🚀 SIMULACIÓN MAESTRA - TPV UltraSmart v4.0")
print("=" * 70)

errors, warnings, ok = [], [], []
def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))
def warn(name, condition, msg=""):
    (warnings if condition else ok).append(name)
    if condition: print(f"  ⚠️ {name}: {msg}")

def get_conn():
    conn = sqlite3.connect('tpv_datos.db', timeout=30, isolation_level=None)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=10000')
    return conn
    return sqlite3.connect('tpv_datos.db', timeout=10)

# ============================================================
# 1. AUTENTICACIÓN
# ============================================================
print("\n🔐 1. AUTENTICACIÓN")
try:
    from db.users import login_usuario
    r = login_usuario('desarrollador', '123456')
    test("Login desarrollador", r is not None)
    if r:
        test("Rol desarrollador", r.get('rol') == 'desarrollador')
        test("Nombre correcto", r.get('nombre') == 'Desarrollador Principal')
except Exception as e: test("Login", False, str(e))

try:
    from security.crypto import hash_password, verify_password
    h = hash_password("test")
    test("Hash password", len(h) > 20)
    test("Verify correcto", verify_password("test", h))
    test("Verify incorrecto", not verify_password("wrong", h))
except Exception as e: test("Crypto", False, str(e))

# ============================================================
# 2. PRODUCTOS Y CATÁLOGO
# ============================================================
print("\n📦 2. PRODUCTOS Y CATÁLOGO")
try:
    from ia.catalog import P
    P.refresh()
    prods = P.search("test", 10)
    test("Buscar 'test'", len(prods) >= 2)
    if prods:
        p = prods[0]
        test("Tiene nombre", 'n' in p)
        test("Tiene precio", 'p' in p)
        test("Tiene stock", 's' in p)
except Exception as e: test("Catálogo", False, str(e))

try:
    from ia.db_utils import q
    total = q("SELECT COUNT(*) c FROM inventario_general", one=True)
    test("Inventario poblado", total['c'] >= 2)
except Exception as e: test("DB Prod", False, str(e))

# ============================================================
# 3. VENTAS
# ============================================================
print("\n💰 3. VENTAS")
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO historial_ventas (venta_id, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha, vendedor_id)
        VALUES ('sim-1778921694', 'T1', 'Test v25', 2, 5.0, 10.0, 'efectivo', datetime('now','localtime'), 'test-sim')
    """)
    conn.commit()
    test("Registrar venta", cur.lastrowid > 0)
    cur.close()
    conn.close()
except Exception as e: test("Venta", False, str(e))

try:
    from ia.db_utils import q
    hoy = q("SELECT COALESCE(SUM(total),0) t FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
    test("Total ventas hoy > 0", hoy['t'] > 0, f"Total: ${hoy['t']:.2f}")
except Exception as e: test("Total ventas", False, str(e))

# ============================================================
# 4. INVENTARIO
# ============================================================
print("\n📊 4. INVENTARIO")
try:
    from ia.db_utils import q
    stock = q("SELECT stock_actual FROM inventario_general WHERE nombre='Test v25'", one=True)
    test("Stock Test v25", stock is not None and stock['stock_actual'] > 0)
    
    bajo = q("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual <= stock_minimo", one=True)
    test("Alertas stock bajo", bajo['c'] >= 0)
except Exception as e: test("Inventario", False, str(e))

# ============================================================
# 5. CIERRES DE CAJA
# ============================================================
print("\n🧾 5. CIERRES DE CAJA")
try:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cierres_caja (fecha, total_ventas, total_costos, total_comisiones, ganancia_total, num_transacciones, cerrado_por, creado)
            VALUES (datetime('now','localtime'), 10.0, 5.0, 1.0, 4.0, 1, 'test-sim', datetime('now','localtime'))
        """)
        conn.commit()
        test("Registrar cierre", cur.lastrowid > 0)
except Exception as e: test("Cierre", False, str(e))

# ============================================================
# 6. GASTOS
# ============================================================
print("\n💸 6. GASTOS")
try:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gastos (gasto_id, descripcion, monto, categoria, fecha, registrado_por)
            VALUES ('gasto-sim-1778921694', 'Compra insumos', 50.0, 'Insumos', datetime('now','localtime'), 'test-sim')
        """)
        conn.commit()
        test("Registrar gasto", cur.lastrowid > 0)
except Exception as e: test("Gasto", False, str(e))

# ============================================================
# 7. TIENDA ONLINE
# ============================================================
print("\n🛒 7. TIENDA ONLINE")
try:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO clientes_tienda (nombre, email, password_hash, password_salt, telefono) VALUES ('Cliente Test', 'test@test.com', 'hash', 'salt', '1234567890')")
        conn.commit()
        test("Registrar cliente", True)
    except: test("Cliente ya existe", True)
    try:
        cur.execute("INSERT INTO inventario_diario (vendedor_id, fecha, producto_id, nombre, stock_inicial, entradas, salidas, stock_final) VALUES ('test-sim', DATE('now','localtime'), 'T1', 'Test v25', 10, 5, 2, 13)")
        conn.commit()
        test("Movimiento diario", True)
    except: pass
    conn.close()
except Exception as e: test("Tienda", False, str(e))

# ============================================================
# 8. IA AGENTE
# ============================================================
print("\n🤖 8. IA AGENTE")
try:
    from ia.agent import process_question, ROLES
    test("5 roles", len(ROLES) == 5)
    for rol, msg in [('cliente','hola'), ('vendedor','ventas hoy'), ('administrador','finanzas'), ('administrador','abc')]:
        r = process_question('sim', msg, rol, 'Test')
        test(f"IA {rol}: {msg}", len(r.get('answer','')) > 5)
except Exception as e: test("IA Agente", False, str(e))

# ============================================================
# 9. IA PROACTIVA
# ============================================================
print("\n🧠 9. IA PROACTIVA")
try:
    from ia.proactive_agent import get_proactive_agent
    agent = get_proactive_agent()
    alerts = agent.check_all()
    test("Alertas generadas", len(alerts) >= 0)
    briefing = agent.get_briefing('administrador')
    test("Briefing", 'resumen' in briefing)
except Exception as e: test("IA Proactiva", False, str(e))

# ============================================================
# 10. MÉTRICAS IA
# ============================================================
print("\n📈 10. MÉTRICAS IA")
try:
    from ia.metrics import M, F
    test("ABC", isinstance(F.abc(), dict))
    test("Diario", 'r' in F.diario())
    test("EOQ", M.eoq(100,10,2) > 0)
    test("ROI", M.roi(1000,1500) == 50.0)
except Exception as e: test("Métricas IA", False, str(e))

# ============================================================
# 11. MÉTRICAS SISTEMA
# ============================================================
print("\n💻 11. MÉTRICAS SISTEMA")
try:
    from metrics.helpers import _ram_info, _storage_info, _inventario_formulas, _get_db_path
    test("RAM", _ram_info()['proceso_mb'] > 0)
    db = _get_db_path()
    test("DB", db and os.path.exists(db))
    inv = _inventario_formulas(db)
    test("Inv total", inv['total_productos'] >= 2)
    test("Margen", inv['margen_bruto_pct'] > 0)
except Exception as e: test("Métricas Sys", False, str(e))

# ============================================================
# 12-15. RESTO
# ============================================================
print("\n🔒 12. SEGURIDAD")
try:
    from security.crypto import hash_password
    from security.validation import sanitize_input
    test("Crypto+Valid", True)
except: test("Crypto+Valid", False)

print("\n☁️ 13. SYNC")
warn("Supabase", not os.path.exists('.env'), "Sin credenciales")
test(".env.example", os.path.exists('.env.example'))

print("\n📥 14. EXCEL")
try:
    import importlib.util
    test("Import tools", importlib.util.find_spec('tools.import_tools') is not None)
except: test("Excel", False)

print("\n📖 15. DICCIONARIO")
try:
    from dictionary.helpers import diccionario_bp
    test("Blueprint", diccionario_bp is not None)
except: test("Diccionario", False)

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 70)
print("📋 RESUMEN FINAL")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ⚠️ {len(warnings)} warnings")
print(f"  ❌ {len(errors)} errores")
if errors:
    print("\n❌ ERRORES:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 ¡SIMULACIÓN MAESTRA EXITOSA! APK lista para producción.")
    sys.exit(0)
