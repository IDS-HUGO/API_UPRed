# ✅ INSTRUCCIONES DE INSTALACIÓN Y CONFIGURACIÓN - UPRed API

## 🎯 Resumen de Cambios

Tu API ha sido completamente actualizada y ajustada al nuevo esquema de base de datos PostgreSQL. Los cambios incluyen:

### ✨ Nuevas Características
- ✅ Migrado de MySQL a PostgreSQL
- ✅ Sistema completo de estructura académica (sedes, facultades, carreras, cuatrimestres)
- ✅ Sistema de catálogo de correos institucionales (whitelist)
- ✅ Sistema de seguidores entre usuarios
- ✅ Publicaciones con tipos, audiencias, comentarios anidados y reacciones
- ✅ Sistema completo de grupos con membresías y roles
- ✅ Mensajería 1-a-1 y grupal con estados (enviado, entregado, leído)
- ✅ Sistema de notificaciones
- ✅ Auditoría completa del sistema
- ✅ CRUDs completos con funciones de búsqueda para todas las entidades

### 📁 Archivos Actualizados/Creados
- ✅ `config.py` - Configuración para PostgreSQL
- ✅ `models.py` - 20+ modelos nuevos
- ✅ `schemas.py` - Schemas Pydantic actualizados
- ✅ `auth.py` - Sistema de auth actualizado
- ✅ `main.py` - Inclusión de todos los routers
- ✅ `requirements.txt` - Dependencias actualizadas
- ✅ `routers/auth.py` - Auth con catálogo de correos
- ✅ `routers/estructura.py` - CRUD de sedes, facultades, carreras, cuatrimestres
- ✅ `routers/usuarios.py` - CRUD usuarios + seguidores + búsqueda
- ✅ `routers/publicaciones.py` - CRUD completo + comentarios + reacciones + búsqueda
- ✅ `routers/grupos.py` - CRUD grupos + membresías + publicaciones
- ✅ `routers/mensajes.py` - Sistema de mensajería completo
- ✅ `routers/notificaciones.py` - Sistema de notificaciones
- ✅ `.env.example` - Plantilla de variables de entorno
- ✅ `README_NEW.md` - Documentación completa

## 🚀 PASOS PARA EJECUTAR LA API

### 1️⃣ Instalar PostgreSQL

Si no tienes PostgreSQL instalado:

**Windows:**
```bash
# Descargar desde: https://www.postgresql.org/download/windows/
# O usar chocolatey:
choco install postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**Mac:**
```bash
brew install postgresql
```

### 2️⃣ Crear la Base de Datos

Abre pgAdmin o psql y ejecuta:

```sql
CREATE DATABASE upred_db;
```

### 3️⃣ Ejecutar el Script SQL

Ejecuta el script SQL completo que te proporcionaron. Ese script crea:
- Todas las tablas
- Extensiones (citext, pgcrypto)
- Tipos ENUM
- Triggers
- Funciones de negocio
- Índices
- Datos semilla

**Usando psql:**
```bash
psql -U postgres -d upred_db -f ruta/al/script.sql
```

**Usando pgAdmin:**
1. Conecta a la base de datos `upred_db`
2. Abre Query Tool
3. Pega el script SQL completo
4. Ejecuta (F5)

### 4️⃣ Configurar Variables de Entorno

Crea un archivo `.env` copiando `.env.example`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_REAL
DB_NAME=upred_db

SECRET_KEY=genera_una_clave_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

**Generar SECRET_KEY segura:**
```python
# Python
import secrets
print(secrets.token_hex(32))
```

O en terminal:
```bash
openssl rand -hex 32
```

### 5️⃣ Crear Entorno Virtual e Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar
# Windows PowerShell:
venv\Scripts\activate

# Windows CMD:
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 6️⃣ Ejecutar la API

```bash
python main.py
```

O con uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7️⃣ Verificar que funciona

Abre tu navegador en:
- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

## 📊 POBLAR CON DATOS DE PRUEBA

Para probar la API, necesitas agregar correos al catálogo:

```sql
-- Insertar correos de prueba
INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT 
    '20260001@universidad.edu', 
    '20260001', 
    (SELECT id FROM carreras WHERE codigo='SIS' LIMIT 1),
    (SELECT id FROM cuatrimestres WHERE numero=1 LIMIT 1)
