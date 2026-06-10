# Free Edition

Local/offline-first edition for demos and edge PC use.

## Uses

- Local MariaDB
- Ollama local server
- Qwen chat model
- bge-m3 or nomic embedding model
- Shared `app/`, `rag_docs/`, `fruits_data/`

## Setup

Run from the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item editions\free\.env.example .env
```

Edit `.env`, then run:

```powershell
python -m app.db.init_schema
python -m app.rag.ingest_docs
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m streamlit run app/ui/streamlit_app.py --server.port 8501
python -m streamlit run app/ui/shop_app.py --server.port 8502
```

The free edition still uses the same shared RAG documents in `rag_docs/`.

## Docker Mode

Use this when you want the free edition to run without keeping local cmd windows open.

Docker runs FastAPI, Streamlit, and MariaDB. Ollama still runs on the host PC.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_free_docker.ps1
```

URLs:

```text
Admin:  http://localhost:8501
Market: http://localhost:8502
API:    http://localhost:8000/health
```

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_free_docker.ps1
```
