$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "[pipx] pipx não encontrado. Instale com: python -m pip install --user pipx" -ForegroundColor Yellow
    exit 1
}

Write-Host "[pipx] Instalando pacote local em modo editable..." -ForegroundColor Cyan
pipx install --force --editable .

Write-Host "[pipx] Validando comando..." -ForegroundColor Cyan
printer-reaper --version
printer-reaper --help | Out-Null

Write-Host "[pipx] OK" -ForegroundColor Green

