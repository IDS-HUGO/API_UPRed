# 🎓 API UPRed - Red Social Universitaria

**Versión 2.0.0** - API REST completa con MySQL y WebSocket para mensajería en tiempo real

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg)](https://www.mysql.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)](https://www.python.org/)

Red social universitaria completa con gestión académica, publicaciones, grupos, mensajería en tiempo real y notificaciones. **100% migrado a MySQL** sin dependencias externas para almacenamiento de archivos.

---

## ✨ Características Principales

### 🔐 Autenticación y Seguridad
- ✅ Registro validado con catálogo de correos institucionales (whitelist)
- ✅ Login con JWT (tokens válidos por 7 días)
- ✅ Sistema de roles (estudiante, moderador, administrador)
- ✅ Endpoints compatibles con OAuth2

### 📚 Estructura Académica Completa
- ✅ Gestión de sedes, facultades, carreras y cuatrimestres
- ✅ Perfiles de usuario vinculados a carrera y cuatrimestre
- ✅ Filtrado de contenido por audiencia académica

### 📝 Publicaciones con Filtros Avanzados
- ✅ CRUD completo de publicaciones
- ✅ 6 tipos: general, académica, evento, oportunidad, pregunta, debate
- ✅ **Filtros especiales:**
  - 🔥 **Recientes**: Últimas publicaciones ordenadas por fecha
  - 🎯 **Por carrera**: Contenido específico de tu carrera
  - ⭐ **Populares**: Más comentadas y reaccionadas
  - 👤 **Mis publicaciones**: Tu contenido personal
- ✅ Sistema de comentarios anidados
- ✅ 5 tipos de reacciones (me gusta, me encanta, interesante, apoyo, felicidades)
- ✅ Búsqueda por texto en título y contenido
- ✅ Almacenamiento de imágenes como BLOB (hasta 16MB)

### 👥 Funcionalidades Sociales
- ✅ Sistema de seguidores/seguidos
- ✅ Feed personalizado
- ✅ Grupos públicos y privados por carrera
- ✅ Roles de grupo (dueño, admin, miembro)

### 💬 Mensajería Completa
- ✅ **REST API**: Mensajes directos con historial
- ✅ **WebSocket (Socket.IO)**: Chat en tiempo real
- ✅ Salas 1 a 1 y grupales
- ✅ Indicadores de entregado y leído
- ✅ Evento "usuario escribiendo..."

### 🔔 Sistema de Notificaciones
- ✅ Notificaciones en tiempo real
- ✅ Tipos: nueva reacción, comentario, seguidor, mensaje
- ✅ Marcado de leído individual o masivo

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework Web | FastAPI | 0.109.0 |
| Base de Datos | MySQL | 8.0+ |
| ORM | SQLAlchemy | 2.0.25 |
| Driver MySQL | pymysql | 1.1.0 |
| WebSocket | Flask-SocketIO | 5.3.5 |
| Concurrencia WS | eventlet | 0.35.1 |
| Autenticación | python-jose[cryptography] | 3.3.0 |
| Hashing | passlib[bcrypt] | 1.7.4 |
| Validación | pydantic | 2.5.3 |

---

## ⚡ Instalación Rápida

### 1️⃣ Clonar el repositorio
```bash
git clone <tu-repo>
cd API_UPRed
```

### 2️⃣ Instalar dependencias
```bash
# Dependencias principales
pip install -r requirements.txt

# Dependencias para WebSocket
pip install -r requirements_websocket.txt
```

### 3️⃣ Crear base de datos MySQL
```bash
# Opción 1: Desde MySQL CLI
mysql -u root -p < setup_database.sql

# Opción 2: Desde MySQL Workbench
# Abrir y ejecutar setup_database.sql
```

Este script creará:
- Base de datos `upred_db`
- 30+ tablas con relaciones
- Datos semilla (sedes, facultades, carreras, cuatrimestres)
- 4 correos de prueba en el catálogo

### 4️⃣ Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos MySQL
DATABASE_URL=mysql+pymysql://root:tu_password@localhost:3306/upred_db

# JWT Configuration
SECRET_KEY=cambia_esto_por_una_clave_super_secreta_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Entorno
ENVIRONMENT=development
```

### 5️⃣ Ejecutar la API
```bash
# Modo desarrollo (con recarga automática)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API disponible en:** `http://localhost:8000`  
**Documentación Swagger:** `http://localhost:8000/docs`  
**Documentación ReDoc:** `http://localhost:8000/redoc`

### 6️⃣ Ejecutar servidor WebSocket (opcional)
```bash
python websocket_server.py
```

**WebSocket disponible en:** `http://localhost:5000`

---

## 📖 Documentación de la API

### 📘 Manual Completo
Consulta [MANUAL_API.md](MANUAL_API.md) para:
- ✅ Todos los endpoints con ejemplos
- ✅ JSON de request/response completos
- ✅ Códigos de error y soluciones
- ✅ Guía de WebSocket con ejemplos de código
- ✅ 38+ ejemplos de uso listos para copiar

### 🌐 Documentación Interactiva

#### Swagger UI (`/docs`)
Interfaz interactiva para probar todos los endpoints:
- Ejecutar peticiones directamente desde el navegador
- Ver esquemas de datos automáticamente
- Autenticación integrada con botón "Authorize"

#### ReDoc (`/redoc`)
Documentación limpia y organizada:
- Vista de lectura optimizada
- Búsqueda rápida de endpoints
- Exportación de OpenAPI spec

---

## 🗄️ Estructura de la Base de Datos

### Tablas Principales

**Estructura Académica:**
- `sedes` - Campus universitarios
- `facultades` - Facultades por sede
- `carreras` - Carreras por facultad
- `cuatrimestres` - Periodos académicos

**Usuarios y Catálogo:**
- `catalogo_correos` - Whitelist de correos institucionales ✅
- `usuarios` - Estudiantes registrados
- `dispositivos_usuario` - Dispositivos para push notifications
- `seguidores` - Relaciones de seguimiento

**Publicaciones:**
- `tipos_publicacion` - Catálogo de tipos
- `publicaciones` - Contenido principal
- `multimedia_publicacion` - Archivos adjuntos (BLOB)
- `comentarios_publicacion` - Comentarios anidados
- `catalogo_reacciones` - Tipos de reacciones
- `reacciones_publicacion` - Reacciones de usuarios

**Grupos:**
- `grupos` - Comunidades estudiantiles
- `miembros_grupo` - Membresía con roles
- `publicaciones_grupo` - Contenido del grupo

**Mensajería:**
- `salas_chat` - Salas 1 a 1 y grupales
- `mensajes` - Mensajes con BLOB para archivos
- `destinatarios_mensaje` - Control de entrega/lectura

**Sistema:**
- `notificaciones` - Notificaciones push
- `auditoria` - Registro de acciones

### Diagrama ER
```
sedes → facultades → carreras → catalogo_correos → usuarios
                                                        ↓
                                    publicaciones ← comentarios
                                          ↓           ↓
                                    reacciones    seguidores
                                    
usuarios → grupos ← miembros_grupo → publicaciones_grupo

usuarios → salas_chat ← mensajes → destinatarios_mensaje
```

---

## 🚦 Uso Básico

### Registro de Usuario
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "correo_institucional": "20260001@universidad.edu",
    "contrasena": "MiPassword123!",
    "nombre": "Juan",
    "apellido_paterno": "Pérez",
    "apellido_materno": "García",
    "fecha_nacimiento": "2005-03-15"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo_institucional": "20260001@universidad.edu",
    "contrasena": "MiPassword123!"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Crear Publicación (autenticado)
```bash
curl -X POST http://localhost:8000/api/publicaciones/ \
  -H "Authorization: Bearer {tu_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Ayuda con cálculo",
    "contenido": "¿Alguien entiende las integrales?",
    "tipo_publicacion_id": 5,
    "audiencia": "general"
  }'
```

### Ver Publicaciones Populares
```bash
curl http://localhost:8000/api/publicaciones/populares?limit=10 \
  -H "Authorization: Bearer {tu_token}"
```

---

## 📁 Estructura del Proyecto

```
API_UPRed/
├── main.py                      # Punto de entrada FastAPI
├── config.py                    # Configuración (DB, JWT, etc.)
├── database.py                  # Conexión SQLAlchemy
├── models.py                    # Modelos ORM (25+ tablas)
├── schemas.py                   # Schemas Pydantic
├── auth.py                      # Utilidades de autenticación
├── websocket_server.py          # Servidor Socket.IO
├── setup_database.sql           # Script completo de BD
├── requirements.txt             # Dependencias API
├── requirements_websocket.txt   # Dependencias WebSocket
├── .env.example                 # Template de variables
├── MANUAL_API.md                # 📘 Manual completo con 38 ejemplos
├── README.md                    # Este archivo
└── routers/
    ├── __init__.py
    ├── auth.py                  # Login, registro, perfil
    ├── estructura.py            # Sedes, facultades, carreras
    ├── usuarios.py              # Perfiles, seguir/dejar seguir
    ├── publicaciones.py         # CRUD + filtros avanzados ⭐
    ├── grupos.py                # Grupos y membresías
    ├── mensajes.py              # Mensajería REST
    └── notificaciones.py        # Notificaciones push
```

---

## 🔑 Correos de Prueba

El script `setup_database.sql` incluye estos correos en el catálogo:

| Correo | Carrera | Cuatrimestre |
|--------|---------|--------------|
| `20260001@universidad.edu` | Ingeniería de Sistemas | 2 |
| `20260002@universidad.edu` | Medicina | 3 |
| `20260003@universidad.edu` | Ingeniería Industrial | 4 |
| `admin@universidad.edu` | Ingeniería de Sistemas | 1 |

**Contraseña sugerida para pruebas:** `Test123!`

---

## 🐛 Solución de Problemas

### Error: "Could not connect to MySQL"
```bash
# Verificar que MySQL está corriendo
# Windows:
net start MySQL80

# Linux/Mac:
sudo systemctl start mysql
```

### Error: "Access denied for user"
Revisa las credenciales en tu archivo `.env`:
```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/upred_db
```

### Error: "Table doesn't exist"
Ejecuta el script de base de datos:
```bash
mysql -u root -p < setup_database.sql
```

### Error: "Correo no está en el catálogo"
Añade correos manualmente:
```sql
INSERT INTO catalogo_correos (correo_institucional, carrera_id, cuatrimestre_id)
VALUES ('nuevo@universidad.edu', 1, 1);
```

---

## 📊 Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Perfil actual

### Publicaciones
- `GET /api/publicaciones/feed` - Feed general
- `GET /api/publicaciones/recientes` - ⏰ Últimas publicaciones
- `GET /api/publicaciones/por-carrera/{id}` - 🎯 Filtrar por carrera
- `GET /api/publicaciones/populares` - ⭐ Más populares
- `GET /api/publicaciones/mis-publicaciones` - 👤 Mis posts
- `POST /api/publicaciones/` - Crear publicación
- `POST /api/publicaciones/{id}/comentarios` - Comentar
- `POST /api/publicaciones/{id}/reaccionar` - Reaccionar

### Usuarios
- `GET /api/usuarios/{id}` - Ver perfil
- `POST /api/usuarios/{id}/seguir` - Seguir usuario
- `GET /api/usuarios/{id}/seguidores` - Ver seguidores

### Grupos
- `GET /api/grupos/` - Listar grupos
- `POST /api/grupos/` - Crear grupo
- `POST /api/grupos/{id}/unirse` - Unirse a grupo

### Mensajería
- `POST /api/mensajes/enviar` - Enviar mensaje
- `GET /api/mensajes/conversaciones` - Ver chats
- `GET /api/mensajes/sala/{id}` - Historial de chat

### Notificaciones
- `GET /api/notificaciones/` - Ver notificaciones
- `PUT /api/notificaciones/{id}/leer` - Marcar como leída

**Ver todos los endpoints:** [MANUAL_API.md](MANUAL_API.md)

---

## 🚀 Deploy en Producción

### Configuración recomendada

**API:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**WebSocket:**
```bash
gunicorn --worker-class eventlet -w 1 websocket_server:app -b 0.0.0.0:5000
```

### Consideraciones de seguridad

1. **Cambiar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Usar HTTPS:** Configurar SSL/TLS con nginx o Apache

3. **Restringir CORS:**
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-dominio.com"],  # No usar "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

4. **Variables de entorno en producción:**
```env
ENVIRONMENT=production
DATABASE_URL=mysql+pymysql://user:pass@mysql-server:3306/upred_db
```

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 👨‍💻 Soporte

- **Documentación completa:** [MANUAL_API.md](MANUAL_API.md)
- **Swagger UI:** http://localhost:8000/docs
- **Issues:** Reporta problemas en el repositorio

---

**Desarrollado con ❤️ usando FastAPI y MySQL**
