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


def delete_document_chunks(source_path: str) -> None:
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM rag_documents WHERE source_path = ?", (source_path,))


def delete_chunks_except_sources(source_paths: list[str]) -> int:
    if not source_paths:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM rag_documents")
            return int(cursor.rowcount)

    placeholders = ",".join(["?"] * len(source_paths))
    with db_cursor() as cursor:
        cursor.execute(
            f"DELETE FROM rag_documents WHERE source_path NOT IN ({placeholders})",
            tuple(source_paths),
        )
        return int(cursor.rowcount)


def search_similar_chunks(
    embedding: list[float],
    top_k: int,
    distance_threshold: float | None = None,
) -> list[dict]:
    params: list = [vector_literal(embedding)]
    where_clause = ""
    if distance_threshold is not None:
        where_clause = "WHERE distance <= ?"
        params.append(distance_threshold)

    params.append(top_k)
    sql = """
        SELECT source_path, chunk_index, content, distance
        FROM (
            SELECT
                source_path,
                chunk_index,
                content,
                VEC_DISTANCE_COSINE(embedding, VEC_FromText(?)) AS distance
            FROM rag_documents
        ) AS ranked_chunks
        {where_clause}
        ORDER BY distance ASC
        LIMIT ?
    """.format(where_clause=where_clause)
    with db_cursor() as cursor:
        cursor.execute(sql, tuple(params))
        return list(cursor.fetchall())
