# 📱 Checklist - App Móvil: Configuración de Notificaciones Push

## ✅ Requisitos Previos

- [ ] Android 8.0+ (API 26+)
- [ ] Google Play Services actualizado
- [ ] Proyecto Firebase creado y configurado en Google Cloud Console
- [ ] `google-services.json` descargado y en `app/`

## 🔧 Implementación en la App

### 1️⃣ Obtener Token FCM Después del Login

**Ubicación:** En el Activity/Fragment después de `login exitoso`

```kotlin
// Después de login exitoso, obtener token FCM
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (!task.isSuccessful) {
        Log.w("FCM", "obtener token FCM falló", task.exception)
        return@addOnCompleteListener
    }
    
    val token = task.result
    Log.d("FCM", "Token FCM: $token")
    
    // Guardar en SharedPreferences
    val sharedPref = context?.getSharedPreferences("fcm_prefs", Context.MODE_PRIVATE)
    sharedPref?.edit()?.apply {
        putString("fcm_token", token)
        apply()
    }
    
    // IMPORTANTE: Registrar dispositivo en el backend
    registrarDispositivoEnBackend(token)
}
```

### 2️⃣ Registrar Dispositivo en Backend

**Ubicación:** Servicio de API en la app

```kotlin
suspend fun registrarDispositivoConToken(
    token: String,
    jwtToken: String
) {
    val request = DeviceRegistrationRequest(
        uuid_dispositivo = obtenerUuidDispositivo(),  // ID único del device
        plataforma = "android",
        token_push = token
    )
    
    try {
        val response = apiService.registrarDispositivo(
            authorization = "Bearer $jwtToken",
            request = request
        )
        Log.d("Push", "Dispositivo registrado: ${response.message}")
    } catch (e: Exception) {
        Log.e("Push", "Error al registrar dispositivo", e)
    }
}

// En Interface API
interface UsuariosApiService {
    @POST("/api/notificaciones/dispositivos")
    suspend fun registrarDispositivo(
        @Header("Authorization") authorization: String,
        @Body request: DeviceRegistrationRequest
    ): MessageResponse
}

// Data Class
data class DeviceRegistrationRequest(
    val uuid_dispositivo: String,
    val plataforma: String,    // "android" o "ios"
    val token_push: String
)
```

### 3️⃣ Obtener UUID único del dispositivo

```kotlin
import android.os.Build

fun obtenerUuidDispositivo(): String {
    val serialNumber = Build.getSerial()
    val androidId = android.provider.Settings.Secure.getString(
        context?.contentResolver,
        android.provider.Settings.Secure.ANDROID_ID
    )
    return "${Build.DEVICE}-$androidId-$serialNumber"
}
```

### 4️⃣ Escuchar Notificaciones Push (Service)

**Ubicación:** `services/MiServicioFCM.kt`

```kotlin
class MiServicioFCM : FirebaseMessagingService() {
    
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        Log.d("FCM", "Mensaje recibido")
        
        val titulo = remoteMessage.notification?.title ?: "UPRed"
        val cuerpo = remoteMessage.notification?.body ?: ""
        val datos = remoteMessage.data
        
        // Mostrar notificación en bandeja
        mostrarNotificacion(titulo, cuerpo, datos)
    }
    
    override fun onNewToken(token: String) {
        Log.d("FCM", "Token actualizado: $token")
        
        // Actualizar en SharedPreferences
        val sharedPref = getSharedPreferences("fcm_prefs", MODE_PRIVATE)
        sharedPref.edit().apply {
            putString("fcm_token", token)
            apply()
        }
        
        // IMPORTANTE: Notificar al backend del nuevo token
        actualizarTokenEnBackend(token)
    }
    
    private fun mostrarNotificacion(
        titulo: String,
        cuerpo: String,
        datos: Map<String, String>
    ) {
        val channelId = "upred_notifications"
        
        // Crear canal (Android 8+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "UPRed Notificaciones",
                NotificationManager.IMPORTANCE_HIGH
            )
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        }
        
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtras(Bundle().apply {
                datos.forEach { (k, v) -> putString(k, v) }
            })
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)  // Tu ícono
            .setContentTitle(titulo)
            .setContentText(cuerpo)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()
        
        NotificationManagerCompat.from(this).notify(
            System.currentTimeMillis().toInt(),
            notification
        )
    }
}
```

### 5️⃣ Registrar Service en AndroidManifest.xml

```xml
<service
    android:name=".services.MiServicioFCM"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

### 6️⃣ Solicitar Permisos

```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

```kotlin
// En Activity (Android 13+)
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
    requestPermissions(
        arrayOf(Manifest.permission.POST_NOTIFICATIONS),
        NOTIFICATION_PERMISSION_CODE
    )
}
```

### 7️⃣ Re-registrar Token en Background

**Ubicación:** Worker para sincronización periódica

```kotlin
class SincronizadorNotificacionesWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            // Obtener token FCM actual
            val token = FirebaseMessaging.getInstance().token.await()
            
            // Obtener JWT del almacenamiento seguro
            val jwtToken = obtenerJWT() ?: return@withContext Result.retry()
            
            // Registrar/actualizar en backend
            registrarDispositivoConToken(token, jwtToken)
            
            Result.success()
        } catch (e: Exception) {
            Log.e("SincFCM", "Error en sincronización", e)
            Result.retry()
        }
    }
}

// Enqueue en Application.onCreate o cuando detectes cambio de token
val syncRequest = PeriodicWorkRequestBuilder<SincronizadorNotificacionesWorker>(
    24, TimeUnit.HOURS  // Sincronizar cada 24 horas
).build()

WorkManager.getInstance(applicationContext).enqueueUniquePeriodicWork(
    "sync_fcm_tokens",
    ExistingPeriodicWorkPolicy.KEEP,
    syncRequest
)
```

## 📋 Verificación en Logcat

Después de implementar, busca estos logs:

✅ **Correcto:**
```
D/FCM: Token FCM: eJwtzf0PAyAIBPAXSRIkQjIe...
D/Push: Dispositivo registrado: Dispositivo registrado correctamente
```

❌ **Problemas:**
```
W/FCM: obtener token FCM falló [error]
E/Push: Error al registrar dispositivo
```

## 🧪 Testing Manual

1. **Compilar y ejecutar la app**
2. **Hacer login** → Debe registrar dispositivo
3. **En otra parte (web/app)** - Seguir al usuario
4. **Verificar**: ¿Llega la notificación? ✅

## 🛡️ Troubleshooting

| Problema | Solución |
|----------|----------|
| No llega token FCM | ¿Google Play Services actualizado? ¿Cuenta Google? |
| Dispositivo no se registra | Verificar en API: `GET /api/notificaciones/push/status` |
| Notificación llega pero no se muestra | Revisar canal de notificaciones |
| Token expirado | Implementar `onNewToken()` |

## 📚 Referencias

- [Firebase Cloud Messaging Docs](https://firebase.google.com/docs/cloud-messaging)
- [FCM for Android](https://firebase.google.com/docs/cloud-messaging/android/client)
