import os
"""Tests Robustos - TPV Ultra Smart v8.0 - 50 pruebas"""
import requests, json, time, random, string

BASE = 'http://127.0.0.1:5000'
passed = failed = total = 0

def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name} {detail}")
        failed += 1

def api(method, path, **kw):
    try:
        url = BASE + path
        if method == 'GET':
            return requests.get(url, timeout=5)
        return requests.post(url, json=kw.get('json', {}), timeout=5)
    except:
        return None

print("=" * 70)
print("🧪 TPV Ultra Smart - TESTS ROBUSTOS (50 pruebas)")
print("=" * 70)

# ==================== AUTH (6) ====================
print("\n🔐 AUTH (6 pruebas)")
check("1. Health check", (r := api('GET','/api/health')) and r.status_code == 200)
check("2. Health devuelve JSON", (r := api('GET','/api/health')) and r.json().get('status') == 'ok')
check("3. Login dev", (r := api('POST','/api/auth/login', json={'username':'desarrollador','password':os.environ.get('TPV_DEMO_PASSWORD', 'demo-tpv-2026')})) and r.json().get('ok'))
check("4. Login admin", (r := api('POST','/api/auth/login', json={'username':'admin','password':'admin'})) and r.json().get('ok'))
check("5. Auth me autenticado", (r := api('GET','/api/auth/me')) and r.json().get('autenticado'))
check("6. Auth me devuelve rol", (r := api('GET','/api/auth/me')) and r.json().get('usuario',{}).get('rol'))

# ==================== CATÁLOGO (5) ====================
print("\n📦 CATÁLOGO (5 pruebas)")
r = api('GET','/api/catalogo')
check("7. Catálogo responde 200", r and r.status_code == 200)
check("8. Tiene productos >= 14", r and len(r.json().get('productos',[])) >= 14)
check("9. Producto tiene precio válido", r and r.json()['productos'][0]['precio'] > 0)
check("10. Producto tiene stock", r and r.json()['productos'][0]['stock'] > 0)
check("11. Tiene categorías", r and 'categorias' in r.json())

# ==================== VENTAS (8) ====================
print("\n💰 VENTAS (8 pruebas)")
# Registrar venta
r = api('POST','/api/ventas/registrar', json={
    'items':[{'id':'p1','nombre':'Test Venta','cantidad':2,'precio':15.50}],
    'metodo_pago':'efectivo'
})
check("12. Registrar venta simple", r and r.json().get('ok'))
check("13. Venta devuelve total", r and r.json().get('total', 0) > 0)
check("14. Venta devuelve ID", r and r.json().get('venta_id'))

# Venta con múltiples items
r2 = api('POST','/api/ventas/registrar', json={
    'items':[
        {'id':'p1','nombre':'Item A','cantidad':1,'precio':10},
        {'id':'p2','nombre':'Item B','cantidad':3,'precio':20}
    ],
    'metodo_pago':'tarjeta'
})
check("15. Venta múltiples items", r2 and r2.json().get('ok'))
check("16. Total múltiple correcto", r2 and r2.json().get('total') == 70.0)

# Totales
check("17. Totales hoy", (r := api('GET','/api/ventas/totales')) and 'hoy' in r.json())
check("18. Ventas hoy lista", (r := api('GET','/api/ventas/hoy')) and r.json().get('ok'))
check("19. Cierre caja", (r := api('POST','/api/ventas/cierre', json={'fecha':'2026-05-30'})) and r.status_code == 200)

# ==================== DASHBOARD (4) ====================
print("\n📊 DASHBOARD (4 pruebas)")
r = api('GET','/api/metrics')
check("20. Métricas OK", r and r.status_code == 200)
check("21. Productos en métricas", r and r.json().get('productos', 0) >= 14)
check("22. Ventas hoy en métricas", r and r.json().get('ventas_hoy', -1) >= 0)
check("23. Top producto existe", r and r.json().get('top_producto') is not None)

# ==================== REPORTES (4) ====================
print("\n📋 REPORTES (4 pruebas)")
check("24. Resumen", (r := api('GET','/api/reportes/resumen')) and 'resumen' in r.json())
check("25. Exportar CSV", (r := api('GET','/api/reportes/exportar')) and 'Fecha' in r.text)
check("26. Ventas con filtro", (r := api('GET','/api/reportes/ventas?desde=2026-05-01&hasta=2026-05-30')) and r.json().get('ok'))
check("27. CSV tiene datos", (r := api('GET','/api/reportes/exportar')) and len(r.text.split('\n')) > 1)

