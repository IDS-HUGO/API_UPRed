#!/bin/bash

# 🚀 Diagnóstico completo para EC2 - Push Notifications UPRed
# Ejecutar en EC2: bash ec2_full_diagnose.sh

echo "=========================================="
echo "🔍 DIAGNÓSTICO COMPLETO EC2 - UPRed Push"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================
# 1. Verificar archivos
# ============================================================
echo -e "\n${BLUE}[1/6] Verificando archivos de configuración...${NC}"

# Firebase JSON
FIREBASE_PATHS=(
    "/home/ec2-user/firebase-service-account.json"
    "/opt/upred/ws/firebase-service-account.json"
    "/home/ubuntu/firebase-service-account.json"
)

FIREBASE_FOUND=false
for path in "${FIREBASE_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo -e "${GREEN}✅ Firebase JSON encontrado: $path${NC}"
        if python3 -c "import json; json.load(open('$path'))" 2>/dev/null; then
            PROJECT_ID=$(python3 -c "import json; print(json.load(open('$path')).get('project_id', 'unknown'))")
            echo -e "${GREEN}✅ JSON válido - Proyecto: $PROJECT_ID${NC}"
            FIREBASE_FOUND=true
            break
        else
            echo -e "${RED}❌ JSON inválido${NC}"
        fi
    fi
done

if [ "$FIREBASE_FOUND" = false ]; then
    echo -e "${RED}❌ Firebase JSON no encontrado en rutas comunes${NC}"
    echo -e "${YELLOW}ℹ️  Necesitas copiar firebase-service-account.json a EC2${NC}"
fi

# .env
ENV_PATHS=(
    "/opt/upred/ws/.env"
    "/home/ec2-user/.env"
)

ENV_FOUND=false
for path in "${ENV_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo -e "${GREEN}✅ .env encontrado: $path${NC}"
        if grep -q "FIREBASE_SERVICE_ACCOUNT_PATH" "$path"; then
            echo -e "${GREEN}✅ FIREBASE_SERVICE_ACCOUNT_PATH configurado${NC}"
            ENV_FOUND=true
        else
            echo -e "${RED}❌ FIREBASE_SERVICE_ACCOUNT_PATH no configurado${NC}"
        fi
        break
    fi
done

if [ "$ENV_FOUND" = false ]; then
    echo -e "${RED}❌ .env no encontrado o mal configurado${NC}"
fi

# ============================================================
# 2. Verificar API
# ============================================================
echo -e "\n${BLUE}[2/6] Verificando API...${NC}"

if curl -s http://localhost:8000/api/notificaciones/push/status > /tmp/api_status.json 2>/dev/null; then
    echo -e "${GREEN}✅ API responde en localhost:8000${NC}"

    ENABLED=$(python3 -c "import json; print(json.load(open('/tmp/api_status.json')).get('firebase_push_enabled', False))")
    PATH_PRESENT=$(python3 -c "import json; print(json.load(open('/tmp/api_status.json')).get('service_account_path_present', False))")

    if [ "$ENABLED" = "True" ]; then
        echo -e "${GREEN}✅ Firebase Push HABILITADO${NC}"
        API_OK=true
    else
        echo -e "${RED}❌ Firebase Push DESHABILITADO${NC}"
        API_OK=false
    fi

    if [ "$PATH_PRESENT" = "True" ]; then
        echo -e "${GREEN}✅ Service account path presente${NC}"
    else
        echo -e "${RED}❌ Service account path no presente${NC}"
    fi
else
    echo -e "${RED}❌ API no responde en localhost:8000${NC}"
    echo -e "${YELLOW}ℹ️  ¿Está corriendo la API?${NC}"
    API_OK=false
fi

# ============================================================
# 3. Verificar BD
# ============================================================
echo -e "\n${BLUE}[3/6] Verificando base de datos...${NC}"

