#!/bin/bash

# 🚀 Auto-setup completo en EC2 - UPRed Push
# Ejecutar en EC2: bash auto_setup_ec2.sh

echo "=========================================="
echo "🚀 AUTO-SETUP EC2 - UPRed Push"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directorios
API_DIR="/opt/upred/ws"
REPO_DIR="/opt/upred/API_UPRed"

# ============================================================
# 1. Verificar y crear estructura
# ============================================================
echo -e "\n${BLUE}[1/6] Verificando estructura de directorios...${NC}"

mkdir -p /opt/upred
mkdir -p "$API_DIR"
mkdir -p "$REPO_DIR"

echo -e "${GREEN}✅ Directorios creados${NC}"

# ============================================================
# 2. Descargar archivos desde repo (si no existen)
# ============================================================
echo -e "\n${BLUE}[2/6] Descargando archivos de configuración...${NC}"

# Si no hay .env, intentar descargar
if [ ! -f "$API_DIR/.env" ]; then
    echo "Descargando .env..."
    curl -s https://raw.githubusercontent.com/tu-repo/.env -o "$API_DIR/.env" 2>/dev/null || echo "No se pudo descargar .env automáticamente"
fi

# Descargar scripts de diagnóstico
curl -s https://raw.githubusercontent.com/tu-repo/ec2_diagnose_fixed.sh -o /opt/upred/ec2_diagnose_fixed.sh 2>/dev/null
curl -s https://raw.githubusercontent.com/tu-repo/ec2_diagnose.py -o /opt/upred/ec2_diagnose.py 2>/dev/null
curl -s https://raw.githubusercontent.com/tu-repo/debug_seguir.py -o /opt/upred/debug_seguir.py 2>/dev/null

chmod +x /opt/upred/ec2_diagnose_fixed.sh 2>/dev/null

# ============================================================
# 3. Verificar Firebase JSON
# ============================================================
echo -e "\n${BLUE}[3/6] Verificando Firebase JSON...${NC}"

FIREBASE_PATHS=(
    "/opt/upred/firebase-service-account.json"
    "/home/ubuntu/firebase-service-account.json"
    "/opt/upred/ws/firebase-service-account.json"
)

FIREBASE_FOUND=false
for path in "${FIREBASE_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo -e "${GREEN}✅ Firebase JSON encontrado: $path${NC}"
        if python3 -c "import json; json.load(open('$path'))" 2>/dev/null; then
            PROJECT_ID=$(python3 -c "import json; print(json.load(open('$path')).get('project_id', 'unknown'))")
            echo -e "${GREEN}✅ JSON válido - Proyecto: $PROJECT_ID${NC}"
            FIREBASE_FOUND=true
            FIREBASE_PATH="$path"
            break
        else
            echo -e "${RED}❌ JSON inválido${NC}"
        fi
    fi
done

if [ "$FIREBASE_FOUND" = false ]; then
    echo -e "${RED}❌ Firebase JSON no encontrado${NC}"
    echo -e "${YELLOW}💡 INSTRUCCIONES PARA SUBIRLO:${NC}"
    echo ""
    echo -e "${BLUE}En tu máquina LOCAL, ejecuta:${NC}"
    echo "scp -i /opt/upred/ws/apiupred.pem firebase-service-account.json ubuntu@$EC2_IP:/opt/upred/"
    echo ""
    echo -e "${BLUE}O desde aquí:${NC}"
    echo "exit  # Sal de EC2"
    echo "scp firebase-service-account.json ubuntu@TU_IP_EC2:/opt/upred/"
    echo ""
    echo -e "${YELLOW}Luego vuelve a ejecutar este script${NC}"
    exit 1
fi

# ============================================================
# 4. Configurar .env
# ============================================================
echo -e "\n${BLUE}[4/6] Configurando .env...${NC}"

if [ ! -f "$API_DIR/.env" ]; then
    echo -e "${RED}❌ .env no encontrado en $API_DIR${NC}"
    echo -e "${YELLOW}Creando .env básico...${NC}"

    cat > "$API_DIR/.env" << EOF
# Database MySQL Configuration
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=root
DB_PASSWORD=
DB_NAME=upred_db

# JWT Configuration
SECRET_KEY=tu_clave_secreta_super_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CORS_ALLOWED_ORIGINS=*

