# PrinterReaper — launcher with local venv (bypasses EDR temp restrictions)
# Usage: .\run.ps1 <ip> --scan
# Usage: .\run.ps1 192.168.0.152 --scan-ml --no-nvd
# Usage: .\run.ps1 --check-config
# Usage: .\run.ps1 --discover-local

$venv_python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venv_python)) {
    Write-Host "[!] Venv not found. Creating..." -ForegroundColor Yellow
    python -m venv "$PSScriptRoot\.venv" --prompt PrinterReaper
    & "$PSScriptRoot\.venv\Scripts\pip.exe" install -r "$PSScriptRoot\requirements.txt"
}

& $venv_python "$PSScriptRoot\src\main.py" @args
