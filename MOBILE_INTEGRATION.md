# Integración con App Móvil

Este documento explica cómo integrar la API con tu aplicación móvil.

## 📱 Configuración

### Base URL
```javascript
const API_BASE_URL = 'http://tu-servidor:8000';
// Para desarrollo local en Android: 'http://10.0.2.2:8000'
// Para desarrollo local en iOS: 'http://localhost:8000'
```

## 🔐 Sistema de Autenticación

### 1. Servicio de API (ejemplo React Native)

```javascript
// services/api.js
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://tu-servidor:8000';

class ApiService {
  // Guardar token
  async saveToken(token) {
    await AsyncStorage.setItem('token', token);
  }

  // Obtener token
  async getToken() {
    return await AsyncStorage.getItem('token');
  }

  // Eliminar token
  async clearToken() {
    await AsyncStorage.removeItem('token');
  }

  // Request con autorización
  async request(endpoint, options = {}) {
    const token = await this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error en la petición');
    }

    return await response.json();
  }

  // Login
  async login(email, password) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    await this.saveToken(data.access_token);
    return data;
  }

  // Register
  async register(userData) {
    return await this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Logout
  async logout() {
    await this.clearToken();
  }

  // Obtener perfil
  async getProfile() {
    return await this.request('/api/auth/me');
  }

  // Obtener publicaciones
  async getPublicaciones(page = 0, limit = 20, carreraId = null) {
    let url = `/api/publicaciones?skip=${page * limit}&limit=${limit}`;
    if (carreraId) url += `&carrera_id=${carreraId}`;
    return await this.request(url);
  }

  // Crear publicación
  async createPublicacion(data) {
    return await this.request('/api/publicaciones', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Actualizar publicación
  async updatePublicacion(id, data) {
    return await this.request(`/api/publicaciones/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Eliminar publicación
  async deletePublicacion(id) {
    return await this.request(`/api/publicaciones/${id}`, {
      method: 'DELETE',
    });
  }

  // Dar like
  async likePublicacion(id) {
    return await this.request(`/api/publicaciones/${id}/like`, {
      method: 'POST',
    });
  }

  // Quitar like
  async unlikePublicacion(id) {
    return await this.request(`/api/publicaciones/${id}/like`, {
      method: 'DELETE',
    });
  }

  // Obtener comentarios
  async getComentarios(publicacionId) {
    return await this.request(`/api/publicaciones/${publicacionId}/comentarios`);
  }

  // Crear comentario
  async createComentario(publicacionId, contenido) {
    return await this.request(`/api/publicaciones/${publicacionId}/comentarios`, {
      method: 'POST',
      body: JSON.stringify({ contenido, publicacion_id: publicacionId }),
    });
  }

  // Obtener carreras
  async getCarreras() {
    return await this.request('/api/carreras');
  }

  // Obtener dominios de correo
  async getDominiosCorreo() {
    return await this.request('/api/auth/dominios-correo');
  }
}

export default new ApiService();
```

## 📋 Ejemplos de Uso

### Pantalla de Login

```javascript
// screens/LoginScreen.js
import React, { useState } from 'react';
import { View, TextInput, Button, Alert } from 'react-native';
import api from '../services/api';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Por favor completa todos los campos');
      return;
    }

    setLoading(true);
    try {
      const response = await api.login(email, password);
      Alert.alert('Éxito', 'Sesión iniciada correctamente');
      navigation.replace('Home');
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        placeholder="Contraseña"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button
        title={loading ? 'Cargando...' : 'Iniciar Sesión'}
        onPress={handleLogin}
        disabled={loading}
      />
      <Button
        title="Registrarse"
        onPress={() => navigation.navigate('Register')}
      />
    </View>
  );
}
```

### Pantalla de Registro

```javascript
// screens/RegisterScreen.js
import React, { useState, useEffect } from 'react';
import { View, TextInput, Button, Picker, Alert } from 'react-native';
import api from '../services/api';

