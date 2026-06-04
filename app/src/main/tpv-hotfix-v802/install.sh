#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# TPV Ultra Smart v8.0.2 — Instalador de Hotfix
# ═══════════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  TPV Ultra Smart v8.0.2 — Instalador de Hotfix${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# ── Detectar directorio del proyecto ──
TPV_DIR=""
if [ -d "$HOME/tpv-chaquopy/app/src/main/assets/frontend" ]; then
    TPV_DIR="$HOME/tpv-chaquopy/app/src/main"
elif [ -d "$HOME/tpv/app/src/main/assets/frontend" ]; then
    TPV_DIR="$HOME/tpv/app/src/main"
else
    # Buscar en ubicaciones comunes de Termux
    for d in "$HOME"/tpv*/app/src/main "$HOME"/*/tpv*/app/src/main; do
        if [ -d "$d/assets/frontend" ]; then
            TPV_DIR="$d"
            break
        fi
    done
fi

if [ -z "$TPV_DIR" ]; then
    echo -e "${RED}❌ No se encontró el directorio del TPV.${NC}"
    echo -e "${YELLOW}Especifica la ruta manualmente:${NC}"
    echo "  export TPV_DIR=/ruta/a/tpv-chaquopy/app/src/main"
    echo "  cd \$TPV_DIR && python3 hotfix_v802.py"
    exit 1
fi

echo -e "${GREEN}📁 TPV encontrado en: $TPV_DIR${NC}"
echo ""

# ── Copiar hotfix al directorio del proyecto ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/hotfix_v802.py" "$TPV_DIR/hotfix_v802.py" 2>/dev/null || true

echo -e "${YELLOW}Ejecutando hotfix...${NC}"
cd "$TPV_DIR"
python3 hotfix_v802.py

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Hotfix instalado correctamente${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📌 Pasos siguientes:${NC}"
echo "  1. Detener el servidor actual (Ctrl+C si está corriendo)"
echo "  2. Reiniciar: cd $TPV_DIR/python && python3 app.py"
echo "  3. Abrir: http://127.0.0.1:5050"
echo "  4. Recargar sin cache: Ctrl+Shift+R en el navegador"
echo ""
echo -e "${YELLOW}Para subir a GitHub:${NC}"
echo "  cd $TPV_DIR/../..  # raiz del repo"
echo "  git add -A"
echo "  git commit -m 'Hotfix v8.0.2: funciones criticas, emoji, endpoints, BD init'"
echo "  git push origin main"
