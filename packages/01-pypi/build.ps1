$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

Write-Host "[pypi] Building wheel + sdist..." -ForegroundColor Cyan
python -m pip install --upgrade pip build twine | Out-Null

if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
Get-ChildItem -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

python -m build

Write-Host "[pypi] Build artifacts:" -ForegroundColor Green
Get-ChildItem "dist" | Format-Table Name, Length, LastWriteTime

Write-Host "[pypi] Validating metadata..." -ForegroundColor Cyan
python -m twine check dist/*

Write-Host "[pypi] Done." -ForegroundColor Green

