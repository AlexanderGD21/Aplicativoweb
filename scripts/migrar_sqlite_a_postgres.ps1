param(
    [switch]$Confirmar
)

$ErrorActionPreference = 'Stop'

if (-not $Confirmar) {
    throw 'Este comando crea un respaldo y carga datos en PostgreSQL. Ejecútalo con -Confirmar cuando DATABASE_* apunte al servidor destino.'
}

$raiz = Resolve-Path (Join-Path $PSScriptRoot '..')
$python = Join-Path $raiz 'venv\Scripts\python.exe'
$sqlite = Join-Path $raiz 'db.sqlite3'
$respaldoDir = Join-Path $raiz 'backups'
$marca = Get-Date -Format 'yyyyMMdd-HHmmss'
$respaldo = Join-Path $respaldoDir "db.sqlite3-antes-postgres-$marca"
$volcado = Join-Path $respaldoDir "sqlite-para-postgres-$marca.json"

if (-not (Test-Path -LiteralPath $python)) { throw "No se encontró el entorno virtual: $python" }
if (-not (Test-Path -LiteralPath $sqlite)) { throw "No se encontró la base SQLite: $sqlite" }

New-Item -ItemType Directory -Force -Path $respaldoDir | Out-Null
Copy-Item -LiteralPath $sqlite -Destination $respaldo

$motorAnterior = $env:DATABASE_ENGINE
$sqlitePathAnterior = $env:SQLITE_DATABASE_PATH
$pythonUtf8Anterior = $env:PYTHONUTF8
try {
    # Evita que Windows use la página de códigos activa al serializar palabras con ñ, tildes y Kichwa.
    $env:PYTHONUTF8 = '1'
    # Fuerza una lectura del origen local aunque .env ya contenga las credenciales destino.
    $env:DATABASE_ENGINE = 'sqlite'
    # DATABASE_NAME apunta a PostgreSQL en .env; SQLite necesita su ruta física.
    $env:SQLITE_DATABASE_PATH = $sqlite
    & $python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes --indent 2 --output $volcado
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo exportar SQLite.' }

    $env:DATABASE_ENGINE = 'postgresql'
    & $python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron aplicar las migraciones en PostgreSQL.' }

    & $python manage.py loaddata $volcado
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron cargar los datos en PostgreSQL.' }

    & $python manage.py check --deploy
    Write-Host "Migración terminada. Respaldo SQLite: $respaldo" -ForegroundColor Green
    Write-Host "Volcado reutilizable: $volcado" -ForegroundColor Green
}
finally {
    if ($null -eq $motorAnterior) { Remove-Item Env:DATABASE_ENGINE -ErrorAction SilentlyContinue }
    else { $env:DATABASE_ENGINE = $motorAnterior }
    if ($null -eq $sqlitePathAnterior) { Remove-Item Env:SQLITE_DATABASE_PATH -ErrorAction SilentlyContinue }
    else { $env:SQLITE_DATABASE_PATH = $sqlitePathAnterior }
    if ($null -eq $pythonUtf8Anterior) { Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue }
    else { $env:PYTHONUTF8 = $pythonUtf8Anterior }
}