# Intentar conectar a BD
if mysql -u root -e "SELECT 1" upred_db 2>/dev/null; then
    echo -e "${GREEN}✅ Conexión BD exitosa${NC}"

    # Contar usuarios
    USUARIOS=$(mysql -u root -e "SELECT COUNT(*) FROM usuarios" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Usuarios totales: $USUARIOS${NC}"

    # Contar dispositivos
    DISPOSITIVOS=$(mysql -u root -e "SELECT COUNT(*) FROM dispositivos_usuario" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Dispositivos registrados: $DISPOSITIVOS${NC}"

    # Contar con token
    CON_TOKEN=$(mysql -u root -e "SELECT COUNT(*) FROM dispositivos_usuario WHERE token_push IS NOT NULL AND token_push != ''" upred_db 2>/dev/null | tail -1)
    echo -e "${BLUE}ℹ️  Con token push: $CON_TOKEN${NC}"

    if [ "$CON_TOKEN" -gt 0 ]; then
        echo -e "${GREEN}✅ Hay dispositivos con tokens${NC}"
        DB_OK=true
    else
        echo -e "${RED}❌ NO hay dispositivos con tokens${NC}"
        echo -e "${YELLOW}💡 La app móvil NO registra dispositivos${NC}"
        DB_OK=false
    fi

else
    echo -e "${RED}❌ No se puede conectar a BD${NC}"
    DB_OK=false
fi

# ============================================================
# 4. Debug del error 400
# ============================================================
echo -e "\n${BLUE}[4/6] Debug del error 400 en seguir...${NC}"

if mysql -u root upred_db -e "
    SELECT 'Usuarios:' as info, COUNT(*) as count FROM usuarios
    UNION ALL
    SELECT 'Relación 2->1 existe:', COUNT(*) FROM seguidores WHERE seguidor_id=2 AND seguido_id=1
    UNION ALL
    SELECT 'Dispositivos usuario 1:', COUNT(*) FROM dispositivos_usuario WHERE usuario_id=1
" 2>/dev/null; then

    # Verificar relación específica
    RELACION=$(mysql -u root -e "SELECT COUNT(*) FROM seguidores WHERE seguidor_id=2 AND seguido_id=1" upred_db 2>/dev/null | tail -1)

    if [ "$RELACION" -gt 0 ]; then
        echo -e "${RED}❌ ERROR 400: Usuario 2 YA sigue a usuario 1${NC}"
        echo -e "${YELLOW}💡 Solución: Dejar de seguir primero o verificar app${NC}"
    else
        echo -e "${GREEN}✅ No existe relación previa - debería funcionar${NC}"
    fi

else
    echo -e "${RED}❌ Error consultando BD${NC}"
fi

# ============================================================
# 5. Test de push
# ============================================================
echo -e "\n${BLUE}[5/6] Test de notificación push...${NC}"

# Obtener JWT token (asumiendo que hay uno guardado o pedirlo)
echo -e "${YELLOW}ℹ️  Para testear push necesitas un JWT token válido${NC}"
echo -e "${YELLOW}ℹ️  Ejecuta: curl -X POST http://localhost:8000/api/notificaciones/push/test \\${NC}"
echo -e "${YELLOW}   -H \"Authorization: Bearer TU_JWT_TOKEN\"${NC}"

# ============================================================
# 6. Resumen y recomendaciones
# ============================================================
echo -e "\n${BLUE}[6/6] RESUMEN Y RECOMENDACIONES${NC}"
echo "=========================================="

ISSUES=0

if [ "$FIREBASE_FOUND" = false ]; then
    echo -e "${RED}❌ Copiar firebase-service-account.json a EC2${NC}"
    ((ISSUES++))
fi

if [ "$ENV_FOUND" = false ]; then
    echo -e "${RED}❌ Configurar FIREBASE_SERVICE_ACCOUNT_PATH en .env${NC}"
    ((ISSUES++))
fi

if [ "$API_OK" = false ]; then
    echo -e "${RED}❌ Verificar que API esté corriendo${NC}"
    ((ISSUES++))
fi

if [ "$DB_OK" = false ]; then
    echo -e "${RED}❌ App móvil no registra dispositivos${NC}"
    echo -e "${YELLOW}💡 IMPLEMENTAR: POST /api/notificaciones/dispositivos después de login${NC}"
    ((ISSUES++))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✅ TODO CONFIGURADO CORRECTAMENTE${NC}"
    echo -e "${YELLOW}Si las notificaciones no llegan, el problema está en la app móvil${NC}"
else
    echo -e "${RED}❌ $ISSUES problema(s) encontrado(s)${NC}"
fi

echo -e "\n${BLUE}Comandos útiles:${NC}"
echo "• Ver dispositivos: mysql -u root upred_db -e 'SELECT * FROM dispositivos_usuario'"
echo "• Ver seguimientos: mysql -u root upred_db -e 'SELECT * FROM seguidores'"
echo "• Test push: curl -X POST http://localhost:8000/api/notificaciones/push/test -H 'Authorization: Bearer TOKEN'"
echo "• Status API: curl http://localhost:8000/api/notificaciones/push/status"

echo -e "\n${GREEN}¡Listo!${NC}"