# Firebase Admin SDK
FIREBASE_SERVICE_ACCOUNT_PATH=$FIREBASE_PATH

# Cloudinary (opcional)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
EOF

    echo -e "${GREEN}✅ .env creado${NC}"
else
    echo -e "${GREEN}✅ .env existe${NC}"

    # Actualizar FIREBASE_SERVICE_ACCOUNT_PATH
    sed -i "s|FIREBASE_SERVICE_ACCOUNT_PATH=.*|FIREBASE_SERVICE_ACCOUNT_PATH=$FIREBASE_PATH|" "$API_DIR/.env"
    echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH actualizado${NC}"
fi

# Verificar configuración
echo -e "${BLUE}Configuración actual:${NC}"
grep -E "(FIREBASE|DB_PORT)" "$API_DIR/.env"

# ============================================================
# 5. Verificar dependencias Python
# ============================================================
echo -e "\n${BLUE}[5/6] Verificando dependencias Python...${NC}"

cd "$API_DIR"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Instalar dependencias si requirements.txt existe
if [ -f "requirements.txt" ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt no encontrado${NC}"
fi

# Verificar firebase-admin
if python3 -c "import firebase_admin" 2>/dev/null; then
    echo -e "${GREEN}✅ firebase-admin instalado${NC}"
else
    echo -e "${YELLOW}Instalando firebase-admin...${NC}"
    pip install firebase-admin
fi

# Verificar mysql-connector
if python3 -c "import mysql.connector" 2>/dev/null; then
    echo -e "${GREEN}✅ mysql-connector instalado${NC}"
else
    echo -e "${YELLOW}Instalando mysql-connector-python...${NC}"
    pip install mysql-connector-python
fi

# ============================================================
# 6. Ejecutar diagnóstico final
# ============================================================
echo -e "\n${BLUE}[6/6] Ejecutando diagnóstico final...${NC}"

cd /opt/upred

if [ -f "ec2_diagnose_fixed.sh" ]; then
    echo -e "${GREEN}Ejecutando diagnóstico completo...${NC}"
    bash ec2_diagnose_fixed.sh
else
    echo -e "${YELLOW}⚠️  Script de diagnóstico no encontrado${NC}"
    echo -e "${YELLOW}Verificación manual:${NC}"

    # Verificación básica
    if curl -s --max-time 5 http://localhost:8000/api/notificaciones/push/status > /tmp/api_test.json 2>/dev/null; then
        ENABLED=$(python3 -c "import json; print(json.load(open('/tmp/api_test.json')).get('firebase_push_enabled', False))" 2>/dev/null)
        if [ "$ENABLED" = "True" ]; then
            echo -e "${GREEN}✅ API corriendo y Firebase habilitado${NC}"
        else
            echo -e "${RED}❌ API corriendo pero Firebase deshabilitado${NC}"
        fi
    else
        echo -e "${RED}❌ API no responde${NC}"
    fi
fi

# ============================================================
# Instrucciones finales
# ============================================================
echo -e "\n${GREEN}=========================================="
echo "✅ AUTO-SETUP COMPLETADO"
echo "==========================================${NC}"

echo -e "\n${BLUE}Estado de configuración:${NC}"
echo "• ✅ Firebase JSON: $FIREBASE_PATH"
echo "• ✅ .env configurado"
echo "• ✅ Dependencias Python instaladas"

echo -e "\n${BLUE}Para iniciar la API:${NC}"
echo -e "${YELLOW}cd /opt/upred/ws${NC}"
echo -e "${YELLOW}source .venv/bin/activate${NC}"
echo -e "${YELLOW}python -u app.py${NC}"

echo -e "\n${BLUE}Para verificar:${NC}"
echo -e "${YELLOW}curl http://localhost:8000/api/notificaciones/push/status${NC}"

echo -e "\n${BLUE}PROBLEMA PRINCIPAL:${NC}"
echo -e "${RED}❌ La app móvil NO registra dispositivos${NC}"
echo -e "${YELLOW}💡 Implementa POST /api/notificaciones/dispositivos después de login${NC}"

echo -e "\n${GREEN}¡Setup completado! Ahora configura la app móvil 🚀${NC}"
