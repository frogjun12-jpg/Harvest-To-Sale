import json

from app.db.connection import db_cursor


def vector_literal(embedding: list[float]) -> str:
    return json.dumps(embedding, separators=(",", ":"))


def upsert_document_chunk(
    source_path: str,
    chunk_index: int,
    content: str,
    embedding: list[float],
) -> None:
    sql = """
        INSERT INTO rag_documents (source_path, chunk_index, content, embedding)
        VALUES (?, ?, ?, VEC_FromText(?))
        ON DUPLICATE KEY UPDATE
            content = VALUES(content),
            embedding = VALUES(embedding)
    """
    with db_cursor() as cursor:
        cursor.execute(sql, (source_path, chunk_index, content, vector_literal(embedding)))


def search_similar_chunks(embedding: list[float], top_k: int) -> list[dict]:
    sql = """
        SELECT
            source_path,
            chunk_index,
            content,
            VEC_DISTANCE_COSINE(embedding, VEC_FromText(?)) AS distance
        FROM rag_documents
        ORDER BY distance ASC
        LIMIT ?
    """
    with db_cursor() as cursor:
        cursor.execute(sql, (vector_literal(embedding), top_k))
        return list(cursor.fetchall())
