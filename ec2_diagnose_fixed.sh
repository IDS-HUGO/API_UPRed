#!/bin/bash

# 🚀 Diagnóstico corregido para tu setup EC2 - UPRed Push
# Ejecutar en EC2: bash ec2_diagnose_fixed.sh

echo "=========================================="
echo "🔍 DIAGNÓSTICO CORREGIDO EC2 - UPRed Push"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directorios basados en tu setup
API_DIR="/opt/upred/ws"  # Donde ejecutas la API
REPO_DIR="/opt/upred/API_UPRed"  # Donde están los archivos del repo

# ============================================================
# 1. Verificar directorios
# ============================================================
echo -e "\n${BLUE}[1/7] Verificando directorios...${NC}"

if [ -d "$API_DIR" ]; then
    echo -e "${GREEN}✅ Directorio API encontrado: $API_DIR${NC}"
else
    echo -e "${RED}❌ Directorio API no encontrado: $API_DIR${NC}"
fi

if [ -d "$REPO_DIR" ]; then
    echo -e "${GREEN}✅ Directorio repo encontrado: $REPO_DIR${NC}"
else
    echo -e "${RED}❌ Directorio repo no encontrado: $REPO_DIR${NC}"
fi

# ============================================================
# 2. Copiar archivos de configuración desde repo
# ============================================================
echo -e "\n${BLUE}[2/7] Copiando archivos de configuración...${NC}"

