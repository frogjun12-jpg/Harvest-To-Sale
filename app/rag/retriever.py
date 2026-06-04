import os

from dotenv import load_dotenv

from app.db.vector_search import search_similar_chunks
from app.rag.embedder import embed_text

load_dotenv()

TOP_K = int(os.getenv("RAG_TOP_K", "4"))
DISTANCE_THRESHOLD = float(os.getenv("RAG_DISTANCE_THRESHOLD", "0.52"))


def retrieve_context(
    question: str,
    top_k: int = TOP_K,
    distance_threshold: float | None = DISTANCE_THRESHOLD,
) -> list[dict]:
    question_embedding = embed_text(question)
    return search_similar_chunks(question_embedding, top_k, distance_threshold)
