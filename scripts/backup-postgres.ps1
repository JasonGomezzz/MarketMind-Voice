[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9_.-]+$')]
    [string]$Container = 'marketmind_postgres',
    [string]$BackupDirectory = (Join-Path $PSScriptRoot '../backups/postgres')
)

$ErrorActionPreference = 'Stop'
function Invoke-DockerChecked([string[]]$DockerArguments) {
    & docker @DockerArguments 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'La operación Docker/PostgreSQL falló. No se considera válido el respaldo.' }
}

$backupRoot = [IO.Path]::GetFullPath($BackupDirectory)
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$backupId = [guid]::NewGuid().ToString('N')
$backupName = 'nexomark-{0}-{1}.dump' -f (Get-Date -Format 'yyyyMMdd-HHmmss'), $backupId
$backupPath = Join-Path $backupRoot $backupName
$containerFile = '/tmp/nexomark-backup-' + $backupId + '.dump'
$archiveCreated = $false
try {
    # pg_dump produces a consistent snapshot; it does not alter the source database.
    # Use the container's configured database/user, without exposing passwords.
    Invoke-DockerChecked @('exec', $Container, 'sh', '-c',
        'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file="$1"',
        '--', $containerFile)
    Invoke-DockerChecked @('exec', $Container, 'pg_restore', '--list', $containerFile)
    Invoke-DockerChecked @('cp', "${Container}:$containerFile", $backupPath)
    if ((Get-Item -LiteralPath $backupPath).Length -le 0) { throw 'El archivo de respaldo está vacío.' }
    $archiveCreated = $true
    $hashPath = $backupPath + '.sha256'
    (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash |
        Set-Content -LiteralPath $hashPath -Encoding ascii
    Write-Output "Respaldo creado: $backupPath"
    Write-Output "SHA256 guardado: $hashPath"
    Write-Output 'Se comprobó el índice del archivo; aún no se probó una restauración completa.'
} finally {
    # Exact generated temporary file only; never a directory or a wildcard.
    if ($containerFile -match '^/tmp/nexomark-backup-[a-f0-9]{32}\.dump$') {
        & docker exec $Container rm -- $containerFile 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Warning 'No se pudo retirar el archivo temporal del contenedor.' }
    }
    if (-not $archiveCreated -and (Test-Path -LiteralPath $backupPath)) {
        Write-Warning "Archivo incompleto conservado para diagnóstico; no usar: $backupPath"
    }
}
