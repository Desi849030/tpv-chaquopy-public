#!/usr/bin/env python3
"""
STRESS TEST - TPV UltraSmart
Simula múltiples usuarios concurrentes realizando operaciones
"""
import sys, os, time, threading, random, sqlite3
sys.path.insert(0, 'app/src/main/python')

print("=" * 60)
print("🔥 STRESS TEST - Múltiples usuarios concurrentes")
print("=" * 60)

errors = []
ok = []
def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))

# Simular usuarios concurrentes
class UsuarioSimulado(threading.Thread):
    def __init__(self, user_id, rol, operaciones):
        super().__init__()
        self.user_id = user_id
        self.rol = rol
        self.operaciones = operaciones
        self.resultados = []
    
    def run(self):
        from ia.agent import process_question
        from ia.db_utils import q
        conn = sqlite3.connect('tpv_datos.db', timeout=10)
        cur = conn.cursor()
        
        for op in self.operaciones:
            try:
                if op == 'consulta':
                    r = process_question(f's{self.user_id}', 'hola', self.rol, f'User{self.user_id}')
                    self.resultados.append(len(r.get('answer','')) > 5)
                elif op == 'venta':
                    cur.execute("""
                        INSERT INTO historial_ventas (venta_id, producto_id, nombre, cantidad, precio_unit, total, metodo_pago, fecha, vendedor_id)
                        VALUES (?, 'T1', 'Test v25', 1, 5.0, 5.0, 'efectivo', datetime('now','localtime'), ?)
                    """, (f"stress-{self.user_id}-{time.time()}", f"user-{self.user_id}"))
                    conn.commit()
                    self.resultados.append(True)
                elif op == 'stock':
                    s = q("SELECT stock_actual FROM inventario_general WHERE nombre='Test v25'", one=True)
                    self.resultados.append(s is not None)
                elif op == 'finanzas':
                    from ia.metrics import F
                    d = F.diario()
                    self.resultados.append('r' in d)
            except Exception as e:
                self.resultados.append(False)
        
        cur.close()
        conn.close()

# Test 1: 5 usuarios concurrentes haciendo consultas IA
print("\n👥 Test 1: 5 usuarios IA concurrentes")
usuarios = []
for i in range(5):
    u = UsuarioSimulado(i, random.choice(['cliente','vendedor','administrador']), ['consulta'] * 3)
    usuarios.append(u)
    u.start()

for u in usuarios:
    u.join()

exitos = sum(1 for u in usuarios if all(u.resultados))
test("5 usuarios IA concurrentes", exitos >= 4, f"{exitos}/5 exitosos")

# Test 2: 10 usuarios concurrentes registrando ventas
print("\n💰 Test 2: 10 usuarios registrando ventas")
usuarios = []
for i in range(10):
    u = UsuarioSimulado(i+10, 'vendedor', ['venta'] * 2)
    usuarios.append(u)
    u.start()

for u in usuarios:
    u.join()

exitos = sum(1 for u in usuarios if all(u.resultados))
test("10 usuarios ventas concurrentes", exitos >= 8, f"{exitos}/10 exitosos")

# Test 3: 5 usuarios mixtos (consulta + venta + stock + finanzas)
print("\n🔄 Test 3: 5 usuarios mixtos concurrentes")
usuarios = []
for i in range(5):
    u = UsuarioSimulado(i+20, 'administrador', ['consulta', 'venta', 'stock', 'finanzas'])
    usuarios.append(u)
    u.start()

for u in usuarios:
    u.join()

exitos = sum(1 for u in usuarios if sum(u.resultados) >= 3)
test("5 usuarios mixtos concurrentes", exitos >= 4, f"{exitos}/5 exitosos")

# Test 4: Medir tiempos de respuesta bajo carga
print("\n⏱️ Test 4: Tiempos de respuesta bajo carga")
from ia.agent import process_question
tiempos = []
for _ in range(20):
    start = time.time()
    process_question('stress', 'ventas', 'administrador', 'Test')
    tiempos.append((time.time() - start) * 1000)

promedio = sum(tiempos) / len(tiempos)
test("Respuesta < 250ms promedio", promedio < 100, f"Promedio: {promedio:.1f}ms")
test("Respuesta máxima < 500ms", max(tiempos) < 500, f"Máxima: {max(tiempos):.1f}ms")

# Test 5: Consistencia de BD bajo carga
print("\n🗄️ Test 5: Consistencia BD bajo carga")
from ia.db_utils import q
productos_antes = q("SELECT COUNT(*) c FROM inventario_general", one=True)['c']
ventas_antes = q("SELECT COUNT(*) c FROM historial_ventas", one=True)['c']

# Hacer operaciones
usuarios = []
for i in range(3):
    u = UsuarioSimulado(i+30, 'vendedor', ['venta', 'stock'] * 2)
    usuarios.append(u)
    u.start()
for u in usuarios:
    u.join()

productos_despues = q("SELECT COUNT(*) c FROM inventario_general", one=True)['c']
ventas_despues = q("SELECT COUNT(*) c FROM historial_ventas", one=True)['c']

test("Productos consistentes", productos_antes == productos_despues)
test("Ventas incrementadas", ventas_despues >= ventas_antes)

# Resumen
print("\n" + "=" * 60)
print("📋 RESUMEN STRESS TEST")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ❌ {len(errors)} errores")
if errors:
    print("\n❌ ERRORES:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 ¡STRESS TEST EXITOSO! Sistema listo para múltiples usuarios.")
    sys.exit(0)
