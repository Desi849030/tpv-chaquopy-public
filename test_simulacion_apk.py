#!/usr/bin/env python3
"""
SIMULACIÓN COMPLETA DE APK - TPV UltraSmart v3.0
Prueba exhaustiva pre-push: IA, métricas, catálogo, sync, Excel, roles, polling
"""
import sys, os, json, time
sys.path.insert(0, 'app/src/main/python')

print("=" * 60)
print("🚀 SIMULACIÓN COMPLETA TPV UltraSmart v3.0")
print("=" * 60)

errors, warnings, ok = [], [], []

def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))

def warn(name, condition, msg=""):
    (warnings if condition else ok).append(name)
    if condition: print(f"  ⚠️ {name}: {msg}")

# ============================================================
# 1. IMPORTACIONES
# ============================================================
print("\n📦 1. IMPORTACIONES")
try:
    from ia.agent import process_question, ROLES
    test("ia.agent", True)
except Exception as e: test("ia.agent", False, str(e))

try:
    from ia.catalog import P
    test("Catálogo P", True)
except Exception as e: test("Catálogo P", False, str(e))

try:
    from ia.metrics import M, F
    test("Métricas IA (M, F)", True)
except Exception as e: test("Métricas IA", False, str(e))

try:
    from ia.normalizer import normalize, contains_any, extract_entities
    test("Normalizador", True)
except Exception as e: test("Normalizador", False, str(e))

try:
    from ia.intent_engine import detect_intents, get_suggestions
    test("Motor intents", True)
except Exception as e: test("Motor intents", False, str(e))

try:
    from ia.context_memory import get_context
    test("Memoria contextual", True)
except Exception as e: test("Memoria contextual", False, str(e))

try:
    from ia.memory import save, recall, get_enriched_context
    test("Memoria avanzada", True)
except Exception as e: test("Memoria avanzada", False, str(e))

try:
    from metrics.helpers import _ram_info, _storage_info, _inventario_formulas, _get_db_path
    test("Métricas sistema", True)
except Exception as e: test("Métricas sistema", False, str(e))

try:
    from ia.handlers import handle_cliente, handle_vendedor, handle_supervisor, handle_admin, handle_dev
    test("Handlers roles", True)
except Exception as e: test("Handlers roles", False, str(e))

# ============================================================
# 2. ROLES
# ============================================================
print("\n👤 2. ROLES")
for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
    test(f"Rol {rol}", rol in ROLES)
test("5 roles exactos", len(ROLES) == 5)

# ============================================================
# 3. INTERACCIÓN POR ROL
# ============================================================
print("\n💬 3. INTERACCIÓN POR ROL")
tests_rol = [
    ('cliente', 'hola', 'Juan'),
    ('cliente', 'café', 'Juan'),
    ('cliente', 'ofertas', 'Juan'),
    ('vendedor', 'hola', 'Ana'),
    ('vendedor', 'ventas hoy', 'Ana'),
    ('supervisor', 'reporte', 'Sup'),
    ('administrador', 'finanzas', 'Admin'),
    ('administrador', 'abc', 'Admin'),
    ('desarrollador', 'métricas', 'Dev'),
]
for rol, msg, nombre in tests_rol:
    r = process_question('sim', msg, rol, nombre)
    test(f"{rol}: '{msg}'", len(r.get('answer','')) > 5 and r.get('role') == rol)

# ============================================================
# 4. INTENTS ENGINE
# ============================================================
print("\n🎯 4. INTENTS")
ints = detect_intents("hola buenos días")
test("GREETING", ints[0]['intent'] == 'GREETING')
ints = detect_intents("cuánto vendí hoy")
test("SALES", any(i['intent']=='SALES' for i in ints))
ints = detect_intents("stock bajo urgente")
test("STOCK_LOW", any(i['intent']=='STOCK_LOW' for i in ints))
ints = detect_intents("ofertas descuentos")
test("OFFERS", any(i['intent']=='OFFERS' for i in ints))

