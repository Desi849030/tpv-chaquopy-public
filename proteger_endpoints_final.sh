#!/bin/bash
echo "Protegiendo endpoints finales..."

# 1. auth_routes.py
python3 << 'EOF'
with open('app/src/main/python/auth_routes.py', 'r') as f:
    content = f.read()
if 'from auth_decorator import' not in content:
    content = 'from auth_decorator import login_required, admin_required\n' + content
content = content.replace('@auth_bp.route("/api/auth/cambiar-password"', '@login_required\n@auth_bp.route("/api/auth/cambiar-password"')
content = content.replace('@auth_bp.route("/api/auth/auto-backup"', '@admin_required\n@auth_bp.route("/api/auth/auto-backup"')
with open('app/src/main/python/auth_routes.py', 'w') as f:
    f.write(content)
print("✅ auth_routes.py")
EOF

# 2. dictionary/routes.py
python3 << 'EOF'
with open('app/src/main/python/dictionary/routes.py', 'r') as f:
    content = f.read()
if 'from auth_decorator import' not in content:
    content = 'from auth_decorator import login_required\n' + content
for endpoint in ['sinonimos', 'definicion', 'corregir']:
    content = content.replace(f'@diccionario_bp.route("/api/diccionario/{endpoint}"', f'@login_required\n@diccionario_bp.route("/api/diccionario/{endpoint}"')
with open('app/src/main/python/dictionary/routes.py', 'w') as f:
    f.write(content)
print("✅ dictionary/routes.py")
EOF

# 3. i18n_routes.py
python3 << 'EOF'
with open('app/src/main/python/i18n_routes.py', 'r') as f:
    content = f.read()
if 'from auth_decorator import' not in content:
    content = 'from auth_decorator import login_required\n' + content
for endpoint in ['dict', 'translate', 'learn']:
    content = content.replace(f'@i18n_bp.route("/api/i18n/{endpoint}"', f'@login_required\n@i18n_bp.route("/api/i18n/{endpoint}"')
with open('app/src/main/python/i18n_routes.py', 'w') as f:
    f.write(content)
print("✅ i18n_routes.py")
EOF

# 4. license_routes.py
python3 << 'EOF'
with open('app/src/main/python/license_routes.py', 'r') as f:
    content = f.read()
if 'from auth_decorator import' not in content:
    content = 'from auth_decorator import login_required, admin_required\n' + content
for endpoint in ['activate', 'generate', 'deactivate', 'list']:
    content = content.replace(f"@lic_bp.route('/endpoint',", f"@admin_required\n@lic_bp.route('/{endpoint}',")
with open('app/src/main/python/license_routes.py', 'w') as f:
    f.write(content)
print("✅ license_routes.py")
EOF

# 5. security_routes.py
python3 << 'EOF'
with open('app/src/main/python/security_routes.py', 'r') as f:
    content = f.read()
if 'from auth_decorator import' not in content:
    content = 'from auth_decorator import login_required, admin_required\n' + content
import re
content = re.sub(r'(@security_bp\.route\()', '@admin_required\n\\1', content)
with open('app/src/main/python/security_routes.py', 'w') as f:
    f.write(content)
print("✅ security_routes.py")
EOF

# Verificación
echo ""
total=$(grep -rn "@.*_bp.route\|@app.route" app/src/main/python/ --include="*.py" | wc -l)
protegidos=$(grep -rn "@login_required\|@admin_required" app/src/main/python/ --include="*.py" | wc -l)
echo "Total: $total | Protegidos: $protegidos"
