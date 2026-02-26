# 📚 MANUAL COMPLETO - API UPRed

**Versión:** 2.0.0  
**Base URL:** `http://localhost:8000`  
**Documentación Interactiva:** `http://localhost:8000/docs` (Swagger UI)

---

## 🔐 AUTENTICACIÓN

### 1. Registrar Usuario
**POST** `/api/auth/register`

```json
{
  "correo_institucional": "20260001@universidad.edu",
  "contrasena": "MiPassword123!",
  "nombre": "Juan",
  "apellido_paterno": "Pérez",
  "apellido_materno": "García",
  "fecha_nacimiento": "2005-03-15",
  "telefono": "5551234567"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "correo_institucional": "20260001@universidad.edu",
  "nombre": "Juan",
  "apellido_paterno": "Pérez",
  "apellido_materno": "García",
  "carrera_id": 1,
  "cuatrimestre_id": 2,
  "rol": "estudiante",
  "estado": "activo",
  "creado_en": "2024-01-15T10:30:00"
}
```

**Errores Comunes:**
- `400`: Correo no está en el catálogo o ya fue usado
- `409`: El correo ya está registrado

---

### 2. Iniciar Sesión
**POST** `/api/auth/login`

```json
{
  "correo_institucional": "20260001@universidad.edu",
  "contrasena": "MiPassword123!"
}
```

**Respuesta Exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "correo_institucional": "20260001@universidad.edu",
    "nombre": "Juan",
    "apellido_paterno": "Pérez",
    "carrera_id": 1,
    "rol": "estudiante"
  }
}
```

**Uso del Token:**
Incluir en todas las peticiones protegidas:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### 3. Obtener Perfil Actual
**GET** `/api/auth/me`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
{
  "id": 1,
  "correo_institucional": "20260001@universidad.edu",
  "nombre": "Juan",
  "apellido_paterno": "Pérez",
  "apellido_materno": "García",
  "fecha_nacimiento": "2005-03-15",
  "telefono": "5551234567",
  "carrera_id": 1,
  "cuatrimestre_id": 2,
  "biografia": null,
  "foto_perfil_url": null,
  "rol": "estudiante",
  "estado": "activo",
  "creado_en": "2024-01-15T10:30:00"
}
```

---

## 📝 PUBLICACIONES

### 4. Crear Publicación
**POST** `/api/publicaciones/`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "titulo": "Ayuda con cálculo integral",
  "contenido": "¿Alguien entiende las integrales por sustitución? Tengo examen mañana 😅",
  "tipo_publicacion_id": 5,
  "audiencia": "general",
  "permite_comentarios": true,
  "es_anonima": false
}
```

**Publicación para una Carrera Específica:**
```json
{
  "titulo": "Proyecto de Base de Datos",
  "contenido": "¿Quién quiere formar equipo para el proyecto final?",
  "tipo_publicacion_id": 2,
  "audiencia": "carrera",
  "carrera_objetivo_id": 1,
  "permite_comentarios": true,
  "es_anonima": false
}
```

**Respuesta (201):**
```json
{
  "id": 10,
  "autor_id": 1,
  "titulo": "Ayuda con cálculo integral",
  "contenido": "¿Alguien entiende las integrales por sustitución?",
  "tipo_publicacion_id": 5,
  "audiencia": "general",
  "permite_comentarios": true,
  "es_anonima": false,
  "activa": true,
  "publicada_en": "2024-01-15T14:20:00",
  "autor": {
    "id": 1,
    "nombre": "Juan",
    "apellido_paterno": "Pérez"
  }
}
```

---

### 5. Obtener Feed de Publicaciones
**GET** `/api/publicaciones/feed?skip=0&limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
[
  {
    "id": 15,
    "titulo": "Conferencia sobre IA",
    "contenido": "Mañana habrá conferencia sobre inteligencia artificial",
    "autor": {
      "id": 2,
      "nombre": "María",
      "apellido_paterno": "López",
      "foto_perfil_url": null
    },
    "tipo_publicacion_id": 3,
    "audiencia": "general",
    "publicada_en": "2024-01-15T15:00:00",
    "permite_comentarios": true,
    "es_anonima": false,
    "total_comentarios": 5,
    "total_reacciones": 12
  }
]
```

---

### 6. Publicaciones Recientes
**GET** `/api/publicaciones/recientes?limit=10`

**Headers:**
```
Authorization: Bearer {token}
```

**Descripción:** Obtiene las publicaciones más recientes ordenadas por fecha.

**Respuesta (200):** Array de publicaciones ordenadas por `publicada_en DESC`

---

### 7. Publicaciones por Carrera
**GET** `/api/publicaciones/por-carrera/{carrera_id}?skip=0&limit=20`

**Ejemplo:** `/api/publicaciones/por-carrera/1?limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

