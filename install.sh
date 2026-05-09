#!/bin/bash
# ═══════════════════════════════════════════════════════
#  TPV Ultra Smart - Script de instalación para Termux
# ═══════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   TPV Ultra Smart - Instalación Termux      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1) Actualizar paquetes
echo "[1/6] Actualizando paquetes..."
pkg update -y && pkg upgrade -y

# 2) Instalar dependencias del sistema
echo "[2/6] Instalando Python y herramientas..."
pkg install -y python git

# 3) Crear entorno virtual
echo "[3/6] Creando entorno virtual..."
python -m venv venv
source venv/bin/activate

# 4) Instalar dependencias Python
echo "[4/6] Instalando dependencias Python..."
pip install --upgrade pip
pip install flask==3.0.3 werkzeug==3.0.3 jinja2==3.1.4 markupsafe==2.1.5 itsdangerous==2.1.2 click==8.1.7

# 5) Directorio del proyecto
echo "[5/6] Verificando estructura..."
cd app/src/main/python/
mkdir -p ia
touch ia/__init__.py

# 6) Generar clave secreta si no existe
echo "[6/6] Configurando seguridad..."
if [ ! -f .tpv_secret_key ]; then
    python -c "import os; open('.tpv_secret_key','w').write(os.urandom(32).hex())"
fi

echo ""
echo "✅ Instalación completa."
echo ""
echo "Para iniciar el servidor:"
echo "  source venv/bin/activate"
echo "  cd app/src/main/python/"
echo "  python start_server.py"
echo ""
echo "Abrir en navegador: http://127.0.0.1:5050"
echo "Credenciales configuradas (ver .env.example)"
echo ""
