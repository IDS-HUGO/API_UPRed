# Guía de Nuevas Funcionalidades - UPRed

## Resumen de Cambios

### Android App (RED-UP)

#### 1. **Pantalla Home Mejorada**
Después de loguearse, el usuario ve:
- ✅ **Feed de Publicaciones**: Lista completa de publicaciones con:
  - Nombre del autor y fecha de publicación
  - Título y contenido
  - Contador de reacciones (❤️) y comentarios (💬)
  - Diseño limpio y mejorado

- ✅ **Botón Flotante de Mensaje**: Un FAB (Floating Action Button) con icono de sobre en la esquina inferior derecha
  - Al presionarlo, abre un diálogo con 2 opciones:
    - 📧 **Mensaje Individual**: Para chatear 1 a 1
    - 👥 **Mensaje Grupal**: Para chatear en un grupo

- ✅ **Botón Cerrar Sesión**: En la esquina superior derecha (TopAppBar)
  - Icono de salida (🚪)
  - Al presionar, muestra un diálogo de confirmación
  - Limpia los datos locales y vuelve a Login

#### 2. **NavigationGraph Actualizado**
- HomeScreen ahora recibe el callback `onNavigateToLogin`
- Después de logout, la navegación vuelve a la pantalla de Login de forma segura
- Scroll popUpTo garantiza que no quede en el stack

### Backend API (API_UPRed)

#### 3. **Nuevos Endpoints REST**

**Buscar Usuario por Correo:**
```http
GET /api/usuarios/por-correo/{correo}
```
- Encuentra un usuario específico usando su correo
- Retorna: `UsuarioResponse` con toda la información del usuario
- Útil para iniciar chats individuales
- Ejemplo: `GET /api/usuarios/por-correo/123456@ing.upchiapas.edu.mx`

**Invitar Miembro por Correo a un Grupo:**
```http
POST /api/grupos/{grupo_id}/miembros/invitar-por-correo?correo=usuario@dominio.com
```
- Busca usuario por correo y lo agrega directamente al grupo
- Parameters:
  - `grupo_id`: ID del grupo (path)
  - `correo`: Email del usuario (query)
- Retorna: Mensaje de confirmación

#### 4. **Mejoras en WebSocket**

**Nuevo Evento: Buscar Usuario**
```json
{
  "event": "search_user_by_email",
  "data": {
    "email": "usuario@universidad.com"
  }
}
```
- Respuesta (si usuario existe):
```json
{
  "event": "user_found",
  "data": {
    "user_id": "5",
    "nombre": "Juan",
    "apellido_paterno": "García",
    "apellido_materno": "López",
    "correo_institucional": "123456@ing.upchiapas.edu.mx",
    "foto_perfil_url": "https://..."
  }
}
```

**Nuevo Evento: Indicador de Escritura**
```json
{
  "event": "typing",
  "data": {
    "sender_id": "1",
    "recipient_id": "2",
    "group_id": null
  }
}
```
Respuesta a otros usuarios:
```json
{
  "event": "user_typing",
  "data": {
    "user_id": "1",
    "recipient_id": "2"
  }
}
```

**Mejoras en Mensajes**
- Ahora incluyen información del remitente: `sender_nombre` y `sender_apellido`
- Mejor tracking de estado: `delivered`, `read`
- Timestamps más precisos en ISO format

#### 5. **Endpoint de Logout**
```http
POST /api/auth/logout
Authorization: Bearer {token}
```
- Retorna: `{"message": "Sesión cerrada correctamente"}`
- El cliente debe eliminar el token después de esta llamada
- En Android, ya se maneja automáticamente en `AuthPreferences.clear()`

### Flujo Completo de Usuario

1. **Login**: Usuario ingresa credenciales
2. **Home**: Ve publicaciones del feed
3. **Enviar Mensaje**:
   - Presiona FAB de mensaje
   - Elige entre Individual o Grupal
   - Si es Individual: busca usuario por correo → abre chat 1 a 1
   - Si es Grupal: va a lista de grupos → selecciona grupo → abre chat grupal
4. **Chat**: Intercambia mensajes en tiempo real via WebSocket
   - Indica cuando otros escriben
   - Marca mensajes como entregados/leídos
5. **Logout**: Presiona botón de salida → confirma → vuelve a Login

### Cambios Técnicos

#### ViewModel (HomeViewModel.kt)
```kotlin
fun logout(onNavigateToLogin: () -> Unit) {
    viewModelScope.launch {
        try {
            chatRepository.disconnect()
            authPreferences.clear()  // Limpia token, user_id, nombre
            onNavigateToLogin()      // Navega a Login
        } catch (e: Exception) {
            // Maneja error
        }
    }
}
```

#### Screen (HomeScreen.kt)
- Nuevo FAB con `FloatingActionButton`
- Nuevo `AlertDialog` para elegir tipo de mensaje
- Nuevo `AlertDialog` para confirmar logout
- Mejor UI de publicaciones con tarjetas mejoradas

### Uso en Cliente WebSocket

**Conectar usuario:**
```javascript
socket.emit('connect', {
  user_id: '123'
});

socket.on('connected', (data) => {
  console.log('Conectado:', data);
});
```

**Buscar usuario:**
```javascript
socket.emit('search_user_by_email', {
  email: 'usuario@universidad.com'
});

socket.on('user_found', (user) => {
  console.log('Usuario encontrado:', user);
  // Iniciar chat con este usuario
});

socket.on('user_not_found', (error) => {
  console.log('Usuario no encontrado');
});
```

**Indicar que está escribiendo:**
```javascript
socket.emit('typing', {
  sender_id: '1',
  recipient_id: '2'  // Para mensajes individuales
  // O
  // group_id: '5'   // Para mensajes grupales
});
```

**Dejar de escribir:**
```javascript
socket.emit('stop_typing', {
  sender_id: '1',
  recipient_id: '2'
});
```

**Obtener usuarios conectados:**
```javascript
socket.emit('get_online_users');

socket.on('online_users', (data) => {
  console.log('Usuarios conectados:', data.users);
  console.log('Total:', data.total);
});
```

---

## Checklist de Validación

- [x] HomeScreen muestra publicaciones correctamente
- [x] FAB de mensaje visible en esquina inferior derecha
- [x] Diálogo de opciones (Individual/Grupal) funciona
- [x] Botón logout en TopAppBar funciona
- [x] Confirmar antes de logout
- [x] API endpoint para buscar usuario por correo
- [x] API endpoint para invitar por correo a grupo
- [x] WebSocket buscar usuario por email
- [x] WebSocket indicador de escritura
- [x] Navegación segura después de logout

## Testing

### Android
```bash
# Ejecutar en Android Studio o emulador
./gradlew assembleDebug
```

### API
```bash
# Test endpoint usuarios
curl -X GET "http://localhost:8000/api/usuarios/por-correo/usuario@dominio.com"

# Test logout
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer {token}"
```

### WebSocket
```bash
# Usar herramienta como Postman, Socket.io Client o navegador
# Conectar a ws://localhost:5000
```

---

**Fecha de Actualización**: 26 de Febrero, 2026
**Versión**: 2.1.0
