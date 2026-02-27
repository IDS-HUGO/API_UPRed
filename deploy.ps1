# =====================================================================
# Script PowerShell para Deploy de API a EC2
# =====================================================================

# Configuración
$ErrorActionPreference = "Stop"

$Config = @{
    KeyFile = "C:\path\to\your-key.pem"  # EDITAR: Ruta a tu archivo .pem
    User = "ubuntu"                       # EDITAR: Usuario del servidor
    Host = "apiupred.ferluna.online"     # EDITAR: Dominio o IP de EC2
    RemotePath = "/home/ubuntu/API_UPRed" # EDITAR: Ruta remota de la API
}

$FilesToUpload = @(
    "routers/publicaciones.py",
    "schemas.py"
)

# =====================================================================
# Funciones Helper
# =====================================================================

function Write-Header {
    param([string]$Text)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-ErrorMsg {
    param([string]$Text)
    Write-Host "`n❌ ERROR: $Text`n" -ForegroundColor Red
}

function Write-Success {
    param([string]$Text)
    Write-Host "`n✅ $Text`n" -ForegroundColor Green
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Yellow
}

# =====================================================================
# Script Principal
# =====================================================================

Write-Header "🚀 DEPLOY API UPRED A EC2"

# Verificar configuración
Write-Header "Verificando Configuración"

if (-not (Test-Path $Config.KeyFile)) {
    Write-ErrorMsg "No se encontró el archivo de clave SSH: $($Config.KeyFile)"
    Write-Info "Por favor, edita este script y configura la ruta correcta en `$Config.KeyFile"
    exit 1
}

Write-Info "Key File: $($Config.KeyFile)"
Write-Info "Usuario: $($Config.User)"
Write-Info "Host: $($Config.Host)"
Write-Info "Path Remoto: $($Config.RemotePath)"

Write-Info "`nArchivos a subir:"
foreach ($file in $FilesToUpload) {
    $localPath = Join-Path $PSScriptRoot $file
    if (-not (Test-Path $localPath)) {
        Write-ErrorMsg "No se encontró el archivo: $localPath"
        exit 1
    }
    Write-Info "  ✓ $file"
}

# Confirmar
Write-Host "`n⚠️  ¿Deseas continuar con el deploy? (s/n): " -NoNewline -ForegroundColor Yellow
$respuesta = Read-Host

if ($respuesta -notin @("s", "si", "S", "SI", "y", "Y", "yes", "YES")) {
    Write-Info "Deploy cancelado por el usuario"
    exit 0
}

# Subir archivos
Write-Header "Subiendo Archivos"

foreach ($file in $FilesToUpload) {
    $localPath = Join-Path $PSScriptRoot $file
    $remotePath = "$($Config.RemotePath)/$($file.Replace('\', '/'))"
    
    Write-Info "Subiendo: $file"
    
    # Comando SCP
    $scpCmd = "scp -i `"$($Config.KeyFile)`" `"$localPath`" $($Config.User)@$($Config.Host):$remotePath"
    
    try {
        Invoke-Expression $scpCmd
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ $file subido correctamente"
        } else {
            Write-ErrorMsg "Falló la subida de $file"
            exit 1
        }
    } catch {
        Write-ErrorMsg "Error al subir $file : $_"
        exit 1
    }
}

# Reiniciar servicio
Write-Header "Reiniciando Servicio"

$sshCmd = "ssh -i `"$($Config.KeyFile)`" $($Config.User)@$($Config.Host) `"cd $($Config.RemotePath) && sudo systemctl restart uvicorn`""

Write-Info "Ejecutando: sudo systemctl restart uvicorn"

try {
    Invoke-Expression $sshCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Servicio reiniciado correctamente"
    } else {
        Write-ErrorMsg "No se pudo reiniciar con systemctl. Intenta manualmente."
        exit 1
    }
} catch {
    Write-ErrorMsg "Error al reiniciar servicio: $_"
    exit 1
}

# Verificación
Write-Header "Verificando Deploy"

$testUrl = "https://$($Config.Host)/api/publicaciones/test"

Write-Info "Verificando endpoint: $testUrl"
Write-Info "`nPuedes verificar manualmente con:"
Write-Host "`n  curl $testUrl`n"
Write-Info "Debería devolver:"
Write-Host '  {"status":"ok","message":"Publicaciones router está funcionando"}'

Write-Header "✨ DEPLOY COMPLETADO EXITOSAMENTE"
Write-Success "Los archivos se han subido y el servidor se ha reiniciado"
Write-Info "Ahora prueba tu app Android - ya no debería dar error 404"

Write-Host "`nPresiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