# Copiar .env si existe en repo
if [ -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env" "$API_DIR/.env"
    echo -e "${GREEN}✅ .env copiado desde repo${NC}"
else
    echo -e "${RED}❌ .env no encontrado en repo${NC}"
fi

# Copiar scripts de diagnóstico
if [ -f "$REPO_DIR/ec2_diagnose.py" ]; then
    cp "$REPO_DIR/ec2_diagnose.py" "$API_DIR/ec2_diagnose.py"
    echo -e "${GREEN}✅ ec2_diagnose.py copiado${NC}"
fi

if [ -f "$REPO_DIR/debug_seguir.py" ]; then
    cp "$REPO_DIR/debug_seguir.py" "$API_DIR/debug_seguir.py"
    echo -e "${GREEN}✅ debug_seguir.py copiado${NC}"
fi

# ============================================================
# 3. Verificar Firebase JSON
# ============================================================
echo -e "\n${BLUE}[3/7] Verificando Firebase JSON...${NC}"

FIREBASE_PATHS=(
    "/opt/upred/firebase-service-account.json"
    "/home/ubuntu/firebase-service-account.json"
    "/opt/upred/ws/firebase-service-account.json"
    "$API_DIR/firebase-service-account.json"
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
    echo -e "${YELLOW}💡 Necesitas subir firebase-service-account.json a EC2${NC}"
    echo -e "${YELLOW}   scp firebase-service-account.json ubuntu@TU_IP:/opt/upred/${NC}"
fi

# ============================================================
# 4. Configurar .env
# ============================================================
echo -e "\n${BLUE}[4/7] Configurando .env...${NC}"

if [ -f "$API_DIR/.env" ]; then
    echo -e "${GREEN}✅ .env encontrado en $API_DIR${NC}"

    # Actualizar FIREBASE_SERVICE_ACCOUNT_PATH si Firebase fue encontrado
    if [ "$FIREBASE_FOUND" = true ]; then
        if grep -q "FIREBASE_SERVICE_ACCOUNT_PATH" "$API_DIR/.env"; then
            sed -i "s|^FIREBASE_SERVICE_ACCOUNT_PATH=.*|FIREBASE_SERVICE_ACCOUNT_PATH=$FIREBASE_PATH|" "$API_DIR/.env"
            echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH actualizado${NC}"
        else
            echo "FIREBASE_SERVICE_ACCOUNT_PATH=$FIREBASE_PATH" >> "$API_DIR/.env"
            echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH agregado${NC}"
        fi
    fi

    # Mostrar configuración actual
    echo -e "${BLUE}Configuración actual:${NC}"
    grep -E "(FIREBASE|DB_|API_)" "$API_DIR/.env" | head -10

else
    echo -e "${RED}❌ .env no encontrado en $API_DIR${NC}"
fi

# ============================================================
# 5. Verificar API corriendo
# ============================================================
echo -e "\n${BLUE}[5/7] Verificando API...${NC}"

# Verificar procesos
API_PROCESS=$(ps aux | grep "python.*app.py" | grep -v grep)
if [ -n "$API_PROCESS" ]; then
    echo -e "${GREEN}✅ API corriendo${NC}"
    echo "$API_PROCESS" | head -1
    API_RUNNING=true
else
    echo -e "${RED}❌ API no está corriendo${NC}"
    echo -e "${YELLOW}💡 Ejecuta: cd /opt/upred/ws && python -u app.py${NC}"
    API_RUNNING=false
fi

# Test API si está corriendo
if [ "$API_RUNNING" = true ]; then
    if curl -s --max-time 5 http://localhost:8000/api/notificaciones/push/status > /tmp/api_status.json 2>/dev/null; then
        echo -e "${GREEN}✅ API responde en localhost:8000${NC}"

        ENABLED=$(python3 -c "import json; print(json.load(open('/tmp/api_status.json')).get('firebase_push_enabled', False))" 2>/dev/null)
        if [ "$ENABLED" = "True" ]; then
            echo -e "${GREEN}✅ Firebase Push HABILITADO${NC}"
        else
            echo -e "${RED}❌ Firebase Push DESHABILITADO${NC}"
        fi
    else
        echo -e "${RED}❌ API no responde (puerto cerrado)${NC}"
    fi
fi

# ============================================================
# 6. Verificar BD (con tunnel SSH)
# ============================================================
echo -e "\n${BLUE}[6/7] Verificando base de datos...${NC}"

# Verificar tunnel SSH
TUNNEL_PROCESS=$(ps aux | grep "ssh.*-L 3307:127.0.0.1:3306" | grep -v grep)
if [ -n "$TUNNEL_PROCESS" ]; then
    echo -e "${GREEN}✅ Tunnel SSH activo (puerto 3307)${NC}"
    DB_PORT=3307
else
    echo -e "${YELLOW}⚠️  Tunnel SSH no encontrado, intentando puerto 3306${NC}"
    DB_PORT=3306
fi

# Test conexión BD
if mysql -u root -P$DB_PORT -e "SELECT 1" upred_db 2>/dev/null; then
    echo -e "${GREEN}✅ Conexión BD exitosa (puerto $DB_PORT)${NC}"

    # Contar usuarios
    USUARIOS=$(mysql -u root -P$DB_PORT -e "SELECT COUNT(*) FROM usuarios" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Usuarios totales: $USUARIOS${NC}"

    # Contar dispositivos
    DISPOSITIVOS=$(mysql -u root -P$DB_PORT -e "SELECT COUNT(*) FROM dispositivos_usuario" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Dispositivos registrados: $DISPOSITIVOS${NC}"

    # Contar con token
    CON_TOKEN=$(mysql -u root -P$DB_PORT -e "SELECT COUNT(*) FROM dispositivos_usuario WHERE token_push IS NOT NULL AND token_push != ''" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Con token push: $CON_TOKEN${NC}"

    if [ "$CON_TOKEN" -gt 0 ]; then
        echo -e "${GREEN}✅ Hay dispositivos con tokens${NC}"
        DB_OK=true
    else
        echo -e "${RED}❌ NO hay dispositivos con tokens${NC}"
        echo -e "${YELLOW}💡 La app móvil NO registra dispositivos${NC}"
        DB_OK=false
    fi

    # Debug del error 400
    echo -e "\n${BLUE}Debug error 400:${NC}"
    RELACION=$(mysql -u root -P$DB_PORT -e "SELECT COUNT(*) FROM seguidores WHERE seguidor_id=2 AND seguido_id=1" upred_db 2>/dev/null | tail -1)
    if [ "$RELACION" -gt 0 ]; then
        echo -e "${RED}❌ Usuario 2 YA sigue a usuario 1 → Error 400 correcto${NC}"
    else
        echo -e "${GREEN}✅ No existe relación previa${NC}"
    fi

else
    echo -e "${RED}❌ No se puede conectar a BD (puerto $DB_PORT)${NC}"
    DB_OK=false
fi

# ============================================================
# 7. Resumen y próximos pasos
# ============================================================
echo -e "\n${BLUE}[7/7] RESUMEN Y PRÓXIMOS PASOS${NC}"
echo "=========================================="

ISSUES=0

if [ "$FIREBASE_FOUND" = false ]; then
    echo -e "${RED}❌ Subir firebase-service-account.json a EC2${NC}"
    echo -e "${YELLOW}   scp firebase-service-account.json ubuntu@TU_IP:/opt/upred/${NC}"
    ((ISSUES++))
fi

if [ "$API_RUNNING" = false ]; then
    echo -e "${RED}❌ Iniciar la API${NC}"
    echo -e "${YELLOW}   cd /opt/upred/ws && python -u app.py${NC}"
    ((ISSUES++))
fi

if [ "$DB_OK" = false ]; then
    echo -e "${RED}❌ Verificar conexión BD${NC}"
    ((ISSUES++))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✅ TODO CONFIGURADO CORRECTAMENTE${NC}"
    echo -e "${YELLOW}Si las notificaciones no llegan, el problema está en la app móvil${NC}"
else
    echo -e "${RED}❌ $ISSUES problema(s) encontrado(s)${NC}"
fi

echo -e "\n${GREEN}Comandos para verificar:${NC}"
echo "• Estado API: curl http://localhost:8000/api/notificaciones/push/status"
echo "• Test push: curl -X POST http://localhost:8000/api/notificaciones/push/test -H 'Authorization: Bearer TOKEN'"
echo "• Ver BD: mysql -u root -P$DB_PORT upred_db -e 'SELECT * FROM dispositivos_usuario'"

echo -e "\n${GREEN}¡Diagnóstico completado!${NC}"
