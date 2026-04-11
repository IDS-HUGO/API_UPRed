# Reporte Tecnico API (Soporte Persona 1 y Persona 2)

## Resumen

Este documento describe el soporte backend entregado para la app movil RED-UP, considerando que Persona 1 y Persona 2 estan completadas a nivel funcional.

## Aporte de API a Persona 1

1. Registro y actualizacion de dispositivos/token push:
   - `POST /api/notificaciones/dispositivos`
   - `PUT /api/notificaciones/dispositivos/token`
2. Configuracion remota de notificaciones:
   - `GET /api/notificaciones/configuracion`
   - `PUT /api/notificaciones/configuracion`
3. Sincronizacion de eventos diferidos offline/online:
   - `POST /api/notificaciones/eventos/sync`
4. Cache ligera para resumen de no leidas:
   - `GET /api/notificaciones/resumen`
5. Push de prueba end-to-end:
   - `POST /api/notificaciones/push/test`
6. Push social por nuevo seguidor:
   - Integrado en `POST /api/usuarios/{usuario_id}/seguir`

## Aporte de API a Persona 2

1. Soporte de perfil y seguimiento de usuarios:
   - `POST /api/usuarios/{usuario_id}/seguir`
   - `DELETE /api/usuarios/{usuario_id}/seguir`
   - Endpoints de stats/seguidores/siguiendo
2. Soporte para vistas de publicaciones y comentarios con datos de autor.
3. Flujo de recuperacion de contrasena:
   - `POST /api/auth/forgot-password/request`
   - `POST /api/auth/forgot-password/confirm`

## Arquitectura y decisiones tecnicas

1. Framework: FastAPI + SQLAlchemy.
2. Seguridad: JWT para sesion, hash de contrasenas en backend.
3. Push: Firebase Admin SDK desacoplado por servicio (`services/firebase_push_service.py`).
4. Persistencia de trazabilidad: tabla `auditoria` para eventos de configuracion/sync/recuperacion.

## Estado de integracion

1. Endpoints funcionales y versionados en rama de trabajo.
2. Compatible con flujo WorkManager + Room de la app movil.
3. Preparado para despliegue en EC2 con variable `FIREBASE_SERVICE_ACCOUNT_PATH`.

## Checklist de validacion

1. `python -m py_compile` sin errores en routers y schemas.
2. Registro de token y push test operativo.
3. Flujo de recuperacion de contrasena operativo para consumo movil.
