# 🖥️ Comandos para Ejecutar en EC2

## 1. Descargar y Ejecutar Diagnóstico Completo
```bash
cd /opt/upred/ws

# Descargar script de diagnóstico
wget https://raw.githubusercontent.com/tu-repo/ec2_full_diagnose.sh -O ec2_full_diagnose.sh 2>/dev/null || curl -s https://raw.githubusercontent.com/tu-repo/ec2_full_diagnose.sh -o ec2_full_diagnose.sh

# Hacer ejecutable
chmod +x ec2_full_diagnose.sh

# Ejecutar diagnóstico
bash ec2_full_diagnose.sh
```

## 2. Verificar Error 400 Específico
```bash
# Verificar si usuario 2 ya sigue a usuario 1
mysql -u root upred_db -e "
  SELECT COUNT(*) as relacion_existe
  FROM seguidores
  WHERE seguidor_id=2 AND seguido_id=1;
"

# Si retorna 1: Ya sigue → Error 400 correcto
# Si retorna 0: Otro problema
```

## 3. Verificar Estado de Dispositivos
```bash
# Ver todos los dispositivos
mysql -u root upred_db -e "
  SELECT usuario_id, plataforma, token_push, activo, ultima_actividad_en
  FROM dispositivos_usuario
  ORDER BY ultima_actividad_en DESC;
"

# Contar dispositivos con token
mysql -u root upred_db -e "
  SELECT
    COUNT(*) as total_dispositivos,
    SUM(CASE WHEN token_push IS NOT NULL AND token_push != '' THEN 1 ELSE 0 END) as con_token
  FROM dispositivos_usuario;
"
```

## 4. Test Manual de Push
```bash
# Obtener JWT token primero (login)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo_institucional":"usuario@ejemplo.com","contrasena":"password"}'

# Copiar el token del response y usar en:
curl -X POST http://localhost:8000/api/notificaciones/push/test \
  -H "Authorization: Bearer TU_JWT_TOKEN_AQUI"
```

## 5. Verificar Logs de la API
```bash
# Si usas gunicorn o similar
tail -f /var/log/upred/api.log

# O buscar en archivos de log
find /var/log -name "*upred*" -o -name "*api*" | head -5
```

## 6. Reiniciar API si es Necesario
```bash
# Matar procesos existentes
sudo fuser -k 8000/tcp || true
sudo fuser -k 5000/tcp || true

# Reiniciar API
cd /opt/upred/ws
source .venv/bin/activate
FLASK_ENV=development python -u app.py
```

## 7. Verificar Firebase JSON
```bash
# Verificar que existe
ls -la /home/ec2-user/firebase-service-account.json

# Verificar contenido
python3 -c "import json; print(json.load(open('/home/ec2-user/firebase-service-account.json')).get('project_id'))"
```

## 8. Backup de BD antes de Cambios
```bash
mysqldump -u root upred_db > upred_db_backup_$(date +%Y%m%d_%H%M%S).sql
```

## 9. Limpiar Dispositivos Antiguos (Opcional)
```bash
# Ver dispositivos antiguos
mysql -u root upred_db -e "
  SELECT id, usuario_id, ultima_actividad_en,
         DATEDIFF(NOW(), ultima_actividad_en) as dias_sin_actividad
  FROM dispositivos_usuario
  WHERE ultima_actividad_en < DATE_SUB(NOW(), INTERVAL 30 DAY);
"

# Eliminar si es necesario
mysql -u root upred_db -e "
  DELETE FROM dispositivos_usuario
  WHERE ultima_actividad_en < DATE_SUB(NOW(), INTERVAL 30 DAY);
"
```

## 10. Verificar Conectividad de Red
```bash
# Test conexión a internet
curl -s https://www.google.com > /dev/null && echo "✅ Internet OK" || echo "❌ Sin internet"

# Test conexión a Firebase
curl -s https://fcm.googleapis.com > /dev/null && echo "✅ Firebase reachable" || echo "❌ Firebase no reachable"
```

---

**Ejecuta primero:** `bash ec2_full_diagnose.sh`
**Comparte la salida** si tienes problemas
