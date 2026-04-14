# 📱 Estado de Notificaciones Push - UPRed

## 🎯 Problema Reportado
❌ Las notificaciones push **NO llegan** en:
- Nuevo seguidor
- Comentarios en publicaciones

## 🔍 Causa Identificada

```
┌────────────────────────────────────────────────────────────┐
│                    FLUJO TEÓRICO                           │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Usuario Móvil                                              │
│  ├─ Login                                                   │
│  ├─ Obtiene token FCM ✅                                    │
│  └─ Registra dispositivo ❌ ← FALTA ESTO                    │
│                   │                                         │
│                   ▼                                         │
│  Base de Datos                                              │
│  └─ dispositivos_usuario.token_push ❌ SIN DATOS            │
│                   │                                         │
│                   ▼                                         │
│  Usuario A sigue a Usuario B                               │
│  ├─ Crear notificación interna ✅                           │
│  ├─ Buscar token push de Usuario B ❌ NO ENCUENTRA         │
│  └─ Warning: "Sin dispositivo activo para push" ⚠️          │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**En resumen:**
```
Firebase está bien ✅
Backend está bien ✅
App móvil NO registra dispositivos ❌ ← AQUÍ ESTÁ EL PROBLEMA
```

## ✅ Cambios Realizados al Backend

### 1. Configuración
- ✅ Creado `.env` con ruta Linux correcta
- ✅ Preparado para `/home/ec2-user/firebase-service-account.json`

### 2. Código
- ✅ Mejorado `firebase_push_service.py` con mejor logging
- ✅ Validación de tokens vacíos
- ✅ Mejor manejo de excepciones

### 3. Herramientas Creadas
- ✅ `DEBUG_PUSH.md` - Guía completa de diagnóstico
- ✅ `diagnose_push.py` - Script automático de verificación
- ✅ `MOBILE_PUSH_SETUP.md` - Implementación Kotlin exacta
- ✅ `queries_push.sql` - Queries para inspeccionar BD
- ✅ `setup_firebase_push.sh` - Script setup para EC2
- ✅ `CAMBIOS_REALIZADOS.md` - Resumen de todo

## 🚀 Plan de Acción

### PASO 1: Backend (tu EC2)
```bash
# Copiar JSON de Firebase
cp /ruta/a/firebase-service-account.json /home/ec2-user/

# Setup automático (RECOMENDADO)
bash setup_firebase_push.sh /home/ec2-user/firebase-service-account.json

# Verificar
python diagnose_push.py

# Salida esperada:
# ✅ Firebase Push HABILITADO
```

### PASO 2: Probar endpoint
```bash
curl http://EC2_IP:8000/api/notificaciones/push/status

# Esperado:
# {"firebase_push_enabled": true, "service_account_path_present": true}
```

### PASO 3: App Móvil (CRÍTICO)
**Implementar en Android/Kotlin:**

Después de login:
```kotlin
// Step 1: Obtener token FCM
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val fcmToken = task.result
        
        // Step 2: Registrar dispositivo
        val request = DeviceRegistrationRequest(
            uuid_dispositivo = getDeviceUUID(),
            plataforma = "android",
            token_push = fcmToken
        )
        
        apiService.registrarDispositivo(
            authorization = "Bearer $jwtToken",
            request = request
        )
    }
}
```

**Ver implementación detallada en:** [MOBILE_PUSH_SETUP.md](MOBILE_PUSH_SETUP.md)

### PASO 4: Test End-to-End
```
1. Compilar app con nuevos cambios
2. Hacer login (DEBE registrar dispositivo)
3. Verificar en BD: SELECT * FROM dispositivos_usuario;
4. Usuario A sigue a Usuario B
5. Verificar: ¿Llega notificación en dispositivo B? ✅
```

## 📊 Checklist

### Backend
- [ ] Firebase JSON copiado a `/home/ec2-user/firebase-service-account.json`
- [ ] `.env` actualizado con ruta correcta
- [ ] `python diagnose_push.py` muestra ✅ Firebase Push HABILITADO
- [ ] API reiniciada

### App Móvil
- [ ] Obtener token FCM después de login ✅
- [ ] Registrar dispositivo en backend ✅
- [ ] Service para recibir notificaciones creado ✅
- [ ] Permisos en AndroidManifest.xml ✅
- [ ] Solicitar permisos POST_NOTIFICATIONS en runtime ✅

### Testing
- [ ] `GET /api/notificaciones/push/status` → `{"firebase_push_enabled": true}`
- [ ] Dispositivo en BD con token_push no NULL
- [ ] `POST /api/notificaciones/push/test` → notificación llega
- [ ] Seguir usuario → notificación llega ✅
- [ ] Comentar publicación → notificación llega ✅

## 🆘 Troubleshooting Rápido

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `firebase_push_enabled: false` | Credenciales no configuradas | Ejecutar `setup_firebase_push.sh` |
| "Sin dispositivo activo" | App no registra dispositivo | Implementar paso 3 en App |
| No llega token FCM | Google Play Services desactualizado | Actualizar GPS en móvil |
| Notificación no se muestra | Canal de notificaciones mal | Ver MOBILE_PUSH_SETUP.md línea 180 |

## 📞 Resumen Ejecutivo

```
✅ Backend está 100% listo solo necesita Firebase JSON
❌ App móvil no implementó registro de dispositivo
= Resultado: Push no llega

SOLUCIÓN: 
1. Copiar JSON a EC2
2. Implementar dispositivo registration en App (Kotlin)
3. ¡Profit! 🎉
```

## 📁 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `.env` | Configuración con path Firebase |
| `diagnose_push.py` | Verificar estado del sistema |
| `DEBUG_PUSH.md` | Guía paso a paso |
| `MOBILE_PUSH_SETUP.md` | **MÁS IMPORTANTE - Código Kotlin aquí** |
| `setup_firebase_push.sh` | Setup automatizado EC2 |
| `queries_push.sql` | Inspeccionar BD |

---

**Última actualización:** 14 de abril 2026
**Status:** 🟢 Backend listo | 🔴 App necesita cambios
