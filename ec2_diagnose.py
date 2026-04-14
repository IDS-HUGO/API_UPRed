#!/usr/bin/env python3
"""
Diagnóstico remoto para EC2 - Verificar estado de push notifications
Ejecutar en EC2: python3 ec2_diagnose.py
"""

import os
import sys
import json
import requests
from pathlib import Path

def check_firebase_json():
    """Verificar si existe el JSON de Firebase"""
    print("🔐 [1/4] Verificando Firebase JSON...")

    paths = [
        "/home/ec2-user/firebase-service-account.json",
        "/opt/upred/ws/firebase-service-account.json",
        "/home/ubuntu/firebase-service-account.json"
    ]

    for path in paths:
        if os.path.exists(path):
            print(f"  ✅ Encontrado: {path}")
            try:
                with open(path) as f:
                    creds = json.load(f)
                project_id = creds.get('project_id', 'unknown')
                print(f"  ✅ Proyecto: {project_id}")
                return True, path
            except Exception as e:
                print(f"  ❌ JSON inválido: {e}")
                return False, path

    print("  ❌ No encontrado en rutas comunes")
    return False, None

def check_env_file():
    """Verificar .env"""
    print("\n⚙️  [2/4] Verificando .env...")

    env_paths = [
        "/opt/upred/ws/.env",
        "/home/ec2-user/.env",
        ".env"
    ]

    for path in env_paths:
        if os.path.exists(path):
            print(f"  ✅ .env encontrado: {path}")
            with open(path) as f:
                content = f.read()
                if "FIREBASE_SERVICE_ACCOUNT_PATH" in content:
                    print("  ✅ FIREBASE_SERVICE_ACCOUNT_PATH configurado")
                    for line in content.split('\n'):
                        if line.startswith("FIREBASE_SERVICE_ACCOUNT_PATH"):
                            firebase_path = line.split('=', 1)[1].strip()
                            print(f"  ℹ️  Path: {firebase_path}")
                            return True
                else:
                    print("  ❌ FIREBASE_SERVICE_ACCOUNT_PATH no encontrado")
                    return False

    print("  ❌ .env no encontrado")
    return False

def check_api_status():
    """Verificar estado de la API"""
    print("\n🌐 [3/4] Verificando API...")

    try:
        # Intentar localhost primero
        response = requests.get("http://localhost:8000/api/notificaciones/push/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            enabled = data.get("firebase_push_enabled", False)
            path_present = data.get("service_account_path_present", False)

            print("  ✅ API responde en localhost:8000")
            print(f"  Firebase enabled: {'✅' if enabled else '❌'}")
            print(f"  Service account path: {'✅' if path_present else '❌'}")

            if enabled:
                print("  🎉 Firebase Push HABILITADO")
                return True
            else:
                print("  ⚠️  Firebase Push DESHABILITADO")
                return False
        else:
            print(f"  ❌ API retorna {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  ❌ No se puede conectar a localhost:8000")
        print("  ℹ️  ¿Está corriendo la API?")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_database():
    """Verificar dispositivos en BD"""
    print("\n💾 [4/4] Verificando base de datos...")

    try:
        import mysql.connector
        from mysql.connector import Error

        # Intentar conectar a BD
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,  # O 3307 si usa tunnel
            user="root",
            password="",  # Cambiar si tiene password
            database="upred_db"
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Contar dispositivos
            cursor.execute("SELECT COUNT(*) FROM dispositivos_usuario")
            total_devices = cursor.fetchone()[0]

            # Contar con token
            cursor.execute("SELECT COUNT(*) FROM dispositivos_usuario WHERE token_push IS NOT NULL AND token_push != ''")
            devices_with_token = cursor.fetchone()[0]

            # Contar usuarios
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_users = cursor.fetchone()[0]

            print("  ✅ Conexión BD exitosa")
            print(f"  ℹ️  Usuarios totales: {total_users}")
            print(f"  ℹ️  Dispositivos registrados: {total_devices}")
            print(f"  ℹ️  Con token push: {devices_with_token}")

            if devices_with_token > 0:
                print("  ✅ Hay dispositivos con tokens - Push debería funcionar")
                return True
            else:
                print("  ❌ NO hay dispositivos con tokens - Push NO funcionará")
                print("  ℹ️  La app móvil NO está registrando dispositivos")
                return False

    except ImportError:
        print("  ❌ mysql-connector-python no instalado")
        print("  ℹ️  pip install mysql-connector-python")
        return False
    except Error as e:
        print(f"  ❌ Error BD: {e}")
        print("  ℹ️  Verificar credenciales y conexión")
        return False

def main():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO EC2 - Push Notifications UPRed")
    print("=" * 60)

    results = {
        "firebase_json": check_firebase_json(),
        "env_config": check_env_file(),
        "api_status": check_api_status(),
        "database": check_database(),
    }

    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)

    checks = {
        "Firebase JSON existe": results["firebase_json"][0] if isinstance(results["firebase_json"], tuple) else results["firebase_json"],
        "Config .env": results["env_config"],
        "API funcionando": results["api_status"],
        "BD con dispositivos": results["database"],
    }

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")

    print(f"\nResultado: {passed}/{total} checks pasados")

    if passed == total:
        print("\n🎉 TODO ESTÁ CONFIGURADO CORRECTAMENTE")
        print("Si las notificaciones no llegan, el problema está en la app móvil")
        print("La app NO está registrando dispositivos después de login")
    else:
        print("\n⚠️  HAY PROBLEMAS DE CONFIGURACIÓN")
        if not results["firebase_json"][0]:
            print("  - Copiar firebase-service-account.json a EC2")
        if not results["env_config"]:
            print("  - Configurar FIREBASE_SERVICE_ACCOUNT_PATH en .env")
        if not results["api_status"]:
            print("  - Verificar que la API esté corriendo")
        if not results["database"]:
            print("  - La app móvil no registra dispositivos")

if __name__ == "__main__":
    main()
