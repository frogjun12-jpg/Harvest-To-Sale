@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=C:\Users\kccistc1\miniconda3\python.exe"
set "APP_ENV_FILE=.env"
set "APP_EDITION=free"
set "SHOP_EDITION=free"
set "LLM_PROVIDER=ollama"
set "EMBEDDING_PROVIDER=ollama"
set "CHAT_API_URL=http://localhost:8000/chat"

if not exist "%PYTHON_EXE%" (
  set "PYTHON_EXE=python"
)

start "Manage Apple Free API" cmd /k "cd /d ""%PROJECT_DIR%"" && ""%PYTHON_EXE%"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "Manage Apple Free Admin" cmd /k "cd /d ""%PROJECT_DIR%"" && ""%PYTHON_EXE%"" -m streamlit run app/ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true"
start "Manage Apple Free Market" cmd /k "cd /d ""%PROJECT_DIR%"" && ""%PYTHON_EXE%"" -m streamlit run app/ui/shop_app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true"

echo Free edition servers are starting.
echo Admin:  http://127.0.0.1:8501
echo Market: http://127.0.0.1:8502
echo API:    http://127.0.0.1:8000/health
