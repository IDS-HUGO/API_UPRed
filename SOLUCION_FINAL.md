# 🚨 SOLUCIÓN FINAL - Error 400 + Push Notifications

## ❌ Problemas Diagnosticados

### 1. **Error 400 en seguir usuario**
- **Causa**: Usuario 2 ya sigue a usuario 1 (relación existente)
- **Solución**: Verificar lógica en app móvil

### 2. **Push notifications no llegan**
- **Causa**: La app móvil **NUNCA registra dispositivos**
- **Solución**: Implementar registro de dispositivo post-login

### 3. **Configuración EC2 incompleta**
- **Causa**: Falta Firebase JSON y .env mal configurado
- **Solución**: Setup automático

## ✅ SOLUCIÓN PASO A PASO

### PASO 1: Setup Automático EC2 (5 minutos)

**Opción A: Desde tu máquina local (recomendado)**
```bash
# En tu máquina local, en el directorio del proyecto
cd /home/eduardo-mandujano/Escuela/CTRSM8/Moviles/API_UPRed

# Asegúrate de tener firebase-service-account.json
ls firebase-service-account.json  # Debe existir

# Ejecutar setup completo
bash setup_ec2_complete.sh TU_IP_EC2

# Ejemplo:
bash setup_ec2_complete.sh 172.31.16.59
```

**Opción B: Manualmente en EC2**
```bash
# En EC2
cd /opt/upred
wget https://raw.githubusercontent.com/tu-repo/auto_setup_ec2.sh -O auto_setup_ec2.sh
chmod +x auto_setup_ec2.sh
bash auto_setup_ec2.sh
```

### PASO 2: Verificar Configuración
```bash
# En EC2, después del setup
curl http://localhost:8000/api/notificaciones/push/status

# Debe retornar:
{
  "firebase_push_enabled": true,
  "service_account_path_present": true
}
```

### PASO 3: Verificar Error 400
```bash
# En EC2
mysql -u root -P3307 upred_db -e "
  SELECT COUNT(*) FROM seguidores
  WHERE seguidor_id=2 AND seguido_id=1;
"

# Si retorna 1: Ya sigue (error 400 correcto)
# Si retorna 0: Verificar código API
```

### PASO 4: Solución App Móvil (CRÍTICA) ⭐

**Después de login exitoso en Android/Kotlin:**

```kotlin
// En tu Activity/Fragment de login exitoso

FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val fcmToken = task.result
        
        // 👇 AGREGAR ESTO - REGISTRO DE DISPOSITIVO
        registrarDispositivoEnBackend(fcmToken, jwtToken)
    }
}

suspend fun registrarDispositivoEnBackend(
    fcmToken: String,
    jwtToken: String
) {
    val request = DeviceRegistrationRequest(
        uuid_dispositivo = getDeviceUUID(),
        plataforma = "android",
        token_push = fcmToken
    )
    
    try {
        val response = apiService.registrarDispositivo(
            authorization = "Bearer $jwtToken",
            request = request
        )
        Log.d("Push", "Dispositivo registrado: ${response.message}")
    } catch (e: Exception) {
        Log.e("Push", "Error registrando dispositivo", e)
    }
}

fun getDeviceUUID(): String {
    return "${android.os.Build.DEVICE}-${
        android.provider.Settings.Secure.getString(
            context?.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )
    }"
}
```

**Data class para la API:**
```kotlin
data class DeviceRegistrationRequest(
    val uuid_dispositivo: String,
    val plataforma: String,
    val token_push: String
)
```

### PASO 5: Verificar Solución
```bash
# Después de implementar en app
mysql -u root -P3307 upred_db -e "
  SELECT usuario_id, plataforma, token_push, activo
  FROM dispositivos_usuario
  WHERE usuario_id=1;
"

# Debería mostrar registros con token_push
```

### PASO 6: Test End-to-End
```bash
# 1. Obtener JWT token
curl -X POST http://TU_EC2_IP:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo_institucional":"usuario@ejemplo.com","contrasena":"password"}'

# 2. Test push
curl -X POST http://TU_EC2_IP:8000/api/notificaciones/push/test \
  -H "Authorization: Bearer TU_JWT_TOKEN"

# 3. La app debe recibir notificación ✅
```

## 📋 Checklist Final

### Backend EC2
- [ ] Firebase JSON subido a `/opt/upred/firebase-service-account.json`
- [ ] `.env configurado con `FIREBASE_SERVICE_ACCOUNT_PATH`
- [ ] API corriendo en puerto 8000
- [ ] `GET /api/notificaciones/push/status` retorna `firebase_push_enabled: true`

### App Móvil
- [ ] Obtener token FCM después de login ✅
- [ ] **Registrar dispositivo en backend** ✅ ← **ESTO FALTA**
- [ ] Service FCM para recibir notificaciones ✅
- [ ] Permisos POST_NOTIFICATIONS ✅

### Testing
- [ ] Usuario A sigue a Usuario B
- [ ] Verificar: ¿Llega notificación en dispositivo B? ✅
- [ ] Comentar publicación → notificación llega ✅

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Error 400 persiste | Verificar BD: relación ya existe |
| Push no llega | App no registra dispositivo |
| Firebase disabled | Verificar JSON y .env |
| API no responde | `cd /opt/upred/ws && python -u app.py` |

## 📁 Archivos de Solución

| Archivo | Propósito | Ejecutar |
|---------|-----------|----------|
| `setup_ec2_complete.sh` | Setup completo desde local | `bash setup_ec2_complete.sh IP` |
| `auto_setup_ec2.sh` | Setup automático en EC2 | `bash auto_setup_ec2.sh` |
| `ec2_diagnose_fixed.sh` | Diagnóstico corregido | `bash ec2_diagnose_fixed.sh` |
| `debug_seguir.py` | Debug error 400 | `python3 debug_seguir.py` |
| `MOBILE_PUSH_SETUP.md` | **Código Kotlin exacto** | **Leer esto** |

## 🎯 Resumen Ejecutivo

```
✅ Backend: Setup automático listo
❌ App: Necesita registrar dispositivo post-login
= Resultado: Push funcionará después de implementar app
```

**Tiempo estimado:** 15 minutos setup EC2 + 20 minutos app móvil = **35 minutos total**

¡Las notificaciones push funcionarán perfectamente una vez que la app registre dispositivos! 🚀