export default function RegisterScreen({ navigation }) {
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    email: '',
    password: '',
    tipo_usuario: 'ALUMNO',
    carrera_id: null,
    matricula: '',
    numero_empleado: '',
  });
  const [carreras, setCarreras] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCarreras();
  }, []);

  const loadCarreras = async () => {
    try {
      const data = await api.getCarreras();
      setCarreras(data);
    } catch (error) {
      Alert.alert('Error', 'No se pudieron cargar las carreras');
    }
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      await api.register(formData);
      Alert.alert('Éxito', 'Registro completado. Ahora puedes iniciar sesión.');
      navigation.navigate('Login');
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <TextInput
        placeholder="Nombre"
        value={formData.nombre}
        onChangeText={(value) => setFormData({ ...formData, nombre: value })}
      />
      <TextInput
        placeholder="Apellido"
        value={formData.apellido}
        onChangeText={(value) => setFormData({ ...formData, apellido: value })}
      />
      <TextInput
        placeholder="Email"
        value={formData.email}
        onChangeText={(value) => setFormData({ ...formData, email: value })}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        placeholder="Contraseña"
        value={formData.password}
        onChangeText={(value) => setFormData({ ...formData, password: value })}
        secureTextEntry
      />
      
      <Picker
        selectedValue={formData.tipo_usuario}
        onValueChange={(value) => setFormData({ ...formData, tipo_usuario: value })}
      >
        <Picker.Item label="Alumno" value="ALUMNO" />
        <Picker.Item label="Docente" value="DOCENTE" />
      </Picker>

      <Picker
        selectedValue={formData.carrera_id}
        onValueChange={(value) => setFormData({ ...formData, carrera_id: value })}
      >
        <Picker.Item label="Selecciona una carrera" value={null} />
        {carreras.map((carrera) => (
          <Picker.Item key={carrera.id} label={carrera.nombre} value={carrera.id} />
        ))}
      </Picker>

      {formData.tipo_usuario === 'ALUMNO' && (
        <TextInput
          placeholder="Matrícula"
          value={formData.matricula}
          onChangeText={(value) => setFormData({ ...formData, matricula: value })}
        />
      )}

      {formData.tipo_usuario === 'DOCENTE' && (
        <TextInput
          placeholder="Número de Empleado"
          value={formData.numero_empleado}
          onChangeText={(value) => setFormData({ ...formData, numero_empleado: value })}
        />
      )}

      <Button
        title={loading ? 'Registrando...' : 'Registrarse'}
        onPress={handleRegister}
        disabled={loading}
      />
    </View>
  );
}
```

### Pantalla de Publicaciones

```javascript
// screens/PublicacionesScreen.js
import React, { useState, useEffect } from 'react';
import { View, FlatList, Text, Button, RefreshControl } from 'react-native';
import api from '../services/api';

export default function PublicacionesScreen({ navigation }) {
  const [publicaciones, setPublicaciones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPublicaciones();
  }, []);

  const loadPublicaciones = async () => {
    setLoading(true);
    try {
      const data = await api.getPublicaciones();
      setPublicaciones(data);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleLike = async (publicacionId) => {
    try {
      await api.likePublicacion(publicacionId);
      loadPublicaciones(); // Recargar para actualizar likes
    } catch (error) {
      Alert.alert('Error', error.message);
    }
  };

  const renderPublicacion = ({ item }) => (
    <View style={{ padding: 15, borderBottomWidth: 1, borderColor: '#ccc' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>{item.titulo}</Text>
      <Text>{item.contenido}</Text>
      <Text style={{ color: '#666', marginTop: 5 }}>
        Por: {item.usuario?.nombre} {item.usuario?.apellido}
      </Text>
      <View style={{ flexDirection: 'row', marginTop: 10 }}>
        <Button title={`❤️ ${item.total_likes}`} onPress={() => handleLike(item.id)} />
        <Button
          title={`💬 ${item.total_comentarios}`}
          onPress={() => navigation.navigate('Comentarios', { publicacionId: item.id })}
        />
      </View>
    </View>
  );

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={publicaciones}
        renderItem={renderPublicacion}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={loadPublicaciones} />
        }
      />
      <Button
        title="Nueva Publicación"
        onPress={() => navigation.navigate('NuevaPublicacion')}
      />
    </View>
  );
}
```

## 🔄 Manejo de Errores

```javascript
// utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.message.includes('401')) {
    // Token expirado
    return 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.';
  } else if (error.message.includes('403')) {
    return 'No tienes permisos para realizar esta acción.';
  } else if (error.message.includes('404')) {
    return 'Recurso no encontrado.';
  } else if (error.message.includes('Network request failed')) {
    return 'Error de conexión. Verifica tu internet.';
  } else {
    return error.message || 'Error desconocido';
  }
};
```

## 📦 Dependencias Necesarias

```bash
# React Native
npm install @react-native-async-storage/async-storage
npm install @react-navigation/native
npm install @react-navigation/stack

# Expo
expo install @react-native-async-storage/async-storage
```

## 🔧 Configuración de Seguridad

⚠️ **Importante**: En producción:

1. Usa HTTPS en lugar de HTTP
2. Valida los certificados SSL
3. No guardes información sensible en texto plano
4. Implementa refresh tokens
5. Maneja la expiración de tokens correctamente

## 📱 Testing

```javascript
// __tests__/api.test.js
import api from '../services/api';

describe('API Service', () => {
  it('should login successfully', async () => {
    const response = await api.login(
      'test@alumno.escuela.edu.mx',
      'password123'
    );
    expect(response).toHaveProperty('access_token');
  });

  it('should get publicaciones', async () => {
    const publicaciones = await api.getPublicaciones();
    expect(Array.isArray(publicaciones)).toBe(true);
  });
});
```

## 🚀 Deploy

Para producción, actualiza la `API_BASE_URL` a tu servidor:

```javascript
const API_BASE_URL = 'https://api.tuescuela.com';
```
