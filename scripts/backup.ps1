# PowerShell Database Backup & AWS S3 Sync
[CmdletBinding()]
param(
    [string]$BackupDir = ".\backups",
    [string]$S3Bucket = $env:S3_BUCKET_NAME,
    [string]$AwsEndpointUrl = $env:AWS_ENDPOINT_URL
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RawDump = Join-Path $BackupDir "ecomdb_$Timestamp.sql"
$GzDump = "$RawDump.gz"

Write-Host "[backup] Starting PostgreSQL backup from ecom_db container..." -ForegroundColor Cyan
docker exec ecom_db pg_dump -U ecom -d ecomdb --no-owner --no-acl > $RawDump

if (!(Test-Path $RawDump) -or (Get-Item $RawDump).Length -eq 0) {
    Write-Error "Database dump failed or produced an empty file."
}

# Compress to .gz using .NET GZipStream
Write-Host "[backup] Compressing backup to $GzDump..." -ForegroundColor Cyan
$InputStream = [System.IO.File]::OpenRead($RawDump)
$OutputStream = [System.IO.File]::Create($GzDump)
$GzipStream = New-Object System.IO.Compression.GZipStream($OutputStream, [System.IO.Compression.CompressionMode]::Compress)
$InputStream.CopyTo($GzipStream)
$GzipStream.Close()
$OutputStream.Close()
$InputStream.Close()
Remove-Item $RawDump -Force

$SizeMB = [math]::Round((Get-Item $GzDump).Length / 1MB, 2)
Write-Host "[backup] Local backup complete: $GzDump ($SizeMB MB)" -ForegroundColor Green

# Optional AWS S3 Upload
if ($S3Bucket) {
    Write-Host "[backup] S3_BUCKET_NAME configured: s3://$S3Bucket" -ForegroundColor Cyan
    Write-Host "[backup] Uploading backup to AWS S3 with AES256 server-side encryption..." -ForegroundColor Cyan

    $S3Dest = "s3://$S3Bucket/backups/ecomdb_$Timestamp.sql.gz"
    $AwsArgs = @("s3", "cp", $GzDump, $S3Dest, "--sse", "AES256")
    if ($AwsEndpointUrl) {
        $AwsArgs += @("--endpoint-url", $AwsEndpointUrl)
    }

    & aws @AwsArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[backup] AWS S3 upload successful: $S3Dest" -ForegroundColor Green
    } else {
        Write-Warning "AWS S3 upload failed with exit code $LASTEXITCODE."
    }
} else {
    Write-Host "[backup] Note: S3_BUCKET_NAME environment variable not set." -ForegroundColor Yellow
    Write-Host "[backup] Tip: Set S3_BUCKET_NAME=<your-bucket> in .env to auto-sync backups to AWS S3." -ForegroundColor Yellow
}