**Descripción:** Filtra publicaciones dirigidas a una carrera específica o públicas para todos.

**Respuesta (200):** Array de publicaciones de la carrera solicitada

---

### 8. Publicaciones Populares
**GET** `/api/publicaciones/populares?limit=10`

**Headers:**
```
Authorization: Bearer {token}
```

**Descripción:** Obtiene publicaciones ordenadas por popularidad (reacciones + comentarios).

**Respuesta (200):**
```json
[
  {
    "id": 20,
    "titulo": "Fiesta de fin de cuatrimestre",
    "contenido": "¡Los invito a todos!",
    "popularidad": 45,
    "total_reacciones": 30,
    "total_comentarios": 15,
    "publicada_en": "2024-01-14T18:00:00"
  }
]
```

---

### 9. Mis Publicaciones
**GET** `/api/publicaciones/mis-publicaciones?skip=0&limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

**Descripción:** Obtiene todas las publicaciones del usuario autenticado.

**Respuesta (200):** Array de publicaciones del usuario

---

### 10. Buscar Publicaciones
**GET** `/api/publicaciones/buscar?q=calculo&skip=0&limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

**Parámetros:**
- `q`: Término de búsqueda (busca en título y contenido)
- `skip`: Número de resultados a omitir (paginación)
- `limit`: Máximo de resultados a retornar

---

### 11. Obtener Publicación por ID
**GET** `/api/publicaciones/{id}`

**Ejemplo:** `/api/publicaciones/10`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
{
  "id": 10,
  "titulo": "Ayuda con cálculo integral",
  "contenido": "¿Alguien entiende las integrales por sustitución?",
  "autor": {
    "id": 1,
    "nombre": "Juan",
    "apellido_paterno": "Pérez"
  },
  "tipo_publicacion_id": 5,
  "publicada_en": "2024-01-15T14:20:00",
  "comentarios": [
    {
      "id": 1,
      "contenido": "Yo te puedo ayudar",
      "usuario": {
        "id": 2,
        "nombre": "María"
      },
      "creado_en": "2024-01-15T14:25:00"
    }
  ],
  "reacciones": [
    {
      "usuario_id": 3,
      "reaccion_codigo": "apoyo"
    }
  ]
}
```

---

### 12. Actualizar Publicación
**PUT** `/api/publicaciones/{id}`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "titulo": "Ayuda con cálculo integral (URGENTE)",
  "contenido": "¿Alguien entiende las integrales por sustitución? Tengo examen mañana 😅",
  "permite_comentarios": true
}
```

**Respuesta (200):** Publicación actualizada

---

### 13. Eliminar Publicación
**DELETE** `/api/publicaciones/{id}`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (204):** Sin contenido (eliminación exitosa)

---

### 14. Comentar Publicación
**POST** `/api/publicaciones/{id}/comentarios`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "contenido": "Yo te puedo explicar, escríbeme al privado"
}
```

**Respuesta (201):**
```json
{
  "id": 5,
  "publicacion_id": 10,
  "usuario_id": 2,
  "contenido": "Yo te puedo explicar, escríbeme al privado",
  "creado_en": "2024-01-15T14:30:00"
}
```

---

### 15. Reaccionar a Publicación
**POST** `/api/publicaciones/{id}/reaccionar`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "reaccion_id": 1
}
```

