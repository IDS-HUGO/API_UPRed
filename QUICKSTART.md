# 🚀 Guía Rápida de Inicio

## Instalación Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar MySQL
Ejecuta `database_schema.sql` en MySQL:
```bash
mysql -u root -p < database_schema.sql
```

### 3. Configurar .env
Copia `.env.example` a `.env` y edita tus credenciales de MySQL:
```bash
copy .env.example .env
```

### 4. Ejecutar API
```bash
python main.py
```

## 🔑 Credenciales por Defecto

**Admin:**
- Email: admin@escuela.edu.mx
- Password: admin123

## 📚 Acceder a la Documentación

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Probar la API

### Registrar un alumno:
```bash
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@alumno.escuela.edu.mx",
  "password": "password123",
  "tipo_usuario": "ALUMNO",
  "carrera_id": 1,
  "matricula": "A12345"
}
```

### Login:
```bash
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "juan@alumno.escuela.edu.mx",
  "password": "password123"
}
```

### Crear publicación (con token):
```bash
POST http://localhost:8000/api/publicaciones
Authorization: Bearer TU_TOKEN_AQUI
Content-Type: application/json

{
  "titulo": "Mi primera publicación",
  "contenido": "Hola a todos!",
  "tipo_publicacion": "GENERAL",
  "carrera_id": 1
}
```

## 📱 Dominios de Correo Permitidos

### Alumnos:
- @alumno.escuela.edu.mx
- @estudiante.escuela.edu.mx

### Docentes:
- @docente.escuela.edu.mx
- @profesor.escuela.edu.mx

## 🎯 Endpoints Principales

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register | Registro | No |
| POST | /api/auth/login | Login | No |
| GET | /api/auth/me | Perfil actual | Sí |
| GET | /api/publicaciones | Listar publicaciones | Sí |
| POST | /api/publicaciones | Crear publicación | Sí |
| GET | /api/publicaciones/{id} | Ver publicación | Sí |
| PUT | /api/publicaciones/{id} | Actualizar publicación | Sí |
| DELETE | /api/publicaciones/{id} | Eliminar publicación | Sí |
| POST | /api/publicaciones/{id}/like | Dar like | Sí |
| GET | /api/carreras | Listar carreras | No |

## 🛠️ Tipos de Usuario

- **ALUMNO**: Requiere matrícula y dominio de alumno
- **DOCENTE**: Requiere número de empleado y dominio de docente
- **ADMINISTRADOR**: Sin restricciones de dominio

## 💡 Tips

1. Usa la documentación automática en `/docs` para probar endpoints
2. El token expira en 30 minutos (configurable en `.env`)
3. Todos los endpoints excepto registro, login y listar carreras requieren autenticación
4. Las publicaciones se pueden filtrar por carrera: `GET /api/publicaciones?carrera_id=1`

## ❓ Problemas Comunes

**Error de conexión a MySQL:**
- Verifica que MySQL esté corriendo
- Revisa las credenciales en `.env`

**Error "email already registered":**
- El correo ya existe en la base de datos

**Error 401 Unauthorized:**
- Token expirado o inválido
- Haz login nuevamente para obtener un nuevo token

**Error 403 Forbidden:**
- No tienes permisos para esa acción
- Verifica el tipo de usuario requerido
