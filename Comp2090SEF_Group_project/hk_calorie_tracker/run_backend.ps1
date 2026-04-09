$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not $env:HK_TRACKER_API_PORT) {
    $env:HK_TRACKER_API_PORT = '5050'
}

$forwardArgs = @($args)

$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $pythonExe) {
    & $pythonExe 'api_server.py' @forwardArgs
    exit $LASTEXITCODE
}

python 'api_server.py' @forwardArgs
