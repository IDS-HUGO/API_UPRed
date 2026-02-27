# Test API Publicaciones - RED UP

## Pasos para probar la API:

### 1. Iniciar el servidor
```bash
cd d:\UNIVERSIDAD\MOVILES\API_UPRed
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente ejecuta: `start_server.bat`

### 2. Verificar que el servidor está funcionando

**Endpoint de prueba (sin autenticación):**
```
GET http://localhost:8000/api/publicaciones/test
```

Debería responder:
```json
{
  "status": "ok",
  "message": "Publicaciones router está funcionando"
}
```

### 3. Obtener token de autenticación

**Login:**
```
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "correo_institucional": "tu_correo@universidad.edu",
  "password": "tu_password"
}
```

Respuesta:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "usuario": { ... }
}
```

### 4. Obtener publicaciones

**Listar publicaciones:**
```
GET http://localhost:8000/api/publicaciones
Authorization: Bearer {tu_token}
```

### 5. Crear publicación

**Crear nueva publicación:**
```
POST http://localhost:8000/api/publicaciones
Authorization: Bearer {tu_token}
Content-Type: application/json

{
  "titulo": "Mi primera publicación",
  "contenido": "Este es el contenido de mi publicación",
  "audiencia": "general"
}
```

### 6. Editar publicación

**Actualizar publicación:**
```
PUT http://localhost:8000/api/publicaciones/{id}
Authorization: Bearer {tu_token}
Content-Type: application/json

{
  "titulo": "Título actualizado",
  "contenido": "Contenido actualizado"
}
```

### 7. Eliminar publicación

**Eliminar publicación:**
```
DELETE http://localhost:8000/api/publicaciones/{id}
Authorization: Bearer {tu_token}
```

---

## Estructura de respuesta esperada por la app móvil:

```json
{
  "id": 1,
  "autor_id": 123,
  "titulo": "Título de la publicación",
  "contenido": "Contenido de la publicación",
  "audiencia": "general",
  "publicada_en": "2026-02-26T10:15:00",
  "autor": {
    "nombre": "Juan",
    "apellido_paterno": "Pérez",
    "apellido_materno": "García",
    "foto_perfil_url": null
  },
  "total_reacciones": 0,
  "total_comentarios": 0
}
```

---

## Solución de problemas:

### Error 404 Not Found
- **Causa:** El servidor no está corriendo o la ruta es incorrecta
- **Solución:** Asegúrate de que el servidor esté corriendo en `http://localhost:8000`

### Error 401 Unauthorized
- **Causa:** No estás enviando el token de autenticación o el token es inválido
- **Solución:** Asegúrate de incluir el header `Authorization: Bearer {token}`

### Error 422 Unprocessable Entity
- **Causa:** El formato del JSON no es correcto o faltan campos requeridos
- **Solución:** Verifica que estés enviando todos los campos requeridos: `titulo`, `contenido`, `audiencia`

### Error de conexión desde Android
- **Causa:** La app no puede conectarse al servidor
- **Solución:** 
  - Verifica que tu computadora y teléfono estén en la misma red
  - Usa la IP de tu computadora en lugar de `localhost`
  - En `local.properties` de Android, configura: `API_BASE_URL=http://TU_IP:8000/`
  - Ejemplo: `API_BASE_URL=http://192.168.1.100:8000/`

---

## Configuración en la app Android

Asegúrate de que `local.properties` tenga la URL correcta:

```properties
# API Configuration
API_BASE_URL=http://192.168.1.100:8000/
```

**Para encontrar tu IP:**
- Windows: Abre CMD y ejecuta `ipconfig`, busca "Dirección IPv4"
- La IP generalmente es algo como `192.168.1.xxx`