**Códigos de Reacción:**
- `1`: me_gusta
- `2`: me_encanta
- `3`: interesante
- `4`: apoyo
- `5`: felicidades

**Respuesta (201):**
```json
{
  "mensaje": "Reacción registrada exitosamente",
  "reaccion": {
    "publicacion_id": 10,
    "usuario_id": 1,
    "reaccion_id": 1
  }
}
```

---

## 👥 USUARIOS

### 16. Obtener Perfil de Usuario
**GET** `/api/usuarios/{id}`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
{
  "id": 2,
  "nombre": "María",
  "apellido_paterno": "López",
  "apellido_materno": "Martínez",
  "correo_institucional": "20260002@universidad.edu",
  "biografia": "Estudiante de medicina apasionada por la neurología",
  "foto_perfil_url": null,
  "carrera": {
    "id": 3,
    "nombre": "Medicina"
  },
  "cuatrimestre": {
    "id": 3,
    "numero": 3
  },
  "total_seguidores": 45,
  "total_seguidos": 30,
  "total_publicaciones": 12
}
```

---

### 17. Actualizar Perfil
**PUT** `/api/usuarios/perfil`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "nombre": "Juan Carlos",
  "apellido_materno": "García",
  "telefono": "5559876543",
  "biografia": "Estudiante de sistemas, me gusta programar en Python 🐍"
}
```

---

### 18. Seguir Usuario
**POST** `/api/usuarios/{id}/seguir`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (201):**
```json
{
  "mensaje": "Ahora sigues a María López",
  "seguidor_id": 1,
  "seguido_id": 2
}
```

---

### 19. Dejar de Seguir
**DELETE** `/api/usuarios/{id}/seguir`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (204):** Sin contenido

---

### 20. Obtener Seguidores
**GET** `/api/usuarios/{id}/seguidores?skip=0&limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
[
  {
    "id": 3,
    "nombre": "Carlos",
    "apellido_paterno": "Ramírez",
    "foto_perfil_url": null,
    "carrera": {
      "nombre": "Ingeniería Industrial"
    }
  }
]
```

---

### 21. Obtener Seguidos
**GET** `/api/usuarios/{id}/seguidos?skip=0&limit=20`

Similar a "Obtener Seguidores"

---

## 🏛️ ESTRUCTURA ACADÉMICA

### 22. Obtener Todas las Sedes
**GET** `/api/estructura/sedes`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "codigo": "MAIN",
    "nombre": "Campus Principal",
    "ciudad": "Ciudad Universitaria"
  }
]
```

---

### 23. Obtener Facultades
**GET** `/api/estructura/facultades`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "codigo": "ING",
    "nombre": "Facultad de Ingeniería",
    "sede_id": 1
  },
  {
    "id": 2,
    "codigo": "SAL",
    "nombre": "Facultad de Ciencias de la Salud",
    "sede_id": 1
  }
]
```

---

### 24. Obtener Carreras
**GET** `/api/estructura/carreras`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "codigo": "SIS",
    "nombre": "Ingeniería de Sistemas",
    "facultad_id": 1,
    "activa": true
  },
  {
    "id": 3,
    "codigo": "MED",
    "nombre": "Medicina",
    "facultad_id": 2,
    "activa": true
  }
]
```

---

### 25. Obtener Carreras por Facultad
**GET** `/api/estructura/facultades/{facultad_id}/carreras`

**Ejemplo:** `/api/estructura/facultades/1/carreras`

---

### 26. Obtener Cuatrimestres
**GET** `/api/estructura/cuatrimestres`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "numero": 1,
    "descripcion": "Primer cuatrimestre",
    "activo": true
  },
  {
    "id": 2,
    "numero": 2,
    "descripcion": "Segundo cuatrimestre",
    "activo": true
  }
]
```

---

## 👥 GRUPOS

