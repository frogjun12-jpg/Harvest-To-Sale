$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path "$PSScriptRoot\..").Path
$Python = (Get-Command python).Source

$Ports = @(8000, 8501, 8502)
foreach ($Port in $Ports) {
    $Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Connection) {
        Stop-Process -Id $Connection.OwningProcess -Force
    }
}

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "scripts\\run_free_(api|admin|shop)\.ps1" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$env:APP_ENV_FILE = ".env"
$env:APP_EDITION = "free"
$env:SHOP_EDITION = "free"
$env:LLM_PROVIDER = "ollama"
$env:EMBEDDING_PROVIDER = "ollama"
$env:CHAT_API_URL = "http://localhost:8000/chat"

Start-Process -FilePath $Python -ArgumentList @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000"
) -WorkingDirectory $ProjectDir -WindowStyle Hidden

Start-Process -FilePath $Python -ArgumentList @(
    "-m",
    "streamlit",
    "run",
    "app/ui/streamlit_app.py",
    "--server.address",
    "127.0.0.1",
    "--server.port",
    "8501",
    "--server.headless",
    "true"
) -WorkingDirectory $ProjectDir -WindowStyle Hidden

Start-Process -FilePath $Python -ArgumentList @(
    "-m",
    "streamlit",
    "run",
    "app/ui/shop_app.py",
    "--server.address",
    "127.0.0.1",
    "--server.port",
    "8502",
    "--server.headless",
    "true"
) -WorkingDirectory $ProjectDir -WindowStyle Hidden

Start-Sleep -Seconds 8
powershell -NoProfile -ExecutionPolicy Bypass -File "$ProjectDir\scripts\status_free_servers.ps1"