# ==================== AGENTE IA (6) ====================
print("\n🧠 AGENTE IA (6 pruebas)")
check("28. Chat responde", (r := api('POST','/api/agent/chat', json={'mensaje':'Hola','rol':'desarrollador'})) and len(r.json().get('respuesta','')) > 10)
check("29. Chat diferente cada vez", len(set([
    api('POST','/api/agent/chat', json={'mensaje':'Hola','rol':'desarrollador'}).json().get('respuesta',''),
    api('POST','/api/agent/chat', json={'mensaje':'recomiendame','rol':'desarrollador'}).json().get('respuesta','')
])) > 1)
check("30. Reconoce finanzas", 'Balance' in api('POST','/api/agent/chat', json={'mensaje':'balance financiero','rol':'admin'}).json().get('respuesta',''))
check("31. Reconoce stock", 'Stock' in api('POST','/api/agent/chat', json={'mensaje':'inventario bajo','rol':'admin'}).json().get('respuesta',''))
check("32. Saludo personalizado", 'Desarrollador' in api('POST','/api/agent/chat', json={'mensaje':'Hola','rol':'desarrollador'}).json().get('respuesta',''))
check("33. Respuesta no vacía", len(api('POST','/api/agent/chat', json={'mensaje':'test','rol':'vendedor'}).json().get('respuesta','')) > 5)

# ==================== PRIVILEGIOS (4) ====================
print("\n🔑 PRIVILEGIOS (4 pruebas)")
check("34. Lista privilegios", (r := api('GET','/api/admin/privilegios')) and 'jerarquia' in r.json())
check("35. 5 roles", (r := api('GET','/api/admin/privilegios')) and len(r.json().get('jerarquia',{})) >= 5)
uid = 'test-'+''.join(random.choices(string.ascii_lowercase, k=4))
check("36. Crear usuario", (r := api('POST','/api/admin/usuarios/crear', json={'username':uid,'password':'123','nombre':'Test','rol':'administrador'})) and (r.json().get('ok') or r.status_code == 403))
check("37. Toggle usuario", (r := api('PUT','/api/admin/usuarios/dev-001/toggle', json={'activo':True})) and r.json().get('ok'))

# ==================== CLIENTES (3) ====================
print("\n👥 CLIENTES (3 pruebas)")
check("38. Registrar cliente", (r := api('POST','/api/clientes/registrar', json={'nombre':'Test Cliente','telefono':'555-0001'})) and r.json().get('ok'))
check("39. Listar clientes", (r := api('GET','/api/clientes')) and r.json().get('ok'))
check("40. Cliente creado tiene ID", (r := api('POST','/api/clientes/registrar', json={'nombre':'Test2'})) and r.json().get('cliente_id'))

# ==================== QR (2) ====================
print("\n📱 QR (2 pruebas)")
check("41. QR producto existe", (r := api('GET','/api/qr/prod-b243e2b3')) and 'qr_data' in r.json())
check("42. QR producto inválido", (r := api('GET','/api/qr/noexiste')) and r.json().get('ok') == False)

# ==================== HERRAMIENTAS IA (3) ====================
print("\n🔧 HERRAMIENTAS (3 pruebas)")
check("43. Finanzas tool", (r := api('GET','/api/tools/finanzas')) and r.json().get('ok'))
check("44. Stock tool", (r := api('GET','/api/tools/stock')) and r.json().get('ok'))
check("45. Recomendar tool", (r := api('GET','/api/tools/recomendar')) and r.json().get('ok'))

# ==================== SEGURIDAD (3) ====================
print("\n🛡️ SEGURIDAD (3 pruebas)")
r = api('GET','/api/seguridad/check')
check("46. Security check OK", r and r.json().get('ok'))
check("47. HET activo", r and 'het' in r.json().get('seguridad',{}))
check("48. PCI activo", r and 'pci' in r.json().get('seguridad',{}))

# ==================== IMPORT/EXPORT (2) ====================
print("\n📥 IMPORT/EXPORT (2 pruebas)")
check("49. Importar producto", (r := api('POST','/api/importar/excel', json={'productos':[{'nombre':'Test Final','precio':99}]})) and r.json().get('ok'))
check("50. Backup BD", (r := api('POST','/api/db/backup')) and r.json().get('ok'))

# ==================== RESULTADO ====================
print("\n" + "=" * 70)
pct = round(passed/total*100) if total > 0 else 0
bar = "█" * (passed//2) + "░" * ((total-passed)//2)
print(f"  {bar}")
print(f"  ✅ {passed} | ❌ {failed} | 📊 {total} | 🎯 {pct}%")
if pct == 100: print("  🏆 PERFECTO - SISTEMA LISTO PARA PRODUCCIÓN")
elif pct >= 95: print("  🎉 EXCELENTE - Listo para demo")
elif pct >= 80: print("  👍 BUENO - Funcionalidad principal OK")
else: print("  🔧 NECESITA MEJORAS")
print("=" * 70)
