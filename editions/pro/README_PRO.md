# Pro Edition

Cloud/server-oriented edition using GPT API and OpenAI embeddings.

## Uses

- Docker Compose
- MariaDB container
- FastAPI container
- Streamlit admin/shop containers
- OpenAI chat model
- OpenAI embedding model
- Shared `app/`, `rag_docs/`, `fruits_data/`

## Does Pro Use Local RAG?

Yes, in the current project structure.

`rag_docs/` and `fruits_data/` are shared source files. When the Pro Docker stack starts, the Docker image copies those folders into the containers. The API container then ingests `rag_docs/` into the MariaDB container using OpenAI embeddings.

So the difference is not the document source. The difference is:

- Free: local Ollama chat + local Ollama embedding
- Pro: OpenAI GPT chat + OpenAI embedding

Later, Pro can be changed to pull RAG documents from an admin upload page, cloud object storage, or a managed database instead of repository files.

## Setup

Run from the project root:

```powershell
Copy-Item editions\pro\.env.pro.example editions\pro\.env.pro
```

Edit `editions/pro/.env.pro` and set at least:

```env
OPENAI_API_KEY=...
MARIADB_PASSWORD=change-this-password
MARIADB_ROOT_PASSWORD=change-this-root-password
```

Start:

```powershell
docker compose --env-file editions/pro/.env.pro -f editions/pro/docker-compose.pro.yml up -d --build
```

Status:

```powershell
docker compose --env-file editions/pro/.env.pro -f editions/pro/docker-compose.pro.yml ps
docker compose --env-file editions/pro/.env.pro -f editions/pro/docker-compose.pro.yml logs -f api
```

URLs:

```text
Admin Pro: http://localhost:8601
Shop Pro:  http://localhost:8602
FastAPI:   http://localhost:8000/health
```

Cloud access uses the server public IP or domain instead of `localhost`.
