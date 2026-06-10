import os
from pathlib import Path

from app.config import load_app_env
from app.db.connection import db_cursor

load_app_env()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "app" / "db" / "schema.sql"


def load_schema_sql() -> str:
    embedding_dim = os.getenv("RAG_EMBEDDING_DIM", "1024")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    return sql.replace("VECTOR(1024)", f"VECTOR({embedding_dim})")


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";").strip())
            current = []
    if current:
        statements.append("\n".join(current).strip())
    return statements


def main() -> None:
    statements = split_sql_statements(load_schema_sql())
    with db_cursor() as cursor:
        if os.getenv("RAG_RECREATE_VECTOR_TABLE", "false").lower() == "true":
            cursor.execute("DROP TABLE IF EXISTS rag_documents")
        for statement in statements:
            cursor.execute(statement)
    print(f"Applied {len(statements)} schema statements.")


if __name__ == "__main__":
    main()
