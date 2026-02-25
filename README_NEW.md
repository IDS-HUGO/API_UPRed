# UPRed - Red Social Universitaria API

API REST completa desarrollada con FastAPI y PostgreSQL para una red social universitaria.

## 🚀 Características

### Estructura Académica
- **Sedes**: Gestión de campus universitarios
- **Facultades**: Organización por facultades
- **Carreras**: Catálogo de programas académicos
- **Cuatrimestres**: Sistema de períodos académicos

### Sistema de Usuarios
- Registro con validación de correo institucional (whitelist)
- Autenticación JWT con roles (estudiante, moderador, administrador)
- Perfiles de usuario completos
- Sistema de seguidores
- Estados de usuario (activo, suspendido, eliminado)

### Publicaciones
- Feed personalizado por carrera y cuatrimestre
- Tipos de publicación (general, académica, evento, oportunidad)
- Audiencias (general o por carrera)
- Sistema de comentarios con respuestas anidadas
- Reacciones personalizables
- Multimedia (imágenes, archivos, audio)

### Grupos
- Creación y gestión de grupos
- Privacidad (público/privado)
- Roles de miembros (dueño, admin, miembro)
- Solicitudes de membresía
- Publicaciones dentro de grupos

### Mensajería
- Chat directo 1 a 1
- Chat grupal
- Estados de mensaje (enviado, entregado, leído)
- Tipos de mensaje (texto, imagen, archivo, audio, sistema)
- Historial de conversaciones

### Notificaciones
- Sistema de notificaciones en tiempo real
- Contador de no leídas
- Marcado masivo como leídas
- Tipos personalizables

### Auditoría
- Registro de todas las acciones importantes
- Trazabilidad completa del sistema

## 📋 Requisitos Previos

- Python 3.10+
- PostgreSQL 15+
- pip (gestor de paquetes de Python)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/IDS-HUGO/WEBSOCKET_REDUP.git
cd API_UPRed
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

Crea una base de datos PostgreSQL:

```sql
CREATE DATABASE upred_db;
```

Ejecuta el script de esquema completo (proporcionado por el usuario) para crear todas las tablas, funciones, triggers e índices.

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
DB_NAME=upred_db

# JWT
SECRET_KEY=tu_clave_secreta_super_segura_cambiala_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 6. Ejecutar la API

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

Una vez ejecutada la API, accede a la documentación interactiva:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Autenticación

La API utiliza JWT (JSON Web Tokens) para autenticación.

### Registro

```bash
POST /api/auth/register
```

**Nota importante**: Solo se pueden registrar correos que estén en la tabla `catalogo_correos` y tengan `habilitado=true` y `usado=false`.

### Login

```bash
POST /api/auth/login
```

Retorna un token JWT que debe incluirse en las siguientes peticiones:

```
Authorization: Bearer <tu_token_aqui>
```

## 📁 Estructura del Proyecto

```
API_UPRed/
├── main.py                 # Punto de entrada de la aplicación
├── config.py              # Configuración y variables de entorno
├── database.py            # Conexión a base de datos
├── models.py              # Modelos SQLAlchemy
├── schemas.py             # Esquemas Pydantic
├── auth.py                # Autenticación y autorización
├── requirements.txt       # Dependencias
├── .env                   # Variables de entorno (no subir a git)
├── routers/
│   ├── __init__.py
│   ├── auth.py           # Endpoints de autenticación
│   ├── estructura.py     # Sedes, facultades, carreras, cuatrimestres
│   ├── usuarios.py       # Gestión de usuarios y seguidores
│   ├── publicaciones.py  # Publicaciones, comentarios, reacciones
│   ├── grupos.py         # Grupos y membresías
│   ├── mensajes.py       # Sistema de mensajería
│   └── notificaciones.py # Notificaciones
└── database_schema.sql   # Script de creación de BD
```

## 🔐 Roles y Permisos

### Estudiante (estudiante)
- Crear y gestionar sus publicaciones
- Comentar y reaccionar
- Unirse a grupos
- Enviar mensajes
- Seguir a otros usuarios

### Moderador (moderador)
- Todos los permisos de estudiante
- Eliminar publicaciones y comentarios inapropiados
- Gestionar reportes

### Administrador (administrador)
- Todos los permisos del sistema
- Gestionar estructura académica
- Gestionar catálogo de correos
- Suspender/eliminar usuarios
- Acceso completo a auditoría

## 🛠️ Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener usuario actual

### Estructura Académica
- `GET /api/estructura/sedes` - Listar sedes
- `GET /api/estructura/facultades` - Listar facultades
- `GET /api/estructura/carreras` - Listar carreras
- `GET /api/estructura/cuatrimestres` - Listar cuatrimestres

### Usuarios
- `GET /api/usuarios` - Listar usuarios
- `GET /api/usuarios/buscar` - Buscar usuarios
- `POST /api/usuarios/{id}/seguir` - Seguir usuario
- `GET /api/usuarios/{id}/stats` - Estadísticas de usuario

