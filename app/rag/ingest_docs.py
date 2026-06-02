import os
from pathlib import Path

from dotenv import load_dotenv

from app.db.vector_search import upsert_document_chunk
from app.rag.embedder import embed_text

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_DOCS_DIR = PROJECT_ROOT / "rag_docs"
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def ingest_markdown_file(path: Path) -> int:
    content = path.read_text(encoding="utf-8")
    chunks = chunk_text(content)
    relative_path = path.relative_to(PROJECT_ROOT).as_posix()

    for index, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        upsert_document_chunk(relative_path, index, chunk, embedding)

    return len(chunks)


def ingest_all() -> None:
    markdown_files = sorted(RAG_DOCS_DIR.glob("**/*.md"))
    if not markdown_files:
        print(f"No Markdown files found in {RAG_DOCS_DIR}")
        return

    total_chunks = 0
    for path in markdown_files:
        chunk_count = ingest_markdown_file(path)
        total_chunks += chunk_count
        print(f"Ingested {chunk_count} chunks from {path.name}")

    print(f"Done. Ingested {total_chunks} chunks from {len(markdown_files)} files.")


if __name__ == "__main__":
    ingest_all()
