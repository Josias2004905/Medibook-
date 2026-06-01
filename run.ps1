# MediBook local dev server (port 8002)
Set-Location $PSScriptRoot

Write-Host "Freeing port 8002..." -ForegroundColor Yellow
$portPids = netstat -ano | Select-String "127.0.0.1:8002\s" | ForEach-Object {
    ($_.Line -split '\s+')[-1]
} | Sort-Object -Unique

foreach ($procId in $portPids) {
    if ($procId -match '^\d+$') {
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 1

Write-Host "Running migrations..." -ForegroundColor Cyan
python -u manage.py migrate --noinput

Write-Host ""
Write-Host "Starting MediBook at http://127.0.0.1:8002/" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

python -u manage.py runserver 8002 --noreload
