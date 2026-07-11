param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'Course-Agent\creative'
$Logs = Join-Path $Root 'artifacts\logs'
$Python = Join-Path $Backend '.venv\Scripts\python.exe'

function Get-AvailablePort([int]$PreferredPort) {
    $used = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners().Port
    $candidate = $PreferredPort
    while ($used -contains $candidate) { $candidate++ }
    return $candidate
}

function Import-DotEnv([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or -not $trimmed.Contains('=')) { continue }
        $name, $value = $trimmed.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
    }
}

New-Item -ItemType Directory -Force -Path $Logs | Out-Null
Import-DotEnv (Join-Path $Root '.env')

if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv (Join-Path $Backend '.venv')
}

& $Python -m pip install -e "$Backend[test]"
corepack pnpm --dir $Frontend install --frozen-lockfile
Push-Location $Backend
try {
    & $Python -m alembic upgrade head
} finally {
    Pop-Location
}

$ApiPort = Get-AvailablePort $ApiPort
$WebPort = Get-AvailablePort $WebPort
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:$ApiPort"
if (-not $env:NEXT_PUBLIC_AGENT_MODE) {
    $env:NEXT_PUBLIC_AGENT_MODE = if ($env:AGENT_MODE) { $env:AGENT_MODE } else { 'mock' }
}

$Api = Start-Process -FilePath $Python -ArgumentList @(
    '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', $ApiPort, '--workers', '1'
) -WorkingDirectory $Backend -RedirectStandardOutput (Join-Path $Logs 'api.log') -RedirectStandardError (Join-Path $Logs 'api-error.log') -WindowStyle Hidden -PassThru
$Web = Start-Process -FilePath 'pnpm.cmd' -ArgumentList @(
    'dev', '--hostname', '127.0.0.1', '--port', $WebPort
) -WorkingDirectory $Frontend -RedirectStandardOutput (Join-Path $Logs 'web.log') -RedirectStandardError (Join-Path $Logs 'web-error.log') -WindowStyle Hidden -PassThru

Write-Host "Web: http://127.0.0.1:$WebPort"
Write-Host "API: http://127.0.0.1:$ApiPort/docs"
Write-Host "PIDs: api=$($Api.Id), web=$($Web.Id)"
try {
    Wait-Process -Id $Api.Id, $Web.Id
} finally {
    Stop-Process -Id $Api.Id, $Web.Id -Force -ErrorAction SilentlyContinue
}
