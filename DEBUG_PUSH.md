# 🔧 Guía de Diagnóstico - Notificaciones Push

## ❌ Problema Identificado
Las notificaciones push no llegan ⟹ Warning: **"Sin dispositivo activo para push"**

## 🎯 Causas Principales

### 1. Firebase No Inicializado ⚠️
```
FIREBASE_SERVICE_ACCOUNT_PATH vacío o archivo inexistente
```

**Solución:**
```bash
# En tu EC2, copia el JSON de Firebase
sudo cp /ruta/a/firebase-service-account.json /home/ec2-user/firebase-service-account.json
sudo chown ec2-user:ec2-user /home/ec2-user/firebase-service-account.json

# Actualizar .env
FIREBASE_SERVICE_ACCOUNT_PATH=/home/ec2-user/firebase-service-account.json
```

### 2. Dispositivos Sin Tokens Push 📱
Los usuarios NO están registrando sus dispositivos con tokens válidos.

**Verificar en BD:**
```sql
-- Ver si hay dispositivos registrados
SELECT id, usuario_id, uuid_dispositivo, token_push, activo 
FROM dispositivos_usuario 
LIMIT 10;

-- Ver específicamente el usuario 2 (del log)
SELECT id, usuario_id, plataforma, token_push, activo, ultima_actividad_en 
FROM dispositivos_usuario 
WHERE usuario_id = 2;
```

### 3. La App Móvil No Está Llamando al Endpoint ❌

**El móvil DEBE hacer esto después de iniciar sesión:**
```bash
POST /api/notificaciones/dispositivos
Content-Type: application/json
Authorization: Bearer {TOKEN}

{
  "uuid_dispositivo": "ab12cd34ef56gh78ij90",
  "plataforma": "android",  // o "ios"
  "token_push": "FIREBASE_TOKEN_AQUI"  // Token de FCM
}
```

## 🔍 Pasos de Verificación

### Paso 1: Verificar Firebase en Backend
```bash
curl http://localhost:8000/api/notificaciones/push/status
```

**Respuesta esperada (✅ OK):**
```json
{
  "firebase_push_enabled": true,
  "service_account_path_present": true
}
```

**Si sale `false`:**
- Credenciales no configuradas
- Path incorrecto en `.env`
- Archivo JSON corrupto

### Paso 2: Enviar Push de Prueba
```bash
# 1. Autenticarse y obtener token JWT
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo_institucional":"usuario@ejemplo.com","contrasena":"password"}'

# Copiar el token del response

# 2. Enviar push de prueba
curl -X POST http://localhost:8000/api/notificaciones/push/test \
  -H "Authorization: Bearer {JWT_TOKEN_AQUI}"
```

**Posibles respuestas:**

✅ **200 OK** - Push enviado correctamente
```json
{"message": "Push de prueba enviado"}
```

❌ **503 Service Unavailable** - Firebase no configurado
```json
{"detail": "Firebase no está configurado en el backend"}
```

❌ **404 Not Found** - Sin dispositivos registrados
```json
{"detail": "No hay token push activo para este usuario"}
```

### Paso 3: Verificar Dispositivos Registrados
```bash
curl http://localhost:8000/api/notificaciones/dispositivos \
  -H "Authorization: Bearer {JWT_TOKEN_AQUI}"
```

## 📋 CheckList de Solución

- [ ] **Backend**: Actualizar `.env` con ruta correcta de Firebase JSON
- [ ] **Backend**: Reiniciar API (`python -m uvicorn main:app --reload`)
- [ ] **Backend**: Verificar con `GET /api/notificaciones/push/status`
- [ ] **Mobile**: Obtener token FCM después de iniciar sesión
- [ ] **Mobile**: Registrar dispositivo con `POST /api/notificaciones/dispositivos`
- [ ] **Mobile**: Verificar que `token_push` esté en BD (verificar con SQL)
- [ ] **Testing**: Enviar push de prueba con `POST /api/notificaciones/push/test`
- [ ] **Testing**: Verificar que llega la notificación en el móvil

## 📊 Logs para Monitoring

Busca estos patrones en los logs:

✅ **Inicialización correcta:**
```
INFO upred.firebase_push Firebase Push habilitado correctamente con credenciales: /home/ec2-user/firebase-service-account.json
```

❌ **Error - archivo no existe:**
```
ERROR upred.firebase_push No existe archivo de credenciales Firebase en ruta
```

❌ **Error - sin dispositivo:**
```
WARNING upred.usuarios Sin dispositivo activo para push nuevo_seguidor usuario_destino=2 follower=1
```

✅ **Push enviado:**
```
INFO upred.firebase_push Push enviado correctamente. response=projects/.../messages/...
```

## 🚀 Flujo Completo para Testing

```
┌─────────────────────────────────────────────────────────┐
│  USUARIO MÓVIL                                          │
└────────────────┬────────────────────────────────────────┘
                 │
         1. Login / FCM token
                 │
                 ▼
REGISTRA DISPOSITIVO (POST /api/notificaciones/dispositivos)
                 │
                 ▼
TOKEN_PUSH guardado en BD (dispositivos_usuario.token_push)
                 │
                 ▼
USUARIO 1 SIGUE A USUARIO 2
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  BACKEND (API)                                           │
├──────────────────────────────────────────────────────────┤
│  1. INSERT notificación en DB                            │
│  2. SELECT dispositivo de usuario 2 (con token_push)     │
│  3. ENVIAR push via Firebase                             │
│  4. Firebase delivery → Google Play Services             │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│  DISPOSITIVO MÓVIL USUARIO 2                             │
├──────────────────────────────────────────────────────────┤
│  💬 Recibe notificación:                                 │
│     "Tienes un nuevo seguidor"                           │
│     "Usuario 1 comenzó a seguirte"                       │
└──────────────────────────────────────────────────────────┘
```

## 🆘 Si aún no funciona

1. **Revisa logs del backend:**
   ```bash
   # En la terminal donde corre la API
   tail -100 /var/log/upred-api.log  # O donde esté tu log
   ```

2. **Verifica Firebase JSON válido:**
   ```bash
   python -c "import json; json.load(open('/home/ec2-user/firebase-service-account.json'))"
   ```
   (Si no da error, es válido)

3. **Verifica conexión a MySQL:**
   ```bash
   mysql -u root -p upred_db -e "SELECT COUNT(*) FROM dispositivos_usuario;"
   ```

4. **Test directo con Firebase Admin SDK:**
   ```python
   import firebase_admin
   from firebase_admin import credentials, messaging
   
   cred = credentials.Certificate('/home/ec2-user/firebase-service-account.json')
   firebase_admin.initialize_app(cred)
   
   # Si llega aquí sin error, Firebase está bien configurado
   print("✅ Firebase inicializado correctamente")
   ```
