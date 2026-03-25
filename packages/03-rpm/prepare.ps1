$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\..\.."
$spec = Join-Path $root "packages\03-rpm\printer-reaper.spec"
$ver = python -c "import sys; sys.path.insert(0, r'$root\src'); import version; print(version.__version__)"

Write-Host "[rpm] version: $ver" -ForegroundColor Cyan
Write-Host "[rpm] spec file: $spec" -ForegroundColor Green
Write-Host "[rpm] Em Windows, o build de RPM deve ser feito em host Linux (Fedora/RHEL/Rocky)." -ForegroundColor Yellow
Write-Host "[rpm] Use WSL/VM e execute: ./packages/03-rpm/build.sh" -ForegroundColor Yellow

