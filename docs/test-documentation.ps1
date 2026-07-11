$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$required = @(
    'README.md',
    'docs/components.md',
    'docs/api-integration.md',
    'docs/deployment.md',
    'docs/demo-script.md',
    'backend/.env.example',
    'Course-Agent/creative/.env.example'
)

$missing = $required | Where-Object { -not (Test-Path -LiteralPath $_) }
if ($missing) {
    throw "Missing documentation: $($missing -join ', ')"
}

$checks = @{
    'README.md' = @('Zhixue Engine', 'start.ps1', 'docker compose', 'AGENT_MODE')
    'docs/components.md' = @('ProfilePanel', 'AgentProgress', 'QaDrawer', 'ResourceCard')
    'docs/api-integration.md' = @(
        '/api/chat/profile',
        '/api/resource/generate',
        '/api/resource/progress/{task_id}',
        '/api/chat/qa',
        '/api/eval/report',
        '/api/course/base',
        'Last-Event-ID',
        'AGENT_MODE',
        'media_url'
    )
    'docs/deployment.md' = @('ALLOW_MOCK_FALLBACK', 'REMOTE_AGENT_BASE_URL', 'COURSE_ROOT', 'HTTPS')
    'docs/demo-script.md' = @('/login', '/profile', '/workspace', '/path', 'QaDrawer', '/evaluation', '/knowledge')
}

foreach ($path in $checks.Keys) {
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    foreach ($needle in $checks[$path]) {
        if (-not $content.Contains($needle)) {
            throw "$path is missing required content: $needle"
        }
    }
}

$allDocumentation = ($required | Where-Object { $_ -like '*.md' }) + @(
    'backend/.env.example',
    'Course-Agent/creative/.env.example'
)
$placeholderPattern = @('T' + 'BD', 'T' + 'ODO', 'FIX' + 'ME') -join '|'
$placeholders = Select-String -Path $allDocumentation -Pattern $placeholderPattern
if ($placeholders) {
    throw "Documentation contains unfinished placeholders: $($placeholders.Path -join ', ')"
}

Write-Host 'Documentation acceptance checks passed.'
