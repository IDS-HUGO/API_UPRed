@echo off
echo ========================================
echo   Iniciando API UPRed
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

echo.
echo Instalando dependencias (si es necesario)...
pip install -r requirements.txt

echo.
echo ========================================
echo   Servidor iniciado en:
echo   http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