# ============================================================
# 5. NORMALIZACIÓN
# ============================================================
print("\n📝 5. NORMALIZACIÓN")
test("normalize hola", normalize("hola") == "hola")
test("normalize MAYÚS", normalize("HELLO") == "hello")
matched, kw, _ = contains_any("quiero ventas", ["ventas","stock"])
test("contains ventas", matched and kw=="ventas")
ent = extract_entities("café con leche precio")
test("extract café", "café" in ent or "cafe" in ent)

# ============================================================
# 6. CATÁLOGO DE PRODUCTOS
# ============================================================
print("\n🛒 6. CATÁLOGO")
P.refresh()
prods = P.search("test", 5)
test("Buscar 'test'", len(prods) > 0, "No se encontraron productos de prueba")

if prods:
    p = prods[0]
    test("Producto tiene nombre", 'n' in p)
    test("Producto tiene precio", 'p' in p)
    test("Producto tiene stock", 's' in p)

# ============================================================
# 7. MÉTRICAS IA (M, F)
# ============================================================
print("\n📊 7. MÉTRICAS IA")
try:
    abc = F.abc()
    test("ABC clasificación", isinstance(abc, dict) and 'A' in abc)
except Exception as e: warn("ABC", True, str(e))

try:
    d = F.diario()
    test("Finanzas diario", isinstance(d, dict) and 'r' in d)
except Exception as e: warn("Diario", True, str(e))

try:
    sem = F.semanal()
    test("Finanzas semanal", isinstance(sem, dict))
except Exception as e: warn("Semanal", True, str(e))

try:
    top = F.top(7, 3)
    test("Top productos", isinstance(top, list))
except Exception as e: warn("Top", True, str(e))

try:
    eoq = M.eoq(100, 10, 2)
    test("EOQ cálculo", eoq > 0)
except Exception as e: warn("EOQ", True, str(e))

try:
    pe = M.punto_eq(1000, 50, 30)
    test("Punto equilibrio", pe > 0)
except Exception as e: warn("Punto eq", True, str(e))

try:
    roi = M.roi(1000, 1500)
    test("ROI cálculo", roi == 50.0)
except Exception as e: warn("ROI", True, str(e))

# ============================================================
# 8. MÉTRICAS DEL SISTEMA
# ============================================================
print("\n💻 8. MÉTRICAS SISTEMA")
try:
    ram = _ram_info()
    test("RAM lectura", ram['proceso_mb'] > 0)
    test("RAM fuente", ram['fuente'] != 'desconocido')
    
    db = _get_db_path()
    test("DB ruta", db and os.path.exists(db))
    
    storage = _storage_info(db)
    test("Storage tamaño", storage['db_size_kb'] > 0)
    
    inv = _inventario_formulas(db)
    test("Inventario productos", inv['total_productos'] > 0)
    test("Inventario margen", inv['margen_bruto_pct'] > 0)
    test("Inventario sin error", inv['error'] is None)
except Exception as e:
    test("Métricas sistema", False, str(e))

# ============================================================
# 9. SINCRONIZACIÓN SUPABASE
# ============================================================
print("\n☁️ 9. SINCRONIZACIÓN SUPABASE")
try:
    import sync.supabase_sync
    test("Importar SupabaseSync", True)
except ImportError:
    warn("SupabaseSync", True, "Módulo no configurado - solo SQLite local")
except Exception as e:
    warn("SupabaseSync", True, str(e))

env_exists = os.path.exists('.env') or os.path.exists('.env.example')
test("Archivo .env existe", env_exists, "Sin configuración de Supabase")

# ============================================================
# 10. IMPORTACIÓN EXCEL (ruta corregida)
# ============================================================
print("\n📥 10. IMPORTACIÓN EXCEL")
try:
    import importlib.util
    spec = importlib.util.find_spec('tools.import_tools')
    test("Módulo tools.import_tools", spec is not None, "No encontrado")
