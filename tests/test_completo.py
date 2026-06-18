"""Tests completos del TPV Ultra Smart v8.0"""
import requests, json

BASE = 'http://127.0.0.1:5000'
passed = 0
failed = 0
total = 0

def check(name, condition, msg=""):
    global passed, failed, total
    total += 1
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}: {msg}")
        failed += 1

def api(method, path, **kw):
    url = BASE + path
    try:
        if method == 'GET':
            return requests.get(url, timeout=5)
        return requests.post(url, json=kw.get('json', {}), timeout=5)
    except Exception as e:
        return None

print("=" * 60)
print("🧪 TPV Ultra Smart - Tests Completos")
print("=" * 60)

# Auth
print("\n🔐 AUTH")
r = api('GET', '/api/health')
check("Health check", r is not None and r.status_code == 200)

r = api('POST', '/api/auth/login', json={'username':'desarrollador','password':'123456'})
check("Login desarrollador", r is not None and r.json().get('ok'))

r = api('POST', '/api/auth/login', json={'username':'admin','password':'admin'})
check("Login admin", r is not None and r.json().get('ok'))

r = api('GET', '/api/auth/me')
check("Auth me", r is not None and 'usuario' in r.json())

# Catálogo
print("\n📦 CATÁLOGO")
r = api('GET', '/api/publico/catalogo')
check("Lista productos", r is not None and len(r.json().get('productos',[])) >= 13)

r = api('GET', '/api/publico/catalogo')
check("Producto con precio", r is not None and r.json()['productos'][0]['precio'] > 0)

# Ventas
print("\n💰 VENTAS")
r = api('POST', '/api/ventas/atomic', json={'items':[{'id':'test','nombre':'Test','cantidad':1,'precio':10}]})
check("Registrar venta", r is not None and r.json().get('ok'))

r = api('GET', '/api/ventas/totales')
check("Totales ventas", r is not None and 'hoy' in r.json())

r = api('POST', '/api/ventas/cierre', json={'fecha':'2026-05-30'})
check("Cierre caja", r is not None and (r.json().get('ok') or "UNIQUE" in r.json().get('error','')))

# Dashboard
print("\n📊 DASHBOARD")
r = api('GET', '/api/metrics')
check("Métricas reales", r is not None and r.json().get('productos', 0) >= 13)

r = api('GET', '/api/metrics')
check("Top producto", r is not None and r.json().get('top_producto') is not None)

# Reportes
print("\n📋 REPORTES")
r = api('GET', '/api/reportes/resumen')
check("Resumen", r is not None and 'resumen' in r.json())

r = api('GET', '/api/reportes/exportar')
check("Exportar CSV", r is not None and 'Fecha' in r.text)

# Agente IA
print("\n🧠 AGENTE IA")
r = api('POST', '/api/agent/chat', json={'mensaje':'Hola','rol':'desarrollador'})
check("Chat responde", r is not None and 'respuesta' in r.json())

r = api('POST', '/api/agent/chat', json={'mensaje':'recomiendame','rol':'desarrollador'})
check("Recomendaciones", r is not None and len(r.json().get('respuesta','')) > 10)

r = api('POST', '/api/agent/chat', json={'mensaje':'inventario','rol':'administrador'})
check("Stock", r is not None and len(r.json().get('respuesta','')) > 10)

# Privilegios
print("\n🔑 PRIVILEGIOS")
r = api('GET', '/api/admin/privilegios')
check("Lista privilegios", r is not None and 'jerarquia' in r.json())

r = api('POST', '/api/admin/usuarios/crear', json={'username':'test_user2','password':'123','nombre':'Test2','rol':'vendedor'})
check("Crear usuario", r is not None and (r.json().get('ok') or r.status_code == 403))

# Herramientas IA
print("\n🔧 HERRAMIENTAS IA")
r = api('GET', '/api/tools/finanzas')
check("Finanzas tool", r is not None and r.json().get('ok'))

r = api('GET', '/api/tools/stock')
check("Stock tool", r is not None and r.json().get('ok'))

r = api('GET', '/api/tools/recomendar')
check("Recomendar tool", r is not None and r.json().get('ok'))

# Seguridad
print("\n🛡️ SEGURIDAD")
r = api('GET', '/api/seguridad/check')
check("Security check", r is not None and r.json().get('ok'))

# Resultado
print("\n" + "=" * 60)
pct = round(passed/total*100) if total > 0 else 0
print(f"✅ {passed} pasados | ❌ {failed} fallidos | 📊 {total} total")
print(f"🎯 {pct}% completado")
print("=" * 60)
