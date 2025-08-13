# Script de PowerShell para probar dependencias en Windows
Write-Host "🧪 Probando dependencias de producción..." -ForegroundColor Green
Write-Host ""

# Verificar que requirements.txt existe
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ No se encontró requirements.txt" -ForegroundColor Red
    exit 1
}

# Crear entorno virtual
Write-Host "1️⃣ Creando entorno virtual..." -ForegroundColor Yellow
try {
    python -m venv test_env
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
} catch {
    Write-Host "❌ Error creando entorno virtual: $_" -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host "2️⃣ Instalando dependencias..." -ForegroundColor Yellow
try {
    # Actualizar pip
    $pythonExe = "test_env\Scripts\python.exe"
    $result = & $pythonExe -m pip install --upgrade pip 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pip actualizado" -ForegroundColor Green
    } else {
        Write-Host "⚠️ pip no se pudo actualizar" -ForegroundColor Yellow
    }
    
    # Instalar dependencias
    $result = & $pythonExe -m pip install -r requirements.txt 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
        $success = $true
    } else {
        Write-Host "❌ Error instalando dependencias:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        $success = $false
    }
    
} catch {
    Write-Host "❌ Error durante la instalación: $_" -ForegroundColor Red
    $success = $false
}

# Limpiar
Write-Host "3️⃣ Limpiando..." -ForegroundColor Yellow
try {
    Remove-Item -Recurse -Force "test_env" -ErrorAction SilentlyContinue
    Write-Host "✅ Entorno temporal eliminado" -ForegroundColor Green
} catch {
    Write-Host "⚠️ No se pudo eliminar test_env (elimínalo manualmente)" -ForegroundColor Yellow
}

Write-Host ""
if ($success) {
    Write-Host "🎉 ¡Dependencias funcionando correctamente!" -ForegroundColor Green
    Write-Host "✅ Tu requirements.txt está listo para Railway" -ForegroundColor Green
} else {
    Write-Host "❌ Hay problemas con las dependencias" -ForegroundColor Red
    Write-Host "💡 Revisa el error anterior" -ForegroundColor Yellow
}
