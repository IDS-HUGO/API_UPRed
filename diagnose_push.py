#!/usr/bin/env python3
"""
Diagnóstico automático de notificaciones push - UPRed API
Uso: python diagnose_push.py
"""

import os
import sys
import json
from pathlib import Path

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def check_env_file():
    """Verifica archivos .env"""
    print("\n📋 [1/5] Verificando archivos de configuración...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("  ❌ .env no existe")
        return False
    
    print("  ✅ .env encontrado")
    
    # Leer .env
    env_vars = {}
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    firebase_path = env_vars.get("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    print(f"  Firebase path en .env: {firebase_path or '❌ VACÍO'}")
    
    return firebase_path


def check_firebase_file(firebase_path):
    """Verifica que el archivo JSON de Firebase exista y sea válido"""
    print("\n🔐 [2/5] Verificando credenciales Firebase...")
    
    if not firebase_path:
        print("  ❌ Ruta de Firebase vacía")
        return False
    
    path = Path(firebase_path)
    if not path.exists():
        print(f"  ❌ Archivo no existe: {firebase_path}")
        return False
    
    print(f"  ✅ Archivo encontrado: {firebase_path}")
    
    try:
        with open(firebase_path) as f:
            creds = json.load(f)
        
        required_keys = ["type", "project_id", "private_key_id", "private_key"]
        missing = [k for k in required_keys if k not in creds]
        
        if missing:
            print(f"  ⚠️  Faltan campos: {', '.join(missing)}")
            return False
        
        print(f"  ✅ Credenciales válidas (proyecto: {creds.get('project_id')})")
        return True
        
    except json.JSONDecodeError:
        print("  ❌ JSON inválido")
        return False


def check_firebase_init():
    """Verifica que Firebase pueda inicializarse"""
    print("\n🔧 [3/5] Inicializando Firebase Admin SDK...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        print("  ✅ firebase_admin importado")
        
        # No reinicializar si ya está inicializado
        if firebase_admin._apps:
            print("  ✅ Firebase ya inicializado en esta sesión")
            return True
        
        print("  ℹ️  Firebase no inicializado aún (será inicializado en aplicación)")
        return True
        
    except ImportError:
        print("  ❌ firebase_admin no instalado: pip install firebase-admin")
        return False


def check_database():
    """Verifica conexión a BD"""
    print("\n💾 [4/5] Verificando base de datos...")
    
    try:
        from database import SessionLocal
        
        db = SessionLocal()
        result = db.execute("SELECT 1")
        db.close()
        print("  ✅ Base de datos conectada")
        
        # Contar dispositivos
        from models import DispositivoUsuario
        db = SessionLocal()
        count = db.query(DispositivoUsuario).count()
        db.close()
        print(f"  ℹ️  Dispositivos registrados: {count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error BD: {str(e)}")
        return False


def check_push_service():
    """Verifica estado del servicio de push"""
    print("\n🚀 [5/5] Verificando servicio de push...")
    
    try:
        from services.firebase_push_service import firebase_push_service
        
        status = firebase_push_service.get_status()
        enabled = status.get("enabled")
        path_present = status.get("service_account_path_present")
        
        if enabled:
            print(f"  ✅ Firebase Push HABILITADO")
        else:
            print(f"  ❌ Firebase Push DESHABILITADO")
            
        if path_present:
            print(f"  ✅ Ruta de credenciales configurada")
        else:
            print(f"  ⚠️  Ruta de credenciales no presente")
        
        return enabled
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE NOTIFICACIONES PUSH - UPRED API")
    print("=" * 60)
    
    results = {
        "config": check_env_file(),
        "firebase_file": None,
        "firebase_init": None,
        "database": None,
        "push_service": None,
    }
    
    if results["config"]:
        firebase_path = results["config"]
        results["firebase_file"] = check_firebase_file(firebase_path)
    
    results["firebase_init"] = check_firebase_init()
    results["database"] = check_database()
    results["push_service"] = check_push_service()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    checks = {
        "Configuración (.env)": results["config"],
        "Archivo Firebase JSON": results["firebase_file"],
        "SDK Firebase": results["firebase_init"],
        "Base de datos": results["database"],
        "Servicio de Push": results["push_service"],
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    for name, status in checks.items():
        icon = "✅" if status else "❌" if status is False else "⚠️"
        print(f"{icon} {name}")
    
    print(f"\nResultado: {passed}/{total} checks pasados")
    
    if results["push_service"]:
        print("\n🎉 Firebase Push está HABILITADO - Las notificaciones deberían funcionar")
    else:
        print("\n⚠️  Firebase Push NO está habilitado")
        print("\n📍 Próximos pasos:")
        print("  1. Verifica que FIREBASE_SERVICE_ACCOUNT_PATH existe en .env")
        print("  2. Verifica que el archivo JSON existe en esa ruta")
        print("  3. Reinicia la API: python -m uvicorn main:app --reload")
        print("  4. Ejecuta este script nuevamente para verificar")


if __name__ == "__main__":
    main()
