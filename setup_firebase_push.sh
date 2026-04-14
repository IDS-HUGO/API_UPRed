#!/bin/bash

# 🚀 Script de Setup e Inicialización de Firebase Push - UPRed EC2
# Uso: bash setup_firebase_push.sh

set -e  # Exit on error

echo "=========================================="
echo "🚀 Setup Firebase Push - UPRed API"
echo "=========================================="

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
FIREBASE_JSON_PATH="${1:-.}"
API_DIR="/home/ec2-user/api"  # Cambiar según tu setup
ENV_FILE="$API_DIR/.env"

# ============================================================
# 1. Validar entrada
# ============================================================
echo -e "\n${BLUE}[1/5] Validando entrada...${NC}"

if [ -z "$FIREBASE_JSON_PATH" ] || [ "$FIREBASE_JSON_PATH" = "." ]; then
    echo -e "${YELLOW}ℹ️  Uso: bash setup_firebase_push.sh /ruta/a/firebase-service-account.json${NC}"
    echo -e "${YELLOW}ℹ️  Por ahora, buscaré el archivo en directorio actual${NC}"
    
    if ls firebase*.json 1> /dev/null 2>&1; then
        FIREBASE_JSON_PATH=$(ls firebase*.json | head -1)
        echo -e "${GREEN}✅ Encontrado: $FIREBASE_JSON_PATH${NC}"
    else
        echo -e "${RED}❌ No encontré archivo firebase*.json${NC}"
        exit 1
    fi
fi

if [ ! -f "$FIREBASE_JSON_PATH" ]; then
    echo -e "${RED}❌ Archivo no existe: $FIREBASE_JSON_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Archivo válido: $FIREBASE_JSON_PATH${NC}"

# ============================================================
# 2. Validar JSON
# ============================================================
echo -e "\n${BLUE}[2/5] Validando JSON de Firebase...${NC}"

if python3 -c "import json; json.load(open('$FIREBASE_JSON_PATH'))" 2>/dev/null; then
    echo -e "${GREEN}✅ JSON válido${NC}"
    
    PROJECT_ID=$(python3 -c "import json; print(json.load(open('$FIREBASE_JSON_PATH')).get('project_id', 'unknown'))")
    echo -e "${GREEN}  Proyecto: $PROJECT_ID${NC}"
else
    echo -e "${RED}❌ JSON inválido${NC}"
    exit 1
fi

# ============================================================
# 3. Copiar archivo a ubicación segura
# ============================================================
echo -e "\n${BLUE}[3/5] Copiando credenciales a ~/firebase-service-account.json...${NC}"

TARGET="/home/ec2-user/firebase-service-account.json"

if [ -f "$TARGET" ]; then
    echo -e "${YELLOW}⚠️  Archivo ya existe. Haciendo backup...${NC}"
    mv "$TARGET" "${TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
fi

cp "$FIREBASE_JSON_PATH" "$TARGET"
chmod 600 "$TARGET"  # Solo lectura para propietario

echo -e "${GREEN}✅ Archivo copiado a: $TARGET${NC}"
echo -e "${GREEN}✅ Permisos establecidos: 600${NC}"

# ============================================================
# 4. Actualizar .env
# ============================================================
echo -e "\n${BLUE}[4/5] Actualizando archivo .env...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env no existe en $API_DIR${NC}"
    echo -e "${YELLOW}   Buscaré el archivo .env...${NC}"
    
    ENV_FILE=$(find /home/ec2-user -name ".env" -type f 2>/dev/null | head -1)
    
    if [ -z "$ENV_FILE" ]; then
        echo -e "${RED}❌ No encontré archivo .env${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Encontrado: $ENV_FILE${NC}"
fi

# Backup .env
echo -e "${YELLOW}ℹ️  Haciendo backup de .env...${NC}"
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Actualizar o agegar FIREBASE_SERVICE_ACCOUNT_PATH
if grep -q "FIREBASE_SERVICE_ACCOUNT_PATH" "$ENV_FILE"; then
    # Ya existe, actualizar
    sed -i "s|^FIREBASE_SERVICE_ACCOUNT_PATH=.*|FIREBASE_SERVICE_ACCOUNT_PATH=$TARGET|" "$ENV_FILE"
    echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH actualizado${NC}"
else
    # No existe, agregar
    echo "FIREBASE_SERVICE_ACCOUNT_PATH=$TARGET" >> "$ENV_FILE"
    echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH agregado${NC}"
fi

# ============================================================
# 5. Verificación Final
# ============================================================
echo -e "\n${BLUE}[5/5] Verificación final...${NC}"

if grep "FIREBASE_SERVICE_ACCOUNT_PATH=$TARGET" "$ENV_FILE" > /dev/null; then
    echo -e "${GREEN}✅ .env actualizado correctamente${NC}"
else
    echo -e "${RED}❌ .env no se actualizó correctamente${NC}"
    exit 1
fi

if [ -f "$TARGET" ]; then
    echo -e "${GREEN}✅ Archivo de credenciales en lugar correcto${NC}"
else
    echo -e "${RED}❌ Archivo de credenciales no está en $TARGET${NC}"
    exit 1
fi

# ============================================================
# Summary
# ============================================================
echo -e "\n${GREEN}=========================================="
echo "✅ Setup Completado Exitosamente"
echo "==========================================${NC}"

echo -e "\n${BLUE}Próximos pasos:${NC}"
echo "1. Reiniciar la API:"
echo -e "   ${YELLOW}cd $(dirname $ENV_FILE)${NC}"
echo -e "   ${YELLOW}python -m uvicorn main:app --reload${NC}"
echo ""
echo "2. Verificar que Firebase está habilitado:"
echo -e "   ${YELLOW}curl http://localhost:8000/api/notificaciones/push/status${NC}"
echo ""
echo "3. Ejecutar diagnóstico (si está disponible):"
echo -e "   ${YELLOW}python diagnose_push.py${NC}"

echo -e "\n${BLUE}Información útil:${NC}"
echo -e "  Credenciales: ${GREEN}$TARGET${NC}"
echo -e "  .env: ${GREEN}$ENV_FILE${NC}"
echo -e "  Proyecto Firebase: ${GREEN}$PROJECT_ID${NC}"

echo ""