### 27. Crear Grupo
**POST** `/api/grupos/`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "nombre": "Estudio de Cálculo",
  "descripcion": "Grupo para estudiar cálculo integral y diferencial",
  "carrera_id": 1,
  "privacidad": "publico"
}
```

**Privacidad:**
- `publico`: Cualquiera puede unirse
- `privado`: Se requiere aprobación

**Respuesta (201):**
```json
{
  "id": 5,
  "nombre": "Estudio de Cálculo",
  "descripcion": "Grupo para estudiar cálculo integral y diferencial",
  "carrera_id": 1,
  "privacidad": "publico",
  "usuario_dueno_id": 1,
  "creado_en": "2024-01-15T16:00:00",
  "total_miembros": 1
}
```

---

### 28. Listar Grupos
**GET** `/api/grupos/?skip=0&limit=20`

**Headers:**
```
Authorization: Bearer {token}
```

---

### 29. Unirse a Grupo
**POST** `/api/grupos/{id}/unirse`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (201):**
```json
{
  "mensaje": "Te has unido al grupo exitosamente",
  "grupo_id": 5,
  "usuario_id": 2,
  "rol_miembro": "miembro"
}
```

---

### 30. Salir de Grupo
**DELETE** `/api/grupos/{id}/salir`

**Headers:**
```
Authorization: Bearer {token}
```

---

### 31. Publicar en Grupo
**POST** `/api/grupos/{id}/publicaciones`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "titulo": "Resumen del tema 5",
  "contenido": "Aquí les comparto mi resumen del último tema visto"
}
```

---

## 💬 MENSAJERÍA (REST)

### 32. Enviar Mensaje Directo
**POST** `/api/mensajes/enviar`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "destinatario_id": 2,
  "contenido": "Hola, ¿te puedo hacer una pregunta sobre la tarea?",
  "tipo_mensaje": "texto"
}
```

**Respuesta (201):**
```json
{
  "id": 100,
  "mensaje_uuid": "a3b4c5d6-e7f8-9012-3456-789012345678",
  "sala_chat_id": 10,
  "remitente_id": 1,
  "contenido": "Hola, ¿te puedo hacer una pregunta sobre la tarea?",
  "tipo_mensaje": "texto",
  "enviado_en": "2024-01-15T17:00:00"
}
```

---

### 33. Obtener Conversaciones
**GET** `/api/mensajes/conversaciones`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
[
  {
    "sala_chat_id": 10,
    "tipo_sala": "directo",
    "otro_usuario": {
      "id": 2,
      "nombre": "María",
      "apellido_paterno": "López",
      "foto_perfil_url": null
    },
    "ultimo_mensaje": {
      "contenido": "Hola, ¿te puedo hacer una pregunta?",
      "enviado_en": "2024-01-15T17:00:00"
    },
    "mensajes_no_leidos": 2
  }
]
```

---

### 34. Obtener Historial de Chat
**GET** `/api/mensajes/sala/{sala_id}?skip=0&limit=50`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
[
  {
    "id": 100,
    "remitente": {
      "id": 1,
      "nombre": "Juan"
    },
    "contenido": "Hola, ¿te puedo hacer una pregunta?",
    "tipo_mensaje": "texto",
    "enviado_en": "2024-01-15T17:00:00",
    "leido_en": null
  },
  {
    "id": 101,
    "remitente": {
      "id": 2,
      "nombre": "María"
    },
    "contenido": "Claro, dime",
    "tipo_mensaje": "texto",
    "enviado_en": "2024-01-15T17:01:00",
    "leido_en": "2024-01-15T17:02:00"
  }
]
```

---

### 35. Marcar Mensajes como Leídos
**PUT** `/api/mensajes/sala/{sala_id}/leer`

**Headers:**
```
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
{
  "mensaje": "Mensajes marcados como leídos",
  "mensajes_actualizados": 3
}
```

---

## 🔔 NOTIFICACIONES

### 36. Obtener Notificaciones
**GET** `/api/notificaciones/?skip=0&limit=20&solo_no_leidas=false`

**Headers:**
```
Authorization: Bearer {token}
```

**Parámetros:**
- `skip`: Paginación
- `limit`: Cantidad de resultados
- `solo_no_leidas`: `true` para filtrar solo no leídas

**Respuesta (200):**
```json
[
  {
    "id": 50,
    "tipo": "nueva_reaccion",
    "titulo": "Nueva reacción en tu publicación",
    "cuerpo": "A María le gustó tu publicación 'Ayuda con cálculo'",
    "datos": {
      "publicacion_id": 10,
      "usuario_id": 2
    },
    "leida": false,
    "creada_en": "2024-01-15T18:00:00"
  }
]
```

---

### 37. Marcar Notificación como Leída
**PUT** `/api/notificaciones/{id}/leer`

**Headers:**
```
Authorization: Bearer {token}
```

---

### 38. Marcar Todas como Leídas
**PUT** `/api/notificaciones/leer-todas`

**Headers:**
```
Authorization: Bearer {token}
```

---

## 🚀 WebSocket - Mensajería en Tiempo Real

**URL del servidor:** `ws://localhost:5000/`  
**Librería recomendada:** Socket.IO Client

