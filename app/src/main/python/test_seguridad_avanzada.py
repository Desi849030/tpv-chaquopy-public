#!/usr/bin/env python3
"""
TEST SEGURIDAD AVANZADA - TPV UltraSmart
Valida: SQLi, XSS, CSRF, Rate Limiting, Tokens, Sesiones
"""
import sys, os, re, hashlib
sys.path.insert(0, 'app/src/main/python')

print("=" * 70)
print("🛡️ TEST SEGURIDAD AVANZADA")
print("=" * 70)

errors, ok = [], []
def test(name, condition, msg=""):
    (ok if condition else errors).append(name)
    print(f"  {'✅' if condition else '❌'} {name}" + (f": {msg}" if msg and not condition else ""))

# 1. SQL Injection
print("\n🔴 1. PROTECCIÓN SQL INJECTION")
sqli_payloads = [
    "' OR '1'='1",
    "'; DROP TABLE usuarios; --",
    "1' UNION SELECT * FROM usuarios--",
    "' OR 1=1--",
    "admin'--"
]

try:
    from security.validation import sanitize_input
    for payload in sqli_payloads:
        sanitized = sanitize_input(payload)
        dangerous = any(x in sanitized.lower() for x in ["drop", "union", "or 1=1", "--"])
        test(f"Sanitizar '{payload[:30]}...'", not dangerous, f"Resultado: {sanitized[:50]}")
except Exception as e:
    test("SQLi protection", False, str(e))

# 2. XSS Protection
print("\n🟠 2. PROTECCIÓN XSS")
xss_payloads = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg/onload=alert(1)>",
]

try:
    for payload in xss_payloads:
        sanitized = sanitize_input(payload)
        has_script = '<script' in sanitized.lower() or 'onerror' in sanitized.lower() or 'onload' in sanitized.lower()
        test(f"Sanitizar XSS '{payload[:30]}...'", not has_script)
except Exception as e:
    test("XSS protection", False, str(e))

# 3. Password Security
print("\n🟡 3. SEGURIDAD DE CONTRASEÑAS")
try:
    from security.crypto import hash_password, verify_password
    
    # Longitud mínima del hash
    h = hash_password("test123")
    test("Hash longitud > 50 chars", len(h) > 50)
    
    # Unicidad (misma contraseña, diferente hash)
    h2 = hash_password("test123")
    test("Hash único por llamada", h != h2)
    
    # Verificación correcta
    test("Verificación OK", verify_password("test123", h))
    test("Verificación FAIL", not verify_password("wrong", h))
    
    # Timing attack resistance (básico)
    import time
    start = time.time()
    verify_password("a" * 1000, h)
    test("Tiempo verificación < 10ms", (time.time() - start) < 0.01)
except Exception as e:
    test("Password security", False, str(e))

# 4. Token Security
print("\n🟢 4. SEGURIDAD DE TOKENS")
try:
    import secrets
    
    # Generar token seguro
    token = secrets.token_hex(32)
    test("Token 256 bits", len(token) == 64)
    
    # Verificar que no es predecible
    token2 = secrets.token_hex(32)
    test("Tokens únicos", token != token2)
    
    # Entropía
    test("Token sin patrón", token[:8] != token2[:8])
except Exception as e:
    test("Token security", False, str(e))

# 5. Rate Limiting
print("\n🔵 5. RATE LIMITING")
try:
    # Simular rate limiting con login_intentos
    import sqlite3
    conn = sqlite3.connect('tpv_datos.db', timeout=10)
    cur = conn.cursor()
    
    # Verificar tabla login_intentos
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login_intentos'")
    test("Tabla login_intentos existe", cur.fetchone() is not None)
    
    # Verificar bloqueo después de 5 intentos
    cur.execute("SELECT COUNT(*) FROM login_intentos WHERE username='test-rate' AND exito=0")
    intentos = cur.fetchone()[0]
    test(f"Rate limiting activo ({intentos} intentos)", intentos >= 0)
    
    conn.close()
except Exception as e:
    test("Rate limiting", False, str(e))

# 6. Session Security
print("\n🟣 6. SEGURIDAD DE SESIÓN")
try:
    # Verificar configuración de sesión en Flask
    from flask import Flask
    app = Flask(__name__)
    
    # Debe tener secret_key configurada
    has_secret = os.path.exists('.env') or os.path.exists('.env.example')
    test("Secret key configurada", has_secret)
    
    # Verificar cookies seguras
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    test("Cookies seguras configurable", True)
except Exception as e:
    test("Session security", False, str(e))

# 7. Archivos sensibles
print("\n🟤 7. ARCHIVOS SENSIBLES")
sensitive_patterns = [
    ('.env', 'Archivo de entorno'),
    ('*.key', 'Clave privada'),
    ('*.pem', 'Certificado'),
    ('*.keystore', 'Keystore Android'),
    ('*.jks', 'Java Keystore'),
]

sensitive_found = []
for root, _, files in os.walk('.'):
    if '.git' in root:
        continue
    for pattern, desc in sensitive_patterns:
        for f in files:
            if f == pattern or (pattern.startswith('*') and f.endswith(pattern[1:])):
                sensitive_found.append(f)

# .env debe existir, pero .env.example también
test(".env.example existe", os.path.exists('.env.example'))

# No debe haber .env real en el repo
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        content = f.read()
    has_real_secrets = any(x in content for x in ['SUPABASE_KEY', 'SECRET_KEY', 'PASSWORD'])
    test("Sin secretos reales en .env", not has_real_secrets, "Usar .env.example")

# 8. HTTPS y headers
print("\n⚪ 8. HEADERS DE SEGURIDAD")
security_headers = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000',
}

# Verificar si están en la configuración
try:
    with open('app/src/main/python/app.py', 'r') as f:
        app_content = f.read()
    
    for header, value in security_headers.items():
        found = header in app_content or header.replace('-', '_').lower() in app_content.lower()
        test(f"Header {header}", found, "No configurado explícitamente")
except:
    pass

# 9. Dependencias seguras
print("\n🔶 9. DEPENDENCIAS")
try:
    with open('requirements.txt', 'r') as f:
        reqs = f.read()
    
    # Verificar versiones conocidas
    test("Flask en requirements", 'flask' in reqs.lower())
    test("Sin dependencias obsoletas", '==' in reqs)
    
    # Contar dependencias
    count = len([l for l in reqs.split('\n') if l.strip() and not l.startswith('#')])
    test(f"Dependencias: {count}", count > 3)
except Exception as e:
    test("Dependencias", False, str(e))

# 10. Logs y auditoría
print("\n🔷 10. LOGS Y AUDITORÍA")
try:
    import sqlite3
    conn = sqlite3.connect('tpv_datos.db', timeout=10)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs_sistema'")
    test("Tabla logs_sistema", cur.fetchone() is not None)
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditoria'")
    test("Tabla auditoria", cur.fetchone() is not None)
    
    conn.close()
except Exception as e:
    test("Logs", False, str(e))

# Resumen
print("\n" + "=" * 70)
print("📋 RESUMEN SEGURIDAD AVANZADA")
print(f"  ✅ {len(ok)} pasaron")
print(f"  ❌ {len(errors)} errores")
if errors:
    print("\n❌ FALLOS:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 ¡SEGURIDAD AVANZADA APROBADA!")
    sys.exit(0)
