$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "== AI Coding Mentor Desktop Build ==" -ForegroundColor Cyan

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js is required." }
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { throw "pnpm is required." }

Write-Host "[1/3] Installing frontend dependencies..."
Push-Location "$RepoRoot\frontend"
pnpm install --frozen-lockfile
Pop-Location

Write-Host "[2/3] Building production web app..."
Push-Location "$RepoRoot\frontend"
$env:VITE_API_URL = "http://localhost:8001"
$env:VITE_WS_URL = "ws://localhost:8001"
$env:VITE_SCREEN_SOURCE_ENABLED = "false"
pnpm build
Pop-Location

Write-Host "[3/3] Packaging with Pake..."
Push-Location "$RepoRoot\desktop"
npx -y pake-cli@3.17.3 --config .\pake.json --targets x64 --json
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) { throw "Pake packaging failed with exit code $exitCode." }

Write-Host "Desktop packaging complete." -ForegroundColor Green
Get-ChildItem "$RepoRoot\desktop" -File |
    Where-Object { $_.Extension -in ".exe", ".msi", ".zip" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, Length, LastWriteTime