### Conectarse al WebSocket

```javascript
const socket = io('http://localhost:5000', {
  auth: {
    token: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  }
});
```

### Eventos que puedes emitir:

#### Unirse a una sala
```javascript
socket.emit('unirse_sala', {
  sala_uuid: 'a3b4c5d6-e7f8-9012-3456-789012345678'
});
```

#### Enviar mensaje
```javascript
socket.emit('enviar_mensaje', {
  sala_uuid: 'a3b4c5d6-e7f8-9012-3456-789012345678',
  contenido: 'Hola en tiempo real!',
  tipo_mensaje: 'texto'
});
```

#### Marcar como leído
```javascript
socket.emit('marcar_leido', {
  mensaje_uuid: 'b1c2d3e4-f5a6-7890-1234-567890abcdef'
});
```

### Eventos que recibirás:

#### Mensaje nuevo
```javascript
socket.on('nuevo_mensaje', (data) => {
  console.log('Mensaje recibido:', data);
  // {
  //   mensaje_uuid: '...',
  //   sala_uuid: '...',
  //   remitente_id: 2,
  //   contenido: 'Hola!',
  //   enviado_en: '2024-01-15T19:00:00'
  // }
});
```

#### Confirmación de leído
```javascript
socket.on('mensaje_leido', (data) => {
  console.log('Mensaje leído por:', data.leido_por_usuario_id);
});
```

#### Usuario escribiendo...
```javascript
socket.on('usuario_escribiendo', (data) => {
  console.log(`${data.usuario_id} está escribiendo...`);
});
```

---

## 📌 NOTAS IMPORTANTES

### Autenticación
- Todos los endpoints (excepto `/register` y `/login`) requieren token JWT
- El token se envía en el header: `Authorization: Bearer {token}`
- Los tokens expiran después de 7 días (configurable en `.env`)

### Paginación
- La mayoría de los endpoints aceptan `skip` y `limit`
- Valores por defecto: `skip=0`, `limit=20`
- Máximo permitido: `limit=100`

### Errores Comunes

**401 Unauthorized:**
```json
{
  "detail": "No autenticado"
}
```

**403 Forbidden:**
```json
{
  "detail": "No tienes permisos para realizar esta acción"
}
```

**404 Not Found:**
```json
{
  "detail": "Recurso no encontrado"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "correo_institucional"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔧 Variables de Entorno Requeridas

Crear archivo `.env`:

```env
# Base de datos MySQL
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/upred_db

# JWT Secret (cambiar en producción)
SECRET_KEY=tu_clave_secreta_super_segura_cambiar_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Entorno
ENVIRONMENT=development
```

---

## 📦 Instalación Rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# 3. Crear base de datos
mysql -u root -p < setup_database.sql

# 4. Iniciar API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Iniciar WebSocket (en otra terminal)
python websocket_server.py
```

---

## 🌐 Endpoints de Documentación

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

**¡Listo para usar!** 🚀
