Param(
  [string]$OutDir = "diagrams/png",
  [string]$Config = "diagrams/mermaid-config.json",
  [int]$Scale = 2,
  [int]$PuppeteerTimeout = 120000
)

$ErrorActionPreference = 'Stop'

Write-Host "Generating PNG diagrams to $OutDir" -ForegroundColor Cyan

# Ensure mermaid-cli
if (-not (Get-Command mmdc -ErrorAction SilentlyContinue)) {
  Write-Host "Installing mermaid-cli locally (npx)..." -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$files = Get-ChildItem -Path "diagrams" -Filter *.mmd
foreach ($f in $files) {
  $out = Join-Path $OutDir ($f.BaseName + '.png')
  Write-Host "  -> $($f.Name) -> $out" -ForegroundColor Green
  npx -y @mermaid-js/mermaid-cli --quiet -i $f.FullName -o $out --configFile $Config --scale $Scale
}

Write-Host "Done." -ForegroundColor Cyan

