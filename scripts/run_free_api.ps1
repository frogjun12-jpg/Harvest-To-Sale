$ErrorActionPreference = "Continue"
Set-Location (Resolve-Path "$PSScriptRoot\..")
$env:APP_ENV_FILE = ".env"
$env:APP_EDITION = "free"
$env:SHOP_EDITION = "free"
$env:LLM_PROVIDER = "ollama"
$env:EMBEDDING_PROVIDER = "ollama"
$env:CHAT_API_URL = "http://localhost:8000/chat"
$LogDir = Join-Path (Get-Location) "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 *> (Join-Path $LogDir "free_api.log")
