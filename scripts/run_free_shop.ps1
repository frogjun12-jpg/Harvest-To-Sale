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
python -m streamlit run app/ui/shop_app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true *> (Join-Path $LogDir "free_shop.log")
