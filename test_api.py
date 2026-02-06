# Script de prueba de la API
# Asegúrate de tener la API corriendo antes de ejecutar este script

import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")

def main():
    # 1. Health Check
    print("\n🔍 1. Verificando que la API esté corriendo...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    
    # 2. Listar carreras
    print("\n📚 2. Listando carreras disponibles...")
    response = requests.get(f"{BASE_URL}/api/carreras")
    print_response("Carreras Disponibles", response)
    
    # 3. Ver dominios de correo permitidos
    print("\n📧 3. Dominios de correo permitidos...")
    response = requests.get(f"{BASE_URL}/api/auth/dominios-correo")
    print_response("Dominios de Correo", response)
    
    # 4. Login con admin
    print("\n🔐 4. Login como Administrador...")
    login_data = {
        "email": "admin@escuela.edu.mx",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print_response("Login Administrador", response)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 5. Ver perfil actual
        print("\n👤 5. Obteniendo perfil del usuario autenticado...")
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print_response("Mi Perfil", response)
        
        # 6. Crear una publicación de ejemplo
        print("\n📝 6. Creando una publicación de ejemplo...")
        publicacion_data = {
            "titulo": "Bienvenidos a la Red Social Escolar",
            "contenido": "Esta es una publicación de prueba del sistema. ¡Bienvenidos!",
            "tipo_publicacion": "GENERAL",
            "carrera_id": 1
        }
        response = requests.post(
            f"{BASE_URL}/api/publicaciones",
            json=publicacion_data,
            headers=headers
        )
        print_response("Crear Publicación", response)
        
        if response.status_code == 201:
            publicacion_id = response.json()["id"]
            
            # 7. Dar like a la publicación
            print(f"\n❤️ 7. Dando like a la publicación {publicacion_id}...")
            response = requests.post(
                f"{BASE_URL}/api/publicaciones/{publicacion_id}/like",
                headers=headers
            )
            print_response("Dar Like", response)
            
            # 8. Crear un comentario
            print(f"\n💬 8. Comentando en la publicación {publicacion_id}...")
            comentario_data = {
                "contenido": "¡Excelente publicación! Gracias por compartir.",
                "publicacion_id": publicacion_id
            }
            response = requests.post(
                f"{BASE_URL}/api/publicaciones/{publicacion_id}/comentarios",
                json=comentario_data,
                headers=headers
            )
            print_response("Crear Comentario", response)
            
            # 9. Listar publicaciones
            print("\n📋 9. Listando todas las publicaciones...")
            response = requests.get(f"{BASE_URL}/api/publicaciones", headers=headers)
            print_response("Listar Publicaciones", response)
    
    print("\n" + "="*60)
    print("✅ Pruebas completadas!")
    print("="*60)
    print("\n📚 Visita http://localhost:8000/docs para ver la documentación completa")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar a la API")
        print("Asegúrate de que la API esté corriendo en http://localhost:8000")
        print("Ejecuta: python main.py")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
