import os

from dotenv import load_dotenv

from app.db.vector_search import search_similar_chunks
from app.rag.embedder import embed_text

load_dotenv()

TOP_K = int(os.getenv("RAG_TOP_K", "4"))


def retrieve_context(question: str, top_k: int = TOP_K) -> list[dict]:
    question_embedding = embed_text(question)
    return search_similar_chunks(question_embedding, top_k)
