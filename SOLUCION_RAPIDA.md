# 🚨 SOLUCIÓN RÁPIDA - Error 400 y Push Notifications

## ❌ Problemas Identificados

### 1. Error 400 en seguir usuario
Del log: `seguidor_id_1: 2, seguido_id_1: 1` → Usuario 2 intentando seguir a usuario 1
**Causa probable:** Ya existe la relación de seguimiento

### 2. Push notifications no llegan
**Causa:** La app móvil NUNCA registra dispositivos en el backend

## ✅ Solución Paso a Paso

### PASO 1: Diagnosticar en EC2
```bash
# En tu EC2, ejecuta:
cd /opt/upred/ws
wget https://raw.githubusercontent.com/tu-repo/ec2_full_diagnose.sh -O ec2_full_diagnose.sh
chmod +x ec2_full_diagnose.sh
bash ec2_full_diagnose.sh
```

**Resultado esperado:**
- ✅ Firebase JSON encontrado
- ✅ .env configurado
- ✅ API funcionando
- ❌ NO hay dispositivos con tokens

### PASO 2: Verificar Error 400 Específico
```bash
# En EC2:
mysql -u root upred_db -e "
  SELECT COUNT(*) as relacion_existe FROM seguidores
  WHERE seguidor_id=2 AND seguido_id=1;
"
```

**Si retorna > 0:** Usuario 2 ya sigue a usuario 1 → Error 400 correcto
**Si retorna 0:** Hay otro problema en el código

### PASO 3: Verificar Dispositivos
```bash
# En EC2:
mysql -u root upred_db -e "
  SELECT usuario_id, plataforma, token_push, activo
  FROM dispositivos_usuario
  WHERE usuario_id=1;
"
```

**Si no hay resultados:** Usuario 1 no tiene dispositivos registrados → Push no llega

### PASO 4: Solución App Móvil (CRÍTICO)

**Después de login exitoso en Android/Kotlin:**

```kotlin
// 1. Obtener token FCM
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val fcmToken = task.result
        
        // 2. REGISTRAR DISPOSITIVO (ESTO FALTA)
        val request = DeviceRegistrationRequest(
            uuid_dispositivo = getDeviceUUID(),
            plataforma = "android",
            token_push = fcmToken
        )
        
        // 3. Llamar a API
        apiService.registrarDispositivo(
            authorization = "Bearer $jwtToken",
            request = request
        ).enqueue(object : Callback<MessageResponse> {
            override fun onResponse(call: Call<MessageResponse>, response: Response<MessageResponse>) {
                if (response.isSuccessful) {
                    Log.d("Push", "Dispositivo registrado correctamente")
                }
            }
            override fun onFailure(call: Call<MessageResponse>, t: Throwable) {
                Log.e("Push", "Error registrando dispositivo", t)
            }
        })
    }
}

// Función helper
fun getDeviceUUID(): String {
    return "${android.os.Build.DEVICE}-${android.provider.Settings.Secure.getString(
        context?.contentResolver,
        android.provider.Settings.Secure.ANDROID_ID
    )}"
}
```

### PASO 5: Verificar Solución
```bash
# Después de implementar en app:
mysql -u root upred_db -e "SELECT COUNT(*) FROM dispositivos_usuario WHERE token_push IS NOT NULL;"

# Debería retornar > 0

# Test push:
curl -X POST http://localhost:8000/api/notificaciones/push/test \
  -H "Authorization: Bearer TU_JWT_TOKEN"
```

## 📋 Checklist Final

- [ ] **EC2**: Firebase JSON copiado y configurado
- [ ] **EC2**: `bash ec2_full_diagnose.sh` muestra ✅ en todo
- [ ] **App**: Implementado registro de dispositivo post-login
- [ ] **BD**: `SELECT * FROM dispositivos_usuario` tiene registros con token_push
- [ ] **Test**: Seguir usuario → notificación llega ✅

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Error 400 persiste | Verificar si ya existe relación en BD |
| Push no llega | App no registra dispositivo |
| Firebase disabled | Copiar JSON y configurar .env |
| API no responde | Verificar que esté corriendo |

## 📞 Contacto
Si sigues teniendo problemas, comparte la salida de `bash ec2_full_diagnose.sh`