ON CONFLICT (correo_institucional) DO NOTHING;

INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT 
    '20260002@universidad.edu', 
    '20260002', 
    (SELECT id FROM carreras WHERE codigo='SIS' LIMIT 1),
    (SELECT id FROM cuatrimestres WHERE numero=2 LIMIT 1)
ON CONFLICT (correo_institucional) DO NOTHING;

INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT 
    'admin@universidad.edu', 
    'ADMIN001', 
    (SELECT id FROM carreras WHERE codigo='SIS' LIMIT 1),
    (SELECT id FROM cuatrimestres WHERE numero=1 LIMIT 1)
ON CONFLICT (correo_institucional) DO NOTHING;
```

## 🧪 PROBAR LA API

### 1. Registrar un usuario

POST http://localhost:8000/api/auth/register

```json
{
  "correo_institucional": "20260001@universidad.edu",
  "password": "Password123!",
  "nombre": "Hugo",
  "apellido_paterno": "Pérez",
  "apellido_materno": "López",
  "fecha_nacimiento": "2002-06-15",
  "telefono": "5551234567"
}
```

### 2. Iniciar sesión

POST http://localhost:8000/api/auth/login

```json
{
  "correo_institucional": "20260001@universidad.edu",
  "password": "Password123!"
}
```

Guarda el `access_token` que recibes.

### 3. Crear una publicación

POST http://localhost:8000/api/publicaciones

Headers: `Authorization: Bearer {tu_token}`

```json
{
  "titulo": "¡Bienvenidos a UPRed!",
  "contenido": "Esta es mi primera publicación en la red social universitaria",
  "audiencia": "general",
  "tipo_publicacion_id": 1,
  "permite_comentarios": true,
  "es_anonima": false
}
```

### 4. Ver el feed

GET http://localhost:8000/api/publicaciones/feed

Headers: `Authorization: Bearer {tu_token}`

## 🔍 ENDPOINTS DISPONIBLES

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Usuario actual

### Estructura Académica
- `GET /api/estructura/sedes` - Listar sedes
- `GET /api/estructura/sedes/buscar` - Buscar sedes
- `POST /api/estructura/sedes` - Crear sede (admin)
- Similar para: facultades, carreras, cuatrimestres

### Usuarios
- `GET /api/usuarios` - Listar usuarios (con filtros)
- `GET /api/usuarios/buscar` - Buscar usuarios
- `GET /api/usuarios/{id}` - Ver perfil
- `PUT /api/usuarios/{id}` - Actualizar perfil
- `POST /api/usuarios/{id}/seguir` - Seguir usuario
- `DELETE /api/usuarios/{id}/seguir` - Dejar de seguir
- `GET /api/usuarios/{id}/seguidores` - Ver seguidores
- `GET /api/usuarios/{id}/siguiendo` - Ver siguiendo
- `GET /api/usuarios/{id}/stats` - Estadísticas

### Publicaciones
- `GET /api/publicaciones` - Listar (con filtros)
- `GET /api/publicaciones/feed` - Feed personalizado
- `GET /api/publicaciones/buscar` - Buscar
- `POST /api/publicaciones` - Crear
- `PUT /api/publicaciones/{id}` - Actualizar
- `DELETE /api/publicaciones/{id}` - Eliminar
- `GET /api/publicaciones/{id}/comentarios` - Ver comentarios
- `POST /api/publicaciones/{id}/comentarios` - Comentar
- `POST /api/publicaciones/{id}/reacciones` - Reaccionar
- `GET /api/publicaciones/reacciones/catalogo` - Ver tipos de reacciones

### Grupos
- `GET /api/grupos` - Listar grupos
- `GET /api/grupos/buscar` - Buscar grupos
- `GET /api/grupos/mis-grupos` - Mis grupos
- `POST /api/grupos` - Crear grupo
- `POST /api/grupos/{id}/unirse` - Unirse
- `GET /api/grupos/{id}/miembros` - Ver miembros
- `GET /api/grupos/{id}/publicaciones` - Ver publicaciones
- `POST /api/grupos/{id}/publicaciones` - Publicar en grupo

### Mensajería
- `GET /api/mensajes/salas` - Mis conversaciones
- `POST /api/mensajes/directo/{usuario_id}` - Enviar mensaje directo
- `POST /api/mensajes/salas/directa/{usuario_id}` - Crear/obtener sala directa
- `GET /api/mensajes/salas/{id}/mensajes` - Ver mensajes
- `POST /api/mensajes/salas/{id}/mensajes` - Enviar mensaje
- `PUT /api/mensajes/mensajes/{id}/leer` - Marcar como leído
- `GET /api/mensajes/no-leidos/count` - Contar no leídos

### Notificaciones
- `GET /api/notificaciones` - Listar
- `GET /api/notificaciones/no-leidas` - No leídas
- `GET /api/notificaciones/count` - Contar no leídas
- `PUT /api/notificaciones/{id}` - Marcar como leída
- `PUT /api/notificaciones/marcar-todas-leidas` - Marcar todas

## 🎨 COLECCIÓN POSTMAN

Crea una colección en Postman con estos endpoints para probar fácilmente.

Variables de entorno en Postman:
- `base_url`: http://localhost:8000
- `token`: (se actualiza después del login)

## ⚠️ NOTAS IMPORTANTES

1. **Catálogo de Correos**: Solo los correos en `catalogo_correos` con `habilitado=true` y `usado=false` pueden registrarse.

2. **Roles**: 
   - Estudiantes: Pueden crear publicaciones, comentar, unirse a grupos
   - Moderadores: Pueden eliminar publicaciones/comentarios inapropiados
   - Administradores: Control total del sistema

3. **Audiencia de Publicaciones**:
   - `general`: Visible para todos
   - `carrera`: Solo visible para usuarios de la carrera especificada

4. **Grupos**:
   - `publico`: Cualquiera puede unirse
   - `privado`: Requiere aprobación del admin/dueño

5. **Mensajes**: Se marcan automáticamente como "entregados" cuando el destinatario los ve.

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "Connection refused" a PostgreSQL
- Verifica que PostgreSQL esté corriendo
- En Windows: Services → PostgreSQL → Start
- En Linux: `sudo systemctl start postgresql`

### Error: "Role 'postgres' does not exist"
Crea el usuario:
```bash
createuser -s postgres
```

### Error: "Database upred_db does not exist"
```bash
createdb upred_db
```

### Error: "Invalid token"
- El token expiró (30 días por defecto)
- Haz login nuevamente

## 📚 RECURSOS ADICIONALES

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Pydantic**: https://docs.pydantic.dev/

## ✅ CHECKLIST DE VERIFICACIÓN

Antes de considerarlo completo, verifica:

- [ ] PostgreSQL instalado y corriendo
- [ ] Base de datos `upred_db` creada
- [ ] Script SQL ejecutado correctamente
- [ ] Archivo `.env` configurado con credenciales reales
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] API ejecutándose sin errores
- [ ] Swagger docs accesibles en /docs
- [ ] Al menos un correo en `catalogo_correos`
- [ ] Registro de usuario exitoso
- [ ] Login exitoso y token recibido
- [ ] Crear publicación funciona
- [ ] Feed personalizado funciona

## 🎉 ¡LISTO!

Tu API está completamente funcional con:
- ✅ Todos los CRUDs implementados
- ✅ Funciones de búsqueda en todos los módulos
- ✅ Sistema de autenticación robusto
- ✅ Validaciones a nivel de BD y aplicación
- ✅ Documentación interactiva
- ✅ Sistema escalable y mantenible

Para cualquier duda, revisa `README_NEW.md` o la documentación en `/docs`.

---

**Desarrollado por:** IDS-HUGO  
**Versión:** 2.0.0  
**Fecha:** 2026-02-25
