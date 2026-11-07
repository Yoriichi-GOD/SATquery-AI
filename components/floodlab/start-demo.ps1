$ErrorActionPreference = 'Stop'
$floodRoot = $PSScriptRoot
New-Item -ItemType Directory -Force (Join-Path $floodRoot '.runtime') | Out-Null
function Test-FloodService($url, $field, $expected) {
    try {
        $response=Invoke-RestMethod $url -TimeoutSec 3
        if ($response.$field -ne $expected) { throw "Unexpected service at $url" }
        return $true
    } catch {
        if ($_.Exception.Message -like 'Unexpected service*') { throw }
        return $false
    }
}
$workspaceWsl='/mnt/c/Users/nrgen/.codex/scratch/satquery-flood-lab'
if (!(Test-FloodService 'http://localhost:8770/api/health' 'service' 'satquery-flood-lab')) {
    Start-Process -FilePath wsl.exe -ArgumentList @('-d','Ubuntu','--cd',$workspaceWsl,'--','/root/satquery-flood-lab/venv/bin/python','-m','uvicorn','floodlab.server:app','--host','127.0.0.1','--port','8770') -WindowStyle Hidden -RedirectStandardOutput "$floodRoot\.runtime\server-out.log" -RedirectStandardError "$floodRoot\.runtime\server-error.log"
}
if (!(Test-FloodService 'http://localhost:8771/health' 'purpose' 'AI question routing only; numbers rendered from frozen map evidence')) {
    Start-Process -FilePath wsl.exe -ArgumentList @('-d','Ubuntu','--cd',$workspaceWsl,'--','/root/satquery/.venv/bin/python','-m','uvicorn','floodlab.ai_worker:app','--host','127.0.0.1','--port','8771') -WindowStyle Hidden -RedirectStandardOutput "$floodRoot\.runtime\ai-out.log" -RedirectStandardError "$floodRoot\.runtime\ai-error.log"
}
$ready=$false
for($attempt=0;$attempt -lt 20;$attempt++) {
    if (Test-FloodService 'http://localhost:8770/api/health' 'service' 'satquery-flood-lab') { $ready=$true; break }
    Start-Sleep -Milliseconds 500
}
if (!$ready) { throw 'Flood server failed to become ready. Inspect .runtime/server-error.log.' }
Write-Host 'Workspace is ready: http://localhost:8770/'
Write-Host 'AI loads on the first question. Explicit topic answers remain available if AI is unavailable.'
