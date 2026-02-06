# API Red Social Escolar

API REST completa para una red social escolar organizada por carreras con sistema de autenticación, gestión de usuarios (Alumno, Docente, Administrador) y CRUD de publicaciones.

## 🚀 Características

- ✅ Sistema de autenticación con JWT
- ✅ Tres tipos de usuarios: Alumno, Docente y Administrador
- ✅ Validación de dominios de correo para Alumnos y Docentes
- ✅ CRUD completo de publicaciones
- ✅ Sistema de likes y comentarios
- ✅ Filtrado por carreras
- ✅ Documentación automática con Swagger/OpenAPI
- ✅ Preparado para app móvil con CORS habilitado

## 📋 Requisitos Previos

- Python 3.8+
- MySQL 5.7+
- pip (gestor de paquetes de Python)

## 🔧 Instalación

### 1. Clonar el repositorio o descargar los archivos

### 2. Crear y activar entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

Ejecuta el script SQL para crear la base de datos:

```bash
mysql -u root -p < database_schema.sql
```

O desde MySQL Workbench/phpMyAdmin, ejecuta el contenido de `database_schema.sql`.

### 5. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
copy .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=red_social_escolar

SECRET_KEY=genera_una_clave_secreta_muy_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 6. Ejecutar la aplicación

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación API

Una vez iniciada la aplicación, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Credenciales por Defecto

**Administrador:**
- Email: `admin@escuela.edu.mx`
- Password: `admin123`

⚠️ **IMPORTANTE**: Cambia esta contraseña inmediatamente después del primer inicio de sesión.

## 📁 Estructura del Proyecto

```
API_UPRED/
├── main.py                 # Archivo principal de la aplicación
├── config.py              # Configuración y variables de entorno
├── database.py            # Configuración de la base de datos
├── models.py              # Modelos de SQLAlchemy
├── schemas.py             # Esquemas de Pydantic
├── auth.py                # Sistema de autenticación JWT
├── routers/               # Endpoints de la API
│   ├── __init__.py
│   ├── auth.py           # Login, registro
│   ├── publicaciones.py  # CRUD de publicaciones
│   ├── carreras.py       # Gestión de carreras
│   └── usuarios.py       # Gestión de usuarios
├── database_schema.sql    # Script de creación de BD
├── requirements.txt       # Dependencias Python
├── .env.example          # Ejemplo de variables de entorno
└── README.md             # Este archivo
```

## 🛣️ Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener usuario actual
- `GET /api/auth/dominios-correo` - Listar dominios permitidos

### Publicaciones
- `GET /api/publicaciones` - Listar todas las publicaciones
- `POST /api/publicaciones` - Crear publicación
- `GET /api/publicaciones/{id}` - Obtener publicación
- `PUT /api/publicaciones/{id}` - Actualizar publicación
- `DELETE /api/publicaciones/{id}` - Eliminar publicación
- `POST /api/publicaciones/{id}/like` - Dar like
- `DELETE /api/publicaciones/{id}/like` - Quitar like
- `POST /api/publicaciones/{id}/comentarios` - Crear comentario
- `GET /api/publicaciones/{id}/comentarios` - Listar comentarios

### Carreras
- `GET /api/carreras` - Listar carreras
- `POST /api/carreras` - Crear carrera (Admin)
- `GET /api/carreras/{id}` - Obtener carrera
- `PUT /api/carreras/{id}` - Actualizar carrera (Admin)
- `DELETE /api/carreras/{id}` - Eliminar carrera (Admin)

### Usuarios
- `GET /api/usuarios/me` - Ver mi perfil
- `PUT /api/usuarios/me` - Actualizar mi perfil
- `GET /api/usuarios` - Listar usuarios
- `GET /api/usuarios/{id}` - Obtener usuario
- `DELETE /api/usuarios/{id}` - Desactivar usuario (Admin)
- `POST /api/usuarios/{id}/activar` - Activar usuario (Admin)

## 👥 Tipos de Usuarios

### 1. **Alumno**
- Debe tener un correo con dominio permitido (@alumno.escuela.edu.mx)
- Requiere matrícula
- Debe pertenecer a una carrera
- Puede crear publicaciones, comentar y dar likes

### 2. **Docente**
- Debe tener un correo con dominio permitido (@docente.escuela.edu.mx)
- Requiere número de empleado
- Debe pertenecer a una carrera
- Puede crear publicaciones, comentar y dar likes

### 3. **Administrador**
- Sin restricción de dominio de correo
- Puede gestionar todos los recursos
- Puede activar/desactivar usuarios
- Puede eliminar cualquier publicación o comentario

## 🔒 Seguridad

- Contraseñas hasheadas con bcrypt
- Autenticación con JWT (JSON Web Tokens)
- Validación de dominios de correo para tipos de usuario específicos
- Middleware CORS configurado
- Validación de datos con Pydantic

## 📱 Integración con App Móvil

La API está configurada con CORS habilitado para permitir peticiones desde aplicaciones móviles. 

**Ejemplo de login desde app móvil:**

```javascript
const response = await fetch('http://tu-servidor:8000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'usuario@alumno.escuela.edu.mx',
    password: 'contraseña123'
  })
});

const data = await response.json();
const token = data.access_token;

// Usar el token en peticiones subsecuentes
const publicaciones = await fetch('http://tu-servidor:8000/api/publicaciones', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## 🗄️ Base de Datos

La base de datos incluye las siguientes tablas:

- `usuarios` - Información de usuarios
- `carreras` - Carreras disponibles
- `dominios_correo` - Dominios permitidos por tipo de usuario
- `publicaciones` - Publicaciones de la red social
- `comentarios` - Comentarios en publicaciones
- `likes` - Likes en publicaciones

## 🚀 Despliegue en Producción

Para desplegar en producción:

1. Cambia `DEBUG=False` en `.env`
2. Genera una `SECRET_KEY` segura
3. Configura los orígenes permitidos en CORS (no usar `*`)
4. Usa un servidor WSGI como Gunicorn
5. Configura un proxy reverso (Nginx)
6. Habilita HTTPS

## 🤝 Contribuciones

Este proyecto está listo para usar y puede ser extendido con características adicionales como:

- Upload de imágenes
- Sistema de notificaciones
- Mensajería directa
- Eventos y calendario
- Sistema de grupos por materia
- Búsqueda avanzada

## 📄 Licencia

Este proyecto es de código abierto y está disponible para uso educativo.

## 📧 Soporte

Para dudas o problemas, consulta la documentación en `/docs` o revisa los logs de la aplicación.
