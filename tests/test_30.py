"""30 Tests - TPV Ultra Smart v8.0"""
import requests, json

BASE = 'http://127.0.0.1:5000'
passed = failed = total = 0

def check(name, condition):
    global passed, failed, total
    total += 1
    if condition:
        print(f"  ✅ {name}"); passed += 1
    else:
        print(f"  ❌ {name}"); failed += 1

def api(method, path, **kw):
    try:
        url = BASE + path
        if method == 'GET': return requests.get(url, timeout=5)
        return requests.post(url, json=kw.get('json', {}), timeout=5)
    except: return None

print("=" * 60)
print("🧪 TPV Ultra Smart - 30 Tests")
print("=" * 60)

# Auth (4)
print("\n🔐 AUTH")
check("1. Health", api('GET','/api/health') and api('GET','/api/health').status_code == 200)
check("2. Login dev", api('POST','/api/auth/login', json={'username':'desarrollador','password':'123456'}).json().get('ok'))
check("3. Login admin", api('POST','/api/auth/login', json={'username':'admin','password':'admin'}).json().get('ok'))
check("4. Auth me", 'usuario' in api('GET','/api/auth/me').json())

# Catálogo (3)
print("\n📦 CATÁLOGO")
r = api('GET','/api/catalogo')
check("5. Tiene productos", r and len(r.json().get('productos',[])) >= 14)
check("6. Producto con precio", r and r.json()['productos'][0]['precio'] > 0)
check("7. Tiene categorías", r and 'categorias' in r.json())

# Ventas (4)
print("\n💰 VENTAS")
check("8. Registrar venta", api('POST','/api/ventas/registrar', json={'items':[{'id':'t1','nombre':'Test','cantidad':1,'precio':10}]}).json().get('ok'))
check("9. Totales", 'hoy' in api('GET','/api/ventas/totales').json())
check("10. Ventas hoy", api('GET','/api/ventas/hoy').json().get('ok'))
check("11. Cierre caja", api('POST','/api/ventas/cierre', json={'fecha':'2026-05-30'}).status_code == 200)

# Dashboard (3)
print("\n📊 DASHBOARD")
r = api('GET','/api/metrics')
check("12. Métricas", r and r.json().get('productos',0) >= 14)
check("13. Top producto", r and r.json().get('top_producto'))
check("14. Ganancia hoy", r and r.json().get('ganancia_hoy', 0) >= 0)

# Reportes (3)
print("\n📋 REPORTES")
check("15. Resumen", 'resumen' in api('GET','/api/reportes/resumen').json())
check("16. Exportar CSV", 'Fecha' in api('GET','/api/reportes/exportar').text)
check("17. Ventas con filtro", api('GET','/api/reportes/ventas?desde=2026-05-01&hasta=2026-05-30').json().get('ok'))

# Agente IA (3)
print("\n🧠 AGENTE IA")
check("18. Chat responde", len(api('POST','/api/agent/chat', json={'mensaje':'Hola','rol':'desarrollador'}).json().get('respuesta','')) > 10)
check("19. Finanzas", len(api('POST','/api/agent/chat', json={'mensaje':'balance financiero','rol':'admin'}).json().get('respuesta','')) > 10)
check("20. Recomendaciones", len(api('POST','/api/agent/chat', json={'mensaje':'recomiendame','rol':'desarrollador'}).json().get('respuesta','')) > 10)

# Clientes (2)
print("\n👥 CLIENTES")
check("21. Registrar cliente", api('POST','/api/clientes/registrar', json={'nombre':'Maria','telefono':'555'}).json().get('ok'))
check("22. Listar clientes", api('GET','/api/clientes').json().get('ok'))

# QR (1)
print("\n📱 QR")
check("23. Generar QR", 'qr_data' in api('GET','/api/qr/prod-b243e2b3').json())

# Notificaciones (1)
print("\n🔔 NOTIFICACIONES")
check("24. Notificaciones", api('GET','/api/notificaciones').json().get('ok'))

# Herramientas IA (3)
print("\n🔧 HERRAMIENTAS")
check("25. Finanzas tool", api('GET','/api/tools/finanzas').json().get('ok'))
check("26. Stock tool", api('GET','/api/tools/stock').json().get('ok'))
check("27. Recomendar tool", api('GET','/api/tools/recomendar').json().get('ok'))

# Seguridad (1)
print("\n🛡️ SEGURIDAD")
check("28. Security check", api('GET','/api/seguridad/check').json().get('ok'))

# Backup (1)
print("\n💾 BACKUP")
check("29. Backup BD", api('POST','/api/db/backup').json().get('ok'))

# Importar (1)
print("\n📥 IMPORTAR")
check("30. Importar Excel", api('POST','/api/importar/excel', json={'productos':[{'nombre':'Test30','precio':30}]}).json().get('ok'))

print("\n" + "=" * 60)
pct = round(passed/total*100) if total > 0 else 0
print(f"✅ {passed} | ❌ {failed} | 📊 {total} | 🎯 {pct}%")
print("=" * 60)
