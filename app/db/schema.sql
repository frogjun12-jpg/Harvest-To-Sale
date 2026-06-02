CREATE TABLE IF NOT EXISTS rag_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_path VARCHAR(512) NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_source_chunk (source_path, chunk_index),
    VECTOR INDEX (embedding) M=8 DISTANCE=cosine
);
