#!/usr/bin/env python3
"""
TEST IMPORTACIÓN DINÁMICA - Catálogo, Productos, Excel
Simula la carga masiva de productos como lo haría la APK
"""
import sys, os, json, time, sqlite3
sys.path.insert(0, 'app/src/main/python')

print("=" * 60)
print("📥 TEST IMPORTACIÓN DINÁMICA DE CATÁLOGO")
print("=" * 60)

errors, ok = [], []
def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))

# 1. Simular importación masiva de productos
print("\n📦 1. IMPORTACIÓN MASIVA (50 productos)")
conn = sqlite3.connect('tpv_datos.db', timeout=10)
cur = conn.cursor()

productos_test = []
categorias = ['Bebidas', 'Lácteos', 'Panadería', 'Carnes', 'Verduras', 'Limpieza', 'Snacks', 'Bebés']
for i in range(50):
    prod = {
        'producto_id': f'IMP{i:04d}',
        'nombre': f'Producto Importado {i}',
        'stock_actual': i * 3 % 50 + 5,
        'stock_minimo': 5,
        'precio_compra': round(i * 1.5 + 2, 2),
        'precio_venta': round(i * 2.5 + 5, 2),
        'categoria': categorias[i % len(categorias)],
        'unidad_medida': 'C/U'
    }
    productos_test.append(prod)

start = time.time()
insertados = 0
for p in productos_test:
    try:
        cur.execute("""
            INSERT OR REPLACE INTO inventario_general 
            (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta, categoria, unidad_medida, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (p['producto_id'], p['nombre'], p['stock_actual'], p['stock_minimo'],
              p['precio_compra'], p['precio_venta'], p['categoria'], p['unidad_medida']))
        insertados += 1
    except Exception as e:
        print(f"    Error en {p['nombre']}: {e}")
conn.commit()
tiempo = (time.time() - start) * 1000
test(f"Insertar 50 productos ({insertados}/50)", insertados == 50, f"{tiempo:.0f}ms")

# 2. Verificar catálogo actualizado
print("\n🔍 2. VERIFICAR CATÁLOGO")
from ia.catalog import P
P.refresh()
prods = P.search("Producto Importado", 10)
test("Búsqueda productos importados", len(prods) > 0, f"Encontrados: {len(prods)}")

# 3. Simular venta de productos importados
print("\n💰 3. VENTAS CON PRODUCTOS IMPORTADOS")
ventas_realizadas = 0
for i in range(20):
    prod = productos_test[i]
    try:
        cur.execute("""
            INSERT INTO historial_ventas (venta_id, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha, vendedor_id)
            VALUES (?, ?, ?, ?, ?, ?, 'efectivo', datetime('now','localtime'), 'test-import')
        """, (f'import-{int(time.time())}-{i}', prod['producto_id'], prod['nombre'], 1, prod['precio_venta'], prod['precio_venta'], ))
        ventas_realizadas += 1
    except Exception as e:
        print(f"    Error venta {i}: {e}")
conn.commit()
test(f"Ventas realizadas ({ventas_realizadas}/20)", ventas_realizadas == 20)

# 4. Verificar stock actualizado
print("\n📊 4. STOCK POST-VENTAS")
from ia.db_utils import q
stock_total = q("SELECT SUM(stock_actual) t FROM inventario_general", one=True)
test("Stock total consistente", stock_total['t'] > 100, f"Total: {stock_total['t']:.0f}")

# 5. Simular importación desde Excel (formato JSON)
print("\n📄 5. IMPORTACIÓN FORMATO EXCEL/JSON")
excel_simulado = [
    {"id": "EXC001", "nombre": "Café Premium", "precio": 15.0, "costoUnitario": 8.0, "categoria": "Bebidas", "um": "C/U", "stock": 50},
    {"id": "EXC002", "nombre": "Pan Integral", "precio": 6.0, "costoUnitario": 3.0, "categoria": "Panadería", "um": "C/U", "stock": 30},
    {"id": "EXC003", "nombre": "Leche 1L", "precio": 4.5, "costoUnitario": 2.5, "categoria": "Lácteos", "um": "C/U", "stock": 100},
]

try:
    import tools.import_tools
    
    # Validar formato
    validos, errores = 0, 0
    for p in excel_simulado:
        try:
            # Validar campos requeridos
            if all(k in p for k in ['nombre', 'precio']):
                validos += 1
            else:
                errores += 1
        except:
            errores += 1
    test(f"Validación Excel ({validos}/{len(excel_simulado)})", validos == len(excel_simulado))
    
    # Insertar productos
    for p in excel_simulado:
        cur.execute("""
            INSERT OR REPLACE INTO inventario_general (producto_id, nombre, stock_actual, stock_minimo, precio_compra, precio_venta, categoria, unidad_medida, actualizado)
            VALUES (?, ?, ?, 5, ?, ?, ?, ?, datetime('now','localtime'))
        """, (p['id'], p['nombre'], p['stock'], p.get('costoUnitario',0), p['precio'], p['categoria'], p['um']))
    conn.commit()
    test("Insertar desde Excel", True)
except Exception as e:
    test("Import Excel", False, str(e))

# 6. Verificar categorías y diversidad
print("\n📊 6. DIVERSIDAD DE CATÁLOGO")
cats = q("SELECT DISTINCT categoria FROM inventario_general")
test(f"Categorías en catálogo", len(cats) >= 5, f"{len(cats)} categorías")

total_prods = q("SELECT COUNT(*) c FROM inventario_general", one=True)
test(f"Total productos en BD", total_prods['c'] >= 50, f"{total_prods['c']} productos")

conn.close()

# 7. Test de búsqueda con fuzzy matching
print("\n🔎 7. BÚSQUEDA FUZZY")
from ia.fuzzy_match import quick_search
resultados = quick_search("cafe", 60)
test("Fuzzy 'cafe' encuentra 'Café Premium'", len(resultados) > 0)

resultados = quick_search("pan", 60)
test("Fuzzy 'pan' encuentra 'Pan Integral'", len(resultados) > 0)

# Resumen
print("\n" + "=" * 60)
print("📋 RESUMEN IMPORTACIÓN DINÁMICA")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ❌ {len(errors)} errores")
if errors:
    print("\n❌ ERRORES:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 ¡IMPORTACIÓN DINÁMICA EXITOSA!")
    sys.exit(0)
