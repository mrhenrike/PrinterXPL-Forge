# PrinterXPL-Forge — launcher with local venv (bypasses EDR temp restrictions)
# Usage: .\run.ps1 <ip> --scan
# Usage: .\run.ps1 192.168.0.152 --scan-ml --no-nvd
# Usage: .\run.ps1 --check-config
# Usage: .\run.ps1 --discover-local

$ErrorActionPreference = "Stop"
$venv_python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venv_python)) {
    Write-Host "[!] Venv not found. Running setup_venv.ps1 ..." -ForegroundColor Yellow
    & "$PSScriptRoot\setup_venv.ps1"
}

& $venv_python "$PSScriptRoot\src\main.py" @args
