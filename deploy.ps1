# 🚀 DEPLOY FINAL A EC2 - UPRED API
# Script para subir cambios a servidor EC2 en una sola ejecución

param(
    [string]$KeyFile = "C:\ruta\a\tu-clave.pem",
    [string]$EC2User = "ubuntu",
    [string]$EC2Host = "apiupred.ferluna.online",
    [string]$RemotePath = "/home/ubuntu/API_UPRed"
)

# =====================================================================
# CONFIGURACIÓN - EDITAR AQUÍ
# =====================================================================

# Si los parámetros no se pasan, puedes editarlos aquí manualmente:
# $KeyFile = "C:\Users\tu-usuario\.ssh\upred-key.pem"
# $EC2User = "ubuntu"
# $EC2Host = "apiupred.ferluna.online"
# $RemotePath = "/home/ubuntu/API_UPRed"

# =====================================================================
# FUNCIONES
# =====================================================================

function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $colors = @{
        "INFO" = "Cyan"
        "OK" = "Green"
        "ERROR" = "Red"
        "WARN" = "Yellow"
    }
    $color = $colors[$Status] ?? "White"
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Verify-Config {
    Write-Status "Verificando configuración..." "INFO"
    
    if (-not (Test-Path $KeyFile)) {
        Write-Status "❌ Clave SSH no encontrada: $KeyFile" "ERROR"
        Write-Status "Edita este script y actualiza KeyFile" "WARN"
        exit 1
    }
    
    Write-Status "✓ Clave SSH: $KeyFile" "OK"
    Write-Status "✓ Usuario: $EC2User" "OK"
    Write-Status "✓ Host: $EC2Host" "OK"
    Write-Status "✓ Path remoto: $RemotePath" "OK"
}

function Upload-Files {
    Write-Status "`nSubiendo archivos..." "INFO"
    
    $files = @(
        "routers\publicaciones.py",
        "schemas.py",
        "main.py"
    )
    
    foreach ($file in $files) {
        if (-not (Test-Path $file)) {
            Write-Status "❌ Archivo no encontrado: $file" "ERROR"
            exit 1
        }
        
        $remoteFile = "$RemotePath/$($file.Replace('\', '/'))"
        Write-Status "Subiendo: $file" "INFO"
        
        & scp -i $KeyFile $file "${EC2User}@${EC2Host}:${remoteFile}" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Status "❌ Falló subida de $file" "ERROR"
            exit 1
        }
        
        Write-Status "✓ $file subido" "OK"
    }
}

function Restart-Service {
    Write-Status "`nReiniciando servicio..." "INFO"
    
    & ssh -i $KeyFile "${EC2User}@${EC2Host}" "cd $RemotePath && sudo systemctl restart uvicorn" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "⚠️  Intenta reiniciar manualmente en el servidor" "WARN"
        return $false
    }
    
    Write-Status "✓ Servicio reiniciado" "OK"
    return $true
}

function Verify-Deploy {
    Write-Status "`nVerificando deploy..." "INFO"
    
    Write-Host "`n📝 Ejecuta esto en tu servidor para verificar:"
    Write-Host "curl https://apiupred.ferluna.online/api/publicaciones/test"
    Write-Host "`nDebería devolver:"
    Write-Host '{​"status":"ok","message":"Publicaciones router está funcionando"}' -ForegroundColor Green
}

# =====================================================================
# MAIN
# =====================================================================

Clear-Host
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  🚀 DEPLOY FINAL - UPRED API A EC2" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Verify-Config
Upload-Files
Restart-Service
Verify-Deploy

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  ✅ DEPLOY COMPLETADO" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

Write-Host "`n✨ Tu API está lista. Verifica en:"
Write-Host "   https://apiupred.ferluna.online/api/publicaciones/test" -ForegroundColor Cyan
