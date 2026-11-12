# PowerShell Database Restore from Local file or AWS S3 URI
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Source,
    [string]$AwsEndpointUrl = $env:AWS_ENDPOINT_URL
)

$ErrorActionPreference = "Stop"

$TempDownload = $null
$FileToRestore = $Source

if ($Source.StartsWith("s3://")) {
    Write-Host "[restore] Detected S3 source URI: $Source" -ForegroundColor Cyan
    $TempDir = [System.IO.Path]::GetTempPath()
    $TempDownload = Join-Path $TempDir ("ecom_s3_restore_" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + ".sql.gz")

    Write-Host "[restore] Downloading backup from AWS S3 to $TempDownload..." -ForegroundColor Cyan
    $AwsArgs = @("s3", "cp", $Source, $TempDownload)
    if ($AwsEndpointUrl) {
        $AwsArgs += @("--endpoint-url", $AwsEndpointUrl)
    }

    & aws @AwsArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to download backup from S3: $Source"
    }
    $FileToRestore = $TempDownload
}

if (!(Test-Path $FileToRestore)) {
    Write-Error "Backup file not found: $FileToRestore"
}

Write-Host "[restore] WARNING: This will drop and recreate database 'ecomdb' in container 'ecom_db'!" -ForegroundColor Red
Write-Host "[restore] Waiting 5 seconds before continuing. Press Ctrl+C to abort..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[restore] Dropping and recreating database ecomdb..." -ForegroundColor Cyan
docker exec ecom_db psql -U ecom -c "DROP DATABASE IF EXISTS ecomdb;"
docker exec ecom_db psql -U ecom -c "CREATE DATABASE ecomdb;"

# Decompress .gz to temporary .sql
$TempSql = Join-Path ([System.IO.Path]::GetTempPath()) ("ecom_restore_" + [Guid]::NewGuid().ToString() + ".sql")
Write-Host "[restore] Decompressing archive..." -ForegroundColor Cyan
$InputStream = [System.IO.File]::OpenRead($FileToRestore)
$GzipStream = New-Object System.IO.Compression.GZipStream($InputStream, [System.IO.Compression.CompressionMode]::Decompress)
$OutputStream = [System.IO.File]::Create($TempSql)
$GzipStream.CopyTo($OutputStream)
$OutputStream.Close()
$GzipStream.Close()
$InputStream.Close()

Write-Host "[restore] Restoring data into ecom_db..." -ForegroundColor Cyan
Get-Content $TempSql | docker exec -i ecom_db psql -U ecom -d ecomdb

Remove-Item $TempSql -Force
if ($TempDownload -and (Test-Path $TempDownload)) {
    Remove-Item $TempDownload -Force
}

Write-Host "[restore] Database restore completed successfully." -ForegroundColor Green
