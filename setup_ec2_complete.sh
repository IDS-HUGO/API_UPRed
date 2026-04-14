#!/bin/bash

# 🚀 Setup completo Firebase + Configuración - EC2 UPRed
# Ejecutar en tu máquina LOCAL: bash setup_ec2_complete.sh TU_IP_EC2

if [ -z "$1" ]; then
    echo "❌ Uso: bash setup_ec2_complete.sh IP_DE_TU_EC2"
    echo "Ejemplo: bash setup_ec2_complete.sh 172.31.16.59"
    exit 1
fi

EC2_IP="$1"
EC2_USER="ubuntu"
KEY_FILE="/opt/upred/ws/apiupred.pem"  # Ajusta según tu setup

echo "=========================================="
echo "🚀 Setup Completo EC2 - UPRed Push"
echo "=========================================="
echo "EC2 IP: $EC2_IP"
echo "Usuario: $EC2_USER"
echo "Key: $KEY_FILE"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================
# 1. Verificar archivos locales
# ============================================================
echo -e "${BLUE}[1/5] Verificando archivos locales...${NC}"

if [ ! -f "firebase-service-account.json" ]; then
    echo -e "${RED}❌ firebase-service-account.json no encontrado en directorio actual${NC}"
    echo -e "${YELLOW}💡 Asegúrate de tener el archivo descargado de Firebase Console${NC}"
    exit 1
else
    echo -e "${GREEN}✅ firebase-service-account.json encontrado${NC}"
fi

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env no encontrado${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env encontrado${NC}"
fi

# Verificar conectividad SSH
echo -e "\n${BLUE}[2/5] Verificando conexión SSH...${NC}"
if ssh -o ConnectTimeout=10 -i "$KEY_FILE" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "echo 'SSH OK'" 2>/dev/null; then
    echo -e "${GREEN}✅ Conexión SSH exitosa${NC}"
else
    echo -e "${RED}❌ No se puede conectar via SSH${NC}"
    echo -e "${YELLOW}💡 Verifica: IP, usuario, archivo .pem${NC}"
    exit 1
fi

# ============================================================
# 2. Subir archivos a EC2
# ============================================================
echo -e "\n${BLUE}[3/5] Subiendo archivos a EC2...${NC}"

# Crear directorio en EC2
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "mkdir -p /opt/upred"

# Subir Firebase JSON
echo "Subiendo firebase-service-account.json..."
if scp -i "$KEY_FILE" "firebase-service-account.json" "$EC2_USER@$EC2_IP:/opt/upred/firebase-service-account.json"; then
    echo -e "${GREEN}✅ Firebase JSON subido${NC}"
else
    echo -e "${RED}❌ Error subiendo Firebase JSON${NC}"
    exit 1
fi

# Subir .env
echo "Subiendo .env..."
if scp -i "$KEY_FILE" ".env" "$EC2_USER@$EC2_IP:/opt/upred/ws/.env"; then
    echo -e "${GREEN}✅ .env subido${NC}"
else
    echo -e "${RED}❌ Error subiendo .env${NC}"
    exit 1
fi

# Subir scripts de diagnóstico
echo "Subiendo scripts de diagnóstico..."
scp -i "$KEY_FILE" "ec2_diagnose_fixed.sh" "$EC2_USER@$EC2_IP:/opt/upred/ec2_diagnose_fixed.sh" 2>/dev/null || true
scp -i "$KEY_FILE" "ec2_diagnose.py" "$EC2_USER@$EC2_IP:/opt/upred/ec2_diagnose.py" 2>/dev/null || true
scp -i "$KEY_FILE" "debug_seguir.py" "$EC2_USER@$EC2_IP:/opt/upred/debug_seguir.py" 2>/dev/null || true

# ============================================================
# 3. Configurar en EC2
# ============================================================
echo -e "\n${BLUE}[4/5] Configurando en EC2...${NC}"

# Configurar .env en EC2
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "
    # Actualizar .env con ruta correcta de Firebase
    sed -i 's|FIREBASE_SERVICE_ACCOUNT_PATH=.*|FIREBASE_SERVICE_ACCOUNT_PATH=/opt/upred/firebase-service-account.json|' /opt/upred/ws/.env
    
    # Verificar configuración
    echo 'Configuración .env:'
    grep -E '(FIREBASE|DB_)' /opt/upred/ws/.env
    
    # Hacer ejecutables los scripts
    chmod +x /opt/upred/ec2_diagnose_fixed.sh 2>/dev/null || true
    
    # Verificar Firebase JSON
    if [ -f /opt/upred/firebase-service-account.json ]; then
        echo '✅ Firebase JSON existe'
        python3 -c \"import json; print('Proyecto:', json.load(open('/opt/upred/firebase-service-account.json')).get('project_id'))\" 2>/dev/null || echo '❌ Error leyendo JSON'
    else
        echo '❌ Firebase JSON no encontrado'
    fi
"

# ============================================================
# 4. Ejecutar diagnóstico en EC2
# ============================================================
echo -e "\n${BLUE}[5/5] Ejecutando diagnóstico en EC2...${NC}"

# Ejecutar diagnóstico remotamente
DIAGNOSIS=$(ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "
    cd /opt/upred
    if [ -f ec2_diagnose_fixed.sh ]; then
        bash ec2_diagnose_fixed.sh
    else
        echo '❌ Script de diagnóstico no encontrado'
        echo 'Ejecuta manualmente:'
        echo '  curl -s https://raw.githubusercontent.com/tu-repo/ec2_diagnose_fixed.sh | bash'
    fi
" 2>&1)

echo "$DIAGNOSIS"

# ============================================================
# 5. Instrucciones finales
# ============================================================
echo -e "\n${GREEN}=========================================="
echo "✅ Setup Completado"
echo "==========================================${NC}"

echo -e "\n${BLUE}Estado:${NC}"
echo "• ✅ Firebase JSON subido y configurado"
echo "• ✅ .env actualizado"
echo "• ✅ Scripts de diagnóstico disponibles"

echo -e "\n${BLUE}Próximos pasos en EC2:${NC}"
echo "1. Si la API no está corriendo:"
echo -e "   ${YELLOW}cd /opt/upred/ws${NC}"
echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
echo -e "   ${YELLOW}python -u app.py${NC}"
echo ""
echo "2. Verificar estado:"
echo -e "   ${YELLOW}curl http://localhost:8000/api/notificaciones/push/status${NC}"
echo ""
echo "3. Test push (con JWT token):"
echo -e "   ${YELLOW}curl -X POST http://localhost:8000/api/notificaciones/push/test -H \"Authorization: Bearer TOKEN\"${NC}"

echo -e "\n${BLUE}Problema principal identificado:${NC}"
echo "❌ La app móvil NO registra dispositivos después de login"
echo "💡 Implementa POST /api/notificaciones/dispositivos en la app"

echo -e "\n${GREEN}¡Listo para probar notificaciones! 🚀${NC}"
