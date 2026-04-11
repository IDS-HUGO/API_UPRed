# FCM Local Checklist (Persona 1)

## Prerrequisitos

1. Archivo de cuenta de servicio Firebase descargado.
2. Variable de entorno en `.env`:
   - `FIREBASE_SERVICE_ACCOUNT_PATH=D:/UNIVERSIDAD/MOVILES/upred-48e2a-firebase-adminsdk-fbsvc-df8fd3a150.json`
3. Dependencias instaladas:
   - `pip install -r requirements.txt`

## Flujo de prueba local

1. Levantar API UPRed.
2. Abrir app Android e iniciar sesion.
3. Verificar en DB tabla `dispositivos_usuario` que exista `token_push` activo para el usuario.
4. Ejecutar endpoint de prueba con token Bearer:
   - `POST /api/notificaciones/push/test`
5. Confirmar recepcion en dispositivo.
6. Tocar notificacion y validar deep link hacia pantalla destino.

## Validacion de sincronizacion

1. Forzar evento diferido en app (login/chat) y revisar `pending_sync_events` en Room.
2. Ejecutar sincronizacion manual desde pantalla `Estado de sincronizacion`.
3. Verificar que API reciba batch en `POST /api/notificaciones/eventos/sync`.
4. Confirmar disminucion de pendientes y actualizacion de `lastSyncAt`.
