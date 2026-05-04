#!/bin/bash
echo "=========================================="
echo " TPV Ultra Smart - Aplicando correcciones"
echo "=========================================="

# FIX 1: biometric_auth.py
echo ""
echo ">>> FIX 1: biometric_auth.py"
sed -i 's/import hashlib, os, json, time/import hashlib, hmac, os, json, time/' app/src/main/python/biometric_auth.py
sed -i 's/raw = f"{user_id}:biometric:{salt.hex()}:{int(time.time())}"/raw = f"{user_id}:biometric:{salt.hex()}"/' app/src/main/python/biometric_auth.py
sed -i 's/raw = f"{user_id}:biometric:{stored_salt}:{int(time.time())}"/raw = f"{user_id}:biometric:{stored_salt}"/' app/src/main/python/biometric_auth.py
echo "[OK] biometric_auth.py"

# FIX 2: ia_assistant_routes.py - @requiere_login
echo ""
echo ">>> FIX 2: ia_assistant_routes.py"
sed -i 's/def chat():/@requiere_login\ndef chat():/' app/src/main/python/ia_assistant_routes.py
echo "[OK] ia_assistant_routes.py"

# FIX 3: app.py - _MODULOS_DISPONIBLES sin duplicados
echo ""
echo ">>> FIX 3: app.py - modulos"
python3 << 'PYEOF'
with open('app/src/main/python/app.py', 'r') as f:
    content = f.read()

old = '_MODULOS_DISPONIBLES = {'
new = '''_MODULOS_DISPONIBLES = {
    "catalogo":"Gestion de catalogo","ventas":"Registro de ventas","caja":"Caja y cobros",
    "dashboard":"Panel estadisticas","inventario":"Control inventario",
    "productos":"CRUD productos","categorias":"Gestion categorias",
    "orden":"Gestion de ordenes","tienda":"Tienda online","registros":"Historial",
    "herramientas":"Herramientas","configuracion":"Configuracion","usuarios":"Gestion usuarios",
    "licencias":"Gestion licencias","debug":"Panel depuracion","privilegios":"Gestion privilegios",
    "blindajes":"Panel blindajes","ia_edge":"IA Edge Analytics","lealtad":"Programa Lealtad",
    "asistente_ia":"Asistente IA","descuentos":"Descuentos","supabase":"Configuracion Supabase",
    "seguridad":"Seguridad","exportar":"Exportar datos","copias":"Copias de seguridad"
}'''

# Buscar el inicio del diccionario y reemplazar todo hasta el cierre
import re
pattern = r'_MODULOS_DISPONIBLES\s*=\s*\{.*?\}[,\s]*"catalogo":.*?"Asistente IA"\}'
match = re.search(pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new + content[match.end():]
    print("[OK] Modulos corregidos")
else:
    print("[AVISO] No se encontro duplicado - ya esta corregido")

with open('app/src/main/python/app.py', 'w') as f:
    f.write(content)
PYEOF

echo ""
echo "=========================================="
echo " CORRECCIONES APLICADAS"
echo "=========================================="
echo ""
echo "Ahora ejecuta:"
echo "  git add -A"
echo "  git commit -m 'fix: biometria + seguridad + modulos'"
echo "  git push"
