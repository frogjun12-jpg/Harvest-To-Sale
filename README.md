# Fruits Local LLM RAG MVP

AI 기반 과일 자동 수확, 선별, 가격산정, 판매등록 시스템을 위한 Local LLM + RAG 챗봇 MVP입니

## Stack

- Python
- FastAPI
- MariaDB 11.8+ with Vector
- Ollama
- Qwen2.5 7B or Qwen3 8B
- bge-m3 or nomic-embed-text
- Streamlit

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에서 MariaDB와 Ollama 설정을 수정합니다.

## MariaDB Schema

MariaDB에 접속한 뒤 `app/db/schema.sql`을 실행합니다.

```sql
SOURCE app/db/schema.sql;
```

## Ollama Models

```powershell
ollama pull qwen2.5:7b
ollama pull bge-m3
```

`nomic-embed-text`를 사용하려면 `.env`의 `OLLAMA_EMBEDDING_MODEL`을 변경하고 해당 모델을 pull 하세요.

## Add RAG Documents

`rag_docs/` 폴더에 Markdown 파일을 넣습니다. 예시 문서가 포함되어 있습니다.

## Ingest Documents

```powershell
python -m app.rag.ingest_docs
```

## Run FastAPI

```powershell
uvicorn app.main:app --reload
```

## Run Streamlit UI

```powershell
streamlit run app/ui/streamlit_app.py
```

## API

### POST `/chat`

Request:

```json
{
  "question": "사과의 당도 기준은 어떻게 되나요?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "source_path": "rag_docs/sample_fruit_policy.md",
      "chunk_index": 0,
      "content": "...",
      "distance": 0.12
    }
  ]
}
```