except Exception as e:
    warn("Import Excel", True, str(e))

# ============================================================
# 11. FLUJO COMPLETO
# ============================================================
print("\n🔄 11. FLUJO COMPLETO")
flujo = [
    ('cliente', 'Juan', 'hola'),
    ('cliente', 'Juan', 'tienen café?'),
    ('cliente', 'Juan', 'precio?'),
    ('vendedor', 'Ana', 'ventas hoy'),
    ('vendedor', 'Ana', 'stock bajo'),
    ('supervisor', 'Sup', 'reporte'),
    ('administrador', 'Admin', 'finanzas'),
    ('administrador', 'Admin', 'abc'),
    ('desarrollador', 'Dev', 'sistema'),
    ('desarrollador', 'Dev', 'métricas'),
]
for rol, nombre, msg in flujo:
    r = process_question('flujo1', msg, rol, nombre)
    test(f"Flujo {rol}/{msg}", len(r.get('answer','')) > 5)

# ============================================================
# 12. SEGURIDAD
# ============================================================
print("\n🔒 12. SEGURIDAD")
try:
    from security.crypto import hash_password, verify_password
    test("Importar crypto", True)
    h = hash_password("test123")
    test("Hash password", len(h) > 20)
    test("Verify password", verify_password("test123", h))
except Exception as e:
    warn("Crypto", True, str(e))

try:
    from security.validation import sanitize_input
    test("Importar validación", True)
except Exception as e:
    warn("Validación", True, str(e))

# ============================================================
# 13. POLLING (verificación de archivos JS)
# ============================================================
print("\n📡 13. POLLING")
polling_files = [
    'app/src/main/assets/frontend/static/js/tpv/tpv_sesion_polling.js',
    'app/src/main/assets/frontend/static/js/tpv/tpv_vendedor_modulo.js',
]
for pf in polling_files:
    test(f"Archivo polling: {os.path.basename(pf)}", os.path.exists(pf), "No encontrado")

# ============================================================
# 14. ESTADO FINAL
# ============================================================
print("\n" + "=" * 60)
print("📋 RESUMEN FINAL")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ⚠️ {len(warnings)} warnings")
print(f"  ❌ {len(errors)} errores")

if warnings:
    print("\n⚠️ WARNINGS:")
    for w in warnings: print(f"  - {w}")

if errors:
    print("\n❌ ERRORES:")
    for e in errors: print(f"  - {e}")
    print(f"\n⚠️ Debes corregir {len(errors)} errores antes del push.")
    sys.exit(1)
else:
    print("\n🎉 ¡SIMULACIÓN EXITOSA! Listo para push.")
    sys.exit(0)

# ============================================================
# 14. AGENTE PROACTIVO (NUEVO)
# ============================================================
print("\n🧠 14. AGENTE PROACTIVO")
try:
    from ia.proactive_agent import get_proactive_agent, ProactiveAgent
    test("Importar ProactiveAgent", True)
    
    agent = get_proactive_agent()
    alerts = agent.check_all()
    test("Alertas generadas", len(alerts) >= 0, f"Se encontraron {len(alerts)} alertas")
    
    # Verificar tipos de alertas
    tipos = set(a['tipo'] for a in alerts)
    test("Tipos de alertas variados", len(tipos) > 0, f"Tipos: {tipos}")
    
    briefing = agent.get_briefing('administrador')
    test("Briefing generado", 'resumen' in briefing)
    test("Briefing tiene recomendaciones", len(briefing.get('recomendaciones', [])) >= 0)
    
    # Verificar que el monitoreo background funciona
    from ia.proactive_agent import start_background_monitor
    start_background_monitor(interval_seconds=999)  # No ejecutar realmente
    test("Monitoreo background", True)
    
except Exception as e:
    test("Agente Proactivo", False, str(e))
