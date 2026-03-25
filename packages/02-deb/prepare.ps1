$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\..\.."
$srcDebian = Join-Path $root "packages\02-deb\debian"
$dstDebian = Join-Path $root "debian"
$srcMan = Join-Path $root "packages\man\printer-reaper.1"
$dstManDir = Join-Path $root "man\man1"

Write-Host "[deb] Syncing Debian templates to repository root..." -ForegroundColor Cyan

if (Test-Path $dstDebian) {
    Remove-Item $dstDebian -Recurse -Force
}
New-Item -ItemType Directory -Path $dstDebian -Force | Out-Null
Copy-Item "$srcDebian\*" $dstDebian -Recurse -Force

New-Item -ItemType Directory -Path $dstManDir -Force | Out-Null
Copy-Item $srcMan (Join-Path $dstManDir "printer-reaper.1") -Force

Write-Host "[deb] Ready: $dstDebian" -ForegroundColor Green

