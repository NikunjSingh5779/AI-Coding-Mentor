$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "Starting AI Coding Mentor infrastructure..." -ForegroundColor Cyan
docker compose up --build -d

Write-Host "Waiting for backend readiness..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/ready" -TimeoutSec 2
        if ($response.status -eq "ready" -or $response.status -eq "degraded") {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $ready) {
    throw "Backend did not become reachable. Run: docker compose logs backend sandbox"
}

$desktopBinary = Get-ChildItem "$RepoRoot\desktop" -Filter "*AI Coding Mentor*.exe" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $desktopBinary) {
    $desktopBinary = Get-ChildItem "$RepoRoot\desktop" -Filter "*.exe" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

if (-not $desktopBinary) {
    throw "No packaged desktop executable found. Run scripts\build-desktop.ps1 first."
}

Write-Host "Launching $($desktopBinary.FullName)" -ForegroundColor Green
Start-Process -FilePath $desktopBinary.FullName