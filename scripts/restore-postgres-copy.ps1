[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BackupFile,
    [ValidatePattern('^nexomark_restore_[a-z0-9_]{1,40}$')]
    [string]$TargetDatabase = ('nexomark_restore_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [guid]::NewGuid().ToString('N').Substring(0, 8)),
    [ValidatePattern('^[a-zA-Z0-9_.-]+$')]
    [string]$Container = 'marketmind_postgres'
)

$ErrorActionPreference = 'Stop'
function Invoke-DockerChecked([string[]]$DockerArguments) {
    & docker @DockerArguments 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'La operación Docker/PostgreSQL falló. La base original no se sobrescribe.' }
}

# Always restore to a NEW database; no --clean, DROP DATABASE or source overwrite.
$sourcePath = (Resolve-Path -LiteralPath $BackupFile).Path
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw 'Selecciona un archivo, no una carpeta.' }
$hashPath = $sourcePath + '.sha256'
if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) { throw 'Falta el archivo SHA256 del respaldo.' }
$expectedHash = (Get-Content -LiteralPath $hashPath -Raw).Trim()
if ($expectedHash -notmatch '^[A-Fa-f0-9]{64}$' -or
    (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'El respaldo no coincide con su SHA256. No se restauró.'
}
$containerFile = '/tmp/nexomark-restore-' + [guid]::NewGuid().ToString('N') + '.dump'
$databaseCreated = $false
try {
    Invoke-DockerChecked @('cp', $sourcePath, "${Container}:$containerFile")
    Invoke-DockerChecked @('exec', $Container, 'pg_restore', '--list', $containerFile)
    # createdb fails if the name already exists; it never overwrites an existing DB.
    Invoke-DockerChecked @('exec', $Container, 'sh', '-c',
        'exec createdb -U "$POSTGRES_USER" -- "$1"', '--', $TargetDatabase)
    $databaseCreated = $true
    Invoke-DockerChecked @('exec', $Container, 'sh', '-c',
        'exec pg_restore -U "$POSTGRES_USER" --dbname="$1" --exit-on-error --no-owner --no-privileges "$2"',
        '--', $TargetDatabase, $containerFile)
    Write-Output "Copia restaurada en base nueva: $TargetDatabase"
    Write-Output 'No se cambiaron .env ni conexiones de la aplicación. La base original sigue intacta.'
} catch {
    if ($databaseCreated) { Write-Warning "Se conserva la base de prueba $TargetDatabase; podría estar incompleta. No conectar la aplicación." }
    throw
} finally {
    if ($containerFile -match '^/tmp/nexomark-restore-[a-f0-9]{32}\.dump$') {
        & docker exec $Container rm -- $containerFile 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Warning 'No se pudo retirar el archivo temporal del contenedor.' }
    }
}
