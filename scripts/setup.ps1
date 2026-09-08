# Crea el entorno virtual e instala las dependencias del proyecto.
# Uso (desde la raíz del proyecto):
#   .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creando entorno virtual en .venv ..."
        py -3.13 -m venv .venv
    }

    Write-Host "Activando entorno virtual e instalando dependencias..."
    & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"

    Write-Host ""
    Write-Host "Listo. Para ejecutar la app:"
    Write-Host "  .\.venv\Scripts\python.exe run.py"
    Write-Host "o, tras activar el entorno (.\.venv\Scripts\Activate.ps1):"
    Write-Host "  python -m astronomia"
}
finally {
    Pop-Location
}
