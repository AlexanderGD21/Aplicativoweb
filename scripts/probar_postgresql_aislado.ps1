param(
    [string]$PostgresBin = 'C:\Program Files\PostgreSQL\18\bin'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'venv\Scripts\python.exe'
$initdb = Join-Path $PostgresBin 'initdb.exe'
$pgCtl = Join-Path $PostgresBin 'pg_ctl.exe'

foreach ($path in @($python, $initdb, $pgCtl)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "No se encontró el ejecutable requerido: $path"
    }
}

$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$clusterRoot = Join-Path $tempRoot ('kichwa-pg-tests-' + [guid]::NewGuid().ToString('N'))
$dataDir = Join-Path $clusterRoot 'data'
$passwordFile = Join-Path $clusterRoot 'password.txt'
$logFile = Join-Path $clusterRoot 'postgres.log'
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
$listener.Stop()
$passwordBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $randomGenerator.GetBytes($passwordBytes)
}
finally {
    $randomGenerator.Dispose()
}
$password = [Convert]::ToBase64String($passwordBytes)
$serverStarted = $false
$databaseVariables = @('DATABASE_ENGINE', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD', 'DATABASE_HOST', 'DATABASE_PORT')
$previousEnvironment = @{}
foreach ($name in $databaseVariables) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

New-Item -ItemType Directory -Path $clusterRoot | Out-Null
Set-Content -LiteralPath $passwordFile -Value $password -NoNewline

try {
    & $initdb -D $dataDir -U codex_test -A scram-sha-256 --pwfile=$passwordFile --no-instructions
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo inicializar PostgreSQL de prueba.' }

    & $pgCtl -D $dataDir -l $logFile -o "-h 127.0.0.1 -p $port" -w start
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar PostgreSQL de prueba.' }
    $serverStarted = $true

    $env:DATABASE_ENGINE = 'postgresql'
    $env:DATABASE_NAME = 'postgres'
    $env:DATABASE_USER = 'codex_test'
    $env:DATABASE_PASSWORD = $password
    $env:DATABASE_HOST = '127.0.0.1'
    $env:DATABASE_PORT = [string]$port

    Push-Location $projectRoot
    try {
        & $python manage.py test --noinput
        if ($LASTEXITCODE -ne 0) { throw 'La suite de Django falló en PostgreSQL.' }
    }
    finally { Pop-Location }
}
finally {
    foreach ($name in $databaseVariables) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }

    if ($serverStarted) {
        & $pgCtl -D $dataDir -m fast -w stop
        if ($LASTEXITCODE -ne 0) { throw "No se pudo detener PostgreSQL de prueba: $clusterRoot" }
    }

    $resolvedCluster = [IO.Path]::GetFullPath($clusterRoot)
    if (-not $resolvedCluster.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -or $resolvedCluster -eq $tempRoot) {
        throw "Ruta temporal inesperada: $resolvedCluster"
    }
    Remove-Item -LiteralPath $resolvedCluster -Recurse -Force
}
