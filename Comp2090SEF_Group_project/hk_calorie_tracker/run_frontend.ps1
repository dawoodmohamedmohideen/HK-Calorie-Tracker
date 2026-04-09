$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$forwardArgs = @($args)

$streamlitExe = Join-Path $PSScriptRoot '.venv\Scripts\streamlit.exe'
if (Test-Path $streamlitExe) {
	& $streamlitExe 'run' 'streamlit_app.py' @forwardArgs
	exit $LASTEXITCODE
}

$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $pythonExe) {
	& $pythonExe '-m' 'streamlit' 'run' 'streamlit_app.py' @forwardArgs
	exit $LASTEXITCODE
}

python '-m' 'streamlit' 'run' 'streamlit_app.py' @forwardArgs
