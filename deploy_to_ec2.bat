@echo off
REM =====================================================================
REM SCRIPT DE DEPLOY A EC2 - API UPRED
REM =====================================================================
REM Este script ayuda a subir los archivos actualizados al servidor EC2

echo ========================================
echo   DEPLOY API UPRED A EC2
echo ========================================
echo.

REM Verificar si se tiene acceso SSH
echo [PASO 1] Verificando conexion SSH...
echo.
echo Para deploy necesitas:
echo - Archivo .pem de clave SSH
echo - IP o dominio del servidor EC2
echo - Usuario del servidor (usualmente: ubuntu, ec2-user, etc.)
echo.

REM Variables (EDITAR ESTAS LINEAS CON TUS DATOS)
set KEY_FILE=C:\path\to\your-key.pem
set EC2_USER=ubuntu
set EC2_HOST=apiupred.ferluna.online
set REMOTE_PATH=/home/ubuntu/API_UPRed

echo ========================================
echo CONFIGURACION:
echo ========================================
echo Key File: %KEY_FILE%
echo Usuario: %EC2_USER%
echo Host: %EC2_HOST%
echo Path Remoto: %REMOTE_PATH%
echo ========================================
echo.

REM Verificar si el archivo .pem existe
if not exist "%KEY_FILE%" (
    echo [ERROR] No se encontro el archivo de clave SSH: %KEY_FILE%
    echo.
    echo Por favor, edita este script y configura la ruta correcta en la variable KEY_FILE
    echo.
    pause
    exit /b 1
)

echo [PASO 2] Subiendo archivos al servidor...
echo.

REM Usar SCP para subir archivos (requiere OpenSSH instalado en Windows)
echo Subiendo routers/publicaciones.py...
scp -i "%KEY_FILE%" routers\publicaciones.py %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/routers/

echo.
echo Subiendo schemas.py...
scp -i "%KEY_FILE%" schemas.py %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

echo.
echo [PASO 3] Reiniciando el servidor API...
echo.

REM Conectar por SSH y reiniciar el servicio
ssh -i "%KEY_FILE%" %EC2_USER%@%EC2_HOST% "cd %REMOTE_PATH% && sudo systemctl restart uvicorn"

echo.
echo ========================================
echo   DEPLOY COMPLETADO
echo ========================================
echo.
echo Los archivos se han subido y el servidor se ha reiniciado.
echo.
echo Verifica que funcione:
echo https://apiupred.ferluna.online/api/publicaciones/test
echo.
pause
