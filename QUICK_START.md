# 🚨 QUICK START - Arreglar Notificaciones Push

## El Problema
Las notificaciones push **NO LLEGAN** ❌
Logs muestran: `"Sin dispositivo activo para push"`

## La Realidad
```
App móvil ❌ nunca registra su dispositivo en el backend
     ↓
Backend no tiene tokens push para enviar
     ↓
Notificaciones no llegan
```

## Solución: 3 Pasos

### 1️⃣ Backend (Tu EC2) - 5 minutos
```bash
# El archivo JSON de Firebase ya debes tenerlo
# Si no lo tienes, bajarlo de Firebase Console

# Copiar a EC2
scp /ruta/local/firebase-service-account.json ec2-user@TU_IP:/home/ec2-user/

# O si ya está en EC2, ejecutar script:
bash setup_firebase_push.sh /home/ec2-user/firebase-service-account.json

# Verificar
python diagnose_push.py
# Debe mostrar: ✅ Firebase Push está HABILITADO
```

### 2️⃣ App Móvil (Kotlin) - La parte importante ⭐
**Agregaga ESTO após hacer login exitoso:**

```kotlin
// Después que login retorna token JWT
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val fcmToken = task.result
        
        // 👇 ESTO ES LO QUE FALTA EN TU APP
        registrarDispositivoEnBackend(fcmToken, jwtToken)
    }
}

fun registrarDispositivoEnBackend(
    fcmToken: String,
    jwtToken: String
) {
    val request = DeviceRegistrationRequest(
        uuid_dispositivo = getDeviceUUID(),
        plataforma = "android",
        token_push = fcmToken
    )
    
    apiService.call(
        Method = "POST",
        url = "/api/notificaciones/dispositivos",
        auth = "Bearer $jwtToken",
        body = request
    )
}
```

**Documentación completa:** [MOBILE_PUSH_SETUP.md](MOBILE_PUSH_SETUP.md)

### 3️⃣ Test
```bash
# En tu EC2
curl http://localhost:8000/api/notificaciones/push/test \
  -H "Authorization: Bearer JWT_TOKEN_AQUI"

# Deberías ver la notificación en tu móvil
```

## 📋 Archivos Clave

| Archivo | Para Qué | Urgencia |
|---------|----------|----------|
| `.env` | Config backend | ✅ Ya listo |
| `DEBUG_PUSH.md` | Guía completa | 📖 Referencia |
| `MOBILE_PUSH_SETUP.md` | **Código Kotlin exacto** | ⭐ **IMPORTANTE** |
| `diagnose_push.py` | Verificar sistema | 🔍 Verificar |
| `setup_firebase_push.sh` | Setup EC2 automático | 🚀 Usar esto |

## 🎯 Sin Andarte Por Las Ramas

1. **Backend:**
   - ✅ Copiar Firebase JSON a `/home/ec2-user/firebase-service-account.json`
   - ✅ Ejecutar: `bash setup_firebase_push.sh ...`
   - ✅ Verificar: `python diagnose_push.py`

2. **App:**
   - ❌ Implementar registro de dispositivo post-login
   - ❌ (VER: MOBILE_PUSH_SETUP.md - copia y pega el código)

3. **Test:**
   - `curl http://IP:8000/api/notificaciones/push/status`
   - Debe retornar `{"firebase_push_enabled": true}`

4. **Go:**
   - Usuario A sigue a Usuario B → 💬 Notificación llega ✅

---

**Próximo paso:** Lee [MOBILE_PUSH_SETUP.md](MOBILE_PUSH_SETUP.md) y copia el código Kotlin

**Duda rápida:** Usa [DEBUG_PUSH.md](DEBUG_PUSH.md) para debugging