### Publicaciones
- `GET /api/publicaciones/feed` - Feed personalizado
- `POST /api/publicaciones` - Crear publicación
- `GET /api/publicaciones/buscar` - Buscar publicaciones
- `POST /api/publicaciones/{id}/comentarios` - Comentar
- `POST /api/publicaciones/{id}/reacciones` - Reaccionar

### Grupos
- `GET /api/grupos` - Listar grupos
- `POST /api/grupos` - Crear grupo
- `POST /api/grupos/{id}/unirse` - Unirse a grupo
- `GET /api/grupos/{id}/publicaciones` - Ver publicaciones del grupo

### Mensajería
- `GET /api/mensajes/salas` - Listar conversaciones
- `POST /api/mensajes/directo/{usuario_id}` - Enviar mensaje directo
- `GET /api/mensajes/salas/{id}/mensajes` - Ver mensajes
- `POST /api/mensajes/salas/{id}/marcar-leidos` - Marcar como leídos

### Notificaciones
- `GET /api/notificaciones` - Listar notificaciones
- `GET /api/notificaciones/no-leidas` - No leídas
- `PUT /api/notificaciones/marcar-todas-leidas` - Marcar todas como leídas

## 🗄️ Base de Datos

La base de datos incluye:
- 20+ tablas normalizadas
- Triggers para actualización de timestamps
- Funciones de negocio en PostgreSQL
- Validaciones a nivel de base de datos
- Índices optimizados para búsquedas
- Sistema de auditoría completo

### Funciones Principales

```sql
-- Registrar estudiante (valida catálogo)
SELECT fn_registrar_estudiante(...);

-- Crear publicación con validaciones
SELECT fn_crear_publicacion(...);

-- Crear grupo y sala de chat automática
SELECT fn_crear_grupo(...);

-- Enviar mensaje directo
SELECT * FROM fn_enviar_mensaje_directo(...);

-- Enviar mensaje grupal
SELECT * FROM fn_enviar_mensaje_grupal(...);
```

## 🔍 Búsquedas

Todos los endpoints principales incluyen funcionalidad de búsqueda:

- **Usuarios**: Por nombre, apellido, correo, carrera, cuatrimestre
- **Publicaciones**: Por título, contenido, tipo, audiencia
- **Grupos**: Por nombre, descripción, carrera
- **Carreras**: Por código, nombre
- **Facultades**: Por código, nombre
- **Sedes**: Por código, nombre

## 📊 Sistema de Catálogo de Correos

El sistema utiliza una whitelist de correos institucionales. Para registrarse:

1. El correo debe existir en `catalogo_correos`
2. Debe tener `habilitado = true`
3. No debe haber sido usado (`usado = false`)
4. Al registrarse, se marca automáticamente como `usado = true`

Insertar correos al catálogo:

```sql
INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT '20260003@universidad.edu', '20260003', 
       (SELECT id FROM carreras WHERE codigo='SIS'), 
       (SELECT id FROM cuatrimestres WHERE numero=1);
```

## 🚦 Estados HTTP

- `200 OK` - Solicitud exitosa
- `201 Created` - Recurso creado
- `400 Bad Request` - Datos inválidos
- `401 Unauthorized` - No autenticado
- `403 Forbidden` - Sin permisos
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error del servidor

## 🔄 Actualización desde versión anterior

Si tienes una versión anterior de esta API:

1. Haz backup de tu base de datos actual
2. Crea una nueva base de datos PostgreSQL
3. Ejecuta el nuevo script SQL completo
4. Actualiza las dependencias: `pip install -r requirements.txt`
5. Actualiza tu archivo `.env` para PostgreSQL
6. Migra los datos si es necesario

## 📝 Notas de Desarrollo

- La API usa soft deletes (borrado lógico) para usuarios y publicaciones
- Todos los timestamps están en UTC
- Las contraseñas se hashean con bcrypt
- Los tokens JWT expiran en 30 días por defecto
- CORS está habilitado para todos los orígenes (configurar en producción)

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
- Verifica que PostgreSQL esté ejecutándose
- Confirma las credenciales en `.env`
- Verifica que el puerto 5432 esté abierto

### Error de autenticación
- Verifica que el correo esté en `catalogo_correos`
- Confirma que el usuario esté activo
- Revisa que el token JWT no haya expirado

### Error al crear publicación
- Verifica que el tipo de publicación exista
- Si es audiencia 'carrera', debe especificar `carrera_objetivo_id`
- Confirma que el usuario tenga permisos

## 👥 Autores

- Hugo Pérez (IDS-HUGO)

## 📄 Licencia

Este proyecto es de código abierto.

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- SQLAlchemy por el ORM
- PostgreSQL por la robusta base de datos
