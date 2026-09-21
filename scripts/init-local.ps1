$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
if (-not (Test-Path '.env')) {
    $randomBytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($randomBytes)
    $rng.Dispose()
    $password = [Convert]::ToBase64String($randomBytes)
    [System.IO.File]::WriteAllText((Join-Path $projectRoot '.env'), "DB_PASSWORD=$password`n")
    Write-Host 'Created .env with a random database password. Do not publish it.'
} else {
    Write-Host 'Keeping existing .env and password.'
}
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
Write-Host 'PyCharm interpreter:' (Join-Path $projectRoot '.venv\Scripts\python.exe')
