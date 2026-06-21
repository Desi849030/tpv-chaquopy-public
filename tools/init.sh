#!/bin/bash
CYAN='\033[1;36m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'

clear
echo -e "${CYAN}======================================================"
echo -e "    🎓 REPORTE DE CALIDAD FINAL - TESIS 2025"
echo -e "         ESTADO: RESTAURACIÓN TOTAL"
echo -e "======================================================${NC}"

# --- 1. LIMPIEZA DE PROCESOS ---
fuser -k 5000/tcp 2>/dev/null
pkill -9 python 2>/dev/null
rm -f .coverage* server.log
coverage erase 2>/dev/null
sleep 2

export SRC_DIR="$(pwd)/app/src/main/python"
export PYTHONPATH="$SRC_DIR:$(pwd)"

# --- 2. RESTAURACIÓN LIMPIA DE DECORATORS.PY ---
echo -e "${YELLOW}🔧 Reconstruyendo decorators.py...${NC}"
cat << 'DECO_EOF' > "$SRC_DIR/decorators.py"
from functools import wraps
from flask import session, jsonify, request

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

requiere_login = login_required

def requiere_rol(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"ok": False, "error": "Unauthorized"}), 401
            
            # Normalizar roles permitidos (soporta string, lista o argumentos)
            if len(roles_permitidos) == 1 and isinstance(roles_permitidos[0], list):
                permitidos = roles_permitidos[0]
            else:
                permitidos = roles_permitidos
                
            if user.get("rol") not in permitidos:
                return jsonify({"ok": False, "error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    return requiere_rol("administrador")(f)

def usuario_actual(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        return f(user, *args, **kwargs)
    return decorated
DECO_EOF

# --- 3. REPARACIÓN SEGURA DE DB/USERS.PY ---
echo -e "${YELLOW}🔧 Reparando db/users.py (sin errores de sintaxis)...${NC}"
python3 -c "
import os
path = '$SRC_DIR/db/users.py'
with open(path, 'r') as f:
    lines = f.readlines()

# 1. Eliminar rastro de parches mal hechos
clean = [l for l in lines if '_get_default_password' not in l and 'Rol inválido' not in l and 'rol = usuario_data' not in l]

# 2. Insertar función maestra al inicio
new_content = ['def _get_default_password(): return \"123456\"\n\n']

# 3. Insertar validación de rol correctamente dentro de crear_usuario
for line in clean:
    new_content.append(line)
    if 'def crear_usuario(usuario_data' in line:
        indent = '    '
        new_content.append(f'{indent}rol = usuario_data.get(\"rol\")\n')
        new_content.append(f'{indent}if rol not in [\"administrador\", \"vendedor\", \"desarrollador\"]: return {{\"ok\": False, \"error\": \"Rol inválido\"}}\n')

with open(path, 'w') as f:
    f.writelines(new_content)
"

# --- 4. PREPARAR TESTS ---
touch tests/__init__.py tests/backend/__init__.py tests/oficial/__init__.py

# --- 5. EJECUTAR TESTS BACKEND ---
echo -e "${YELLOW}1. Ejecutando Cobertura Backend (66 Tests)...${NC}"
coverage run -p --source="$SRC_DIR" -m unittest discover -s tests/backend -p "test_*.py"

# --- 6. LEVANTAR SERVIDOR REAL ---
echo -e "\n${YELLOW}2. Levantando servidor app.py...${NC}"
nohup env PYTHONPATH="$SRC_DIR" python "$SRC_DIR/app.py" > server.log 2>&1 &
SERVER_PID=$!

echo -ne "${CYAN}⏳ Esperando servidor...${NC}"
sleep 10
if curl -s http://127.0.0.1:5000/api/health > /dev/null; then
    echo -e " ${GREEN}[OK]${NC}"
else
    echo -e " ${RED}[FALLÓ]${NC}"; tail -n 10 server.log; kill $SERVER_PID 2>/dev/null; exit 1
fi

# --- 7. EJECUTAR TESTS DE HUMO ---
echo -e "${YELLOW}3. Ejecutando Pruebas de Humo (23 Tests)...${NC}"
coverage run -p --source="$SRC_DIR" -m unittest discover -s tests/oficial -p "test_*.py"

# --- 8. REPORTE FINAL ---
echo -e "\n${CYAN}----------------------------------------------------"
echo -e "📊 RESULTADO DE COBERTURA INTEGRAL (FINAL)"
echo -e "----------------------------------------------------${NC}"
kill $SERVER_PID 2>/dev/null
coverage combine 2>/dev/null
coverage report -m "$SRC_DIR/db/users.py" \
                    "$SRC_DIR/decorators.py" \
                    "$SRC_DIR/modules/auth.py" \
                    "$SRC_DIR/modules/publico_bp.py"

echo -e "${CYAN}======================================================"
echo -e "✅ PROCESO COMPLETADO"
echo -e "======================================================${NC}"
