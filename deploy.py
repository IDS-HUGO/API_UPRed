"""
Script de deploy automatizado para subir cambios de API a servidor EC2
Uso: python deploy.py
"""

import os
import sys
from pathlib import Path

# =====================================================================
# CONFIGURACIÓN - EDITA ESTOS VALORES
# =====================================================================

EC2_CONFIG = {
    "key_file": r"C:\path\to\your-key.pem",  # Ruta a tu archivo .pem
    "user": "ubuntu",  # Usuario del servidor (ubuntu, ec2-user, etc.)
    "host": "apiupred.ferluna.online",  # Dominio o IP de tu EC2
    "remote_path": "/home/ubuntu/API_UPRed",  # Ruta remota de la API
}

# Archivos a subir (relativos a este script)
FILES_TO_UPLOAD = [
    "routers/publicaciones.py",
    "schemas.py",
]

# =====================================================================
# NO EDITAR DEBAJO DE ESTA LÍNEA
# =====================================================================

def print_header(text):
    """Imprime un encabezado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_error(text):
    """Imprime un error"""
    print(f"\n❌ ERROR: {text}\n")

def print_success(text):
    """Imprime un mensaje de éxito"""
    print(f"\n✅ {text}\n")

def print_info(text):
    """Imprime información"""
    print(f"ℹ️  {text}")

def check_config():
    """Verifica la configuración"""
    print_header("Verificando Configuración")
    
    # Verificar archivo .pem
    key_file = Path(EC2_CONFIG["key_file"])
    if not key_file.exists():
        print_error(f"No se encontró el archivo de clave SSH: {key_file}")
        print_info("Por favor, edita el archivo 'deploy.py' y configura la ruta correcta en EC2_CONFIG['key_file']")
        return False
    
    print_info(f"Key File: {key_file}")
    print_info(f"Usuario: {EC2_CONFIG['user']}")
    print_info(f"Host: {EC2_CONFIG['host']}")
    print_info(f"Path Remoto: {EC2_CONFIG['remote_path']}")
    
    # Verificar archivos locales
    print_info("\nArchivos a subir:")
    for file_path in FILES_TO_UPLOAD:
        local_file = Path(__file__).parent / file_path
        if not local_file.exists():
            print_error(f"No se encontró el archivo local: {local_file}")
            return False
        print_info(f"  ✓ {file_path}")
    
    return True

def upload_files():
    """Sube los archivos al servidor"""
    print_header("Subiendo Archivos")
    
    key_file = EC2_CONFIG["key_file"]
    user = EC2_CONFIG["user"]
    host = EC2_CONFIG["host"]
    remote_path = EC2_CONFIG["remote_path"]
    
    for file_path in FILES_TO_UPLOAD:
        local_file = Path(__file__).parent / file_path
        remote_file = f"{remote_path}/{file_path.replace(os.sep, '/')}"
        
        print_info(f"Subiendo: {file_path}")
        
        # Comando SCP
        cmd = f'scp -i "{key_file}" "{local_file}" {user}@{host}:{remote_file}'
        
        result = os.system(cmd)
        
        if result != 0:
            print_error(f"Falló la subida de {file_path}")
            return False
        
        print_success(f"✓ {file_path} subido correctamente")
    
    return True

def restart_service():
    """Reinicia el servicio en el servidor"""
    print_header("Reiniciando Servicio")
    
    key_file = EC2_CONFIG["key_file"]
    user = EC2_CONFIG["user"]
    host = EC2_CONFIG["host"]
    remote_path = EC2_CONFIG["remote_path"]
    
    # Comando SSH para reiniciar
    restart_cmd = f'ssh -i "{key_file}" {user}@{host} "cd {remote_path} && sudo systemctl restart uvicorn"'
    
    print_info("Ejecutando: sudo systemctl restart uvicorn")
    result = os.system(restart_cmd)
    
    if result != 0:
        print_error("No se pudo reiniciar con systemctl. Intentando método alternativo...")
        
        # Método alternativo
        alt_cmd = f'ssh -i "{key_file}" {user}@{host} "sudo pkill -f uvicorn && cd {remote_path} && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &"'
        result = os.system(alt_cmd)
        
        if result != 0:
            print_error("No se pudo reiniciar el servicio")
            return False
    
    print_success("Servicio reiniciado correctamente")
    return True

def verify_deploy():
    """Verifica que el deploy fue exitoso"""
    print_header("Verificando Deploy")
    
    test_url = f"https://{EC2_CONFIG['host']}/api/publicaciones/test"
    
    print_info(f"Verificando endpoint: {test_url}")
    print_info("\nPuedes verificar manualmente con:")
    print(f"\n  curl {test_url}\n")
    print_info("Debería devolver:")
    print('  {"status":"ok","message":"Publicaciones router está funcionando"}')

def main():
    """Función principal"""
    print_header("🚀 DEPLOY API UPRED A EC2")
    
    # Paso 1: Verificar configuración
    if not check_config():
        sys.exit(1)
    
    # Paso 2: Confirmar
    print("\n⚠️  ¿Deseas continuar con el deploy? (s/n): ", end="")
    respuesta = input().strip().lower()
    
    if respuesta not in ["s", "si", "y", "yes"]:
        print_info("Deploy cancelado por el usuario")
        sys.exit(0)
    
    # Paso 3: Subir archivos
    if not upload_files():
        print_error("Deploy fallido en la subida de archivos")
        sys.exit(1)
    
    # Paso 4: Reiniciar servicio
    if not restart_service():
        print_error("Deploy parcial: archivos subidos pero el servicio no se reinició")
        print_info("Intenta reiniciar manualmente con:")
        print(f"  ssh -i {EC2_CONFIG['key_file']} {EC2_CONFIG['user']}@{EC2_CONFIG['host']}")
        print(f"  sudo systemctl restart uvicorn")
        sys.exit(1)
    
    # Paso 5: Verificar
    verify_deploy()
    
    print_header("✨ DEPLOY COMPLETADO EXITOSAMENTE")
    print_success("Los archivos se han subido y el servidor se ha reiniciado")
    print_info("Ahora prueba tu app Android - ya no debería dar error 404")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nDeploy cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        sys.exit(1)
