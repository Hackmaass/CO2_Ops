# CO2Ops - Local Development Runner
# Launches the authenticated CO2Ops Backend (co2ops_agent/server.py) on port 8080
# and the Streamlit Frontend on port 8501.

$VenvDir = Join-Path $PSScriptRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvStreamlit = Join-Path $VenvDir "Scripts\streamlit.exe"
$ServerScript = Join-Path $PSScriptRoot "co2ops_agent\server.py"
$EnvFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Virtual Environment at $VenvDir..." -ForegroundColor Cyan
    python -m venv $VenvDir
}

Write-Host "Activating Virtual Environment..." -ForegroundColor Green
& (Join-Path $VenvDir "Scripts\Activate.ps1")

Write-Host "Ensuring dependencies are installed..." -ForegroundColor Cyan
& $VenvPython -m pip install -q -r (Join-Path $PSScriptRoot "co2ops_agent\requirements.txt")
& $VenvPython -m pip install -q -r (Join-Path $PSScriptRoot "Frontend\requirements.txt")

if (-not (Test-Path $EnvFile)) {
    Write-Host "`nNo .env file found at $EnvFile." -ForegroundColor Red
    Write-Host "Copy .env.example to .env and set GEMINI_API_KEY and CO2OPS_API_KEY first -" -ForegroundColor Red
    Write-Host "the backend refuses all requests until CO2OPS_API_KEY is set." -ForegroundColor Red
}

$env:PYTHONIOENCODING = "utf-8"

Write-Host "`nStarting CO2Ops Backend (authenticated) on http://127.0.0.1:8080..." -ForegroundColor Yellow
$BackendJob = Start-Job -Name "CO2Ops_Backend" -ScriptBlock {
    param($ServerScript, $PythonExe)
    $env:PYTHONIOENCODING = "utf-8"
    $env:HOST = "127.0.0.1"
    $env:PORT = "8080"
    & $PythonExe $ServerScript
} -ArgumentList $ServerScript, $VenvPython

Start-Sleep -Seconds 3

Write-Host "Starting Streamlit Workspace on http://localhost:8501..." -ForegroundColor Yellow
Write-Host "Open http://localhost:8501 in your browser to access the CO2Ops Workspace." -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate both servers.`n" -ForegroundColor DarkGray

try {
    & $VenvStreamlit run (Join-Path $PSScriptRoot "Frontend\app.py") --server.port 8501
} finally {
    Write-Host "`nShutting down CO2Ops Backend..." -ForegroundColor Yellow
    Stop-Job -Name "CO2Ops_Backend" -ErrorAction SilentlyContinue
    Remove-Job -Name "CO2Ops_Backend" -ErrorAction SilentlyContinue
    Write-Host "CO2Ops servers terminated cleanly." -ForegroundColor Green
}
