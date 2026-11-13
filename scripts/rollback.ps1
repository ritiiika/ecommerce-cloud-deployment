# PowerShell Docker Compose Rollback Script
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ImageTag
)

$ErrorActionPreference = "Stop"

Write-Host "[rollback] Target rollback image: $ImageTag" -ForegroundColor Cyan

docker pull $ImageTag 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[rollback] Using local image or remote pull skipped." -ForegroundColor Yellow
}

$OverrideContent = @"
version: "3.9"
services:
  api:
    image: $ImageTag
    build: !reset null
"@

$OverridePath = "docker-compose.rollback.yml"
Set-Content -Path $OverridePath -Value $OverrideContent

Write-Host "[rollback] Applying rollback via Docker Compose..." -ForegroundColor Cyan
docker compose -f docker-compose.yml -f $OverridePath up -d --no-deps api
Remove-Item $OverridePath -Force

Write-Host "[rollback] Awaiting container health check..." -ForegroundColor Cyan
$Healthy = $false
for ($i = 1; $i -le 12; $i++) {
    $res = docker exec ecom_api curl -sf http://localhost:8000/health 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Healthy = $true
        break
    }
    Write-Host "[rollback] Probe check ($i/12)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

if ($Healthy) {
    Write-Host "[rollback] SUCCESS: Service healthy on rollback image $ImageTag" -ForegroundColor Green
} else {
    Write-Error "[rollback] Health check timed out after rollback."
}
