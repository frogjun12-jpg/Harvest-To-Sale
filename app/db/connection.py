import os
from contextlib import contextmanager
from typing import Iterator

import mariadb
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> mariadb.Connection:
    return mariadb.connect(
        host=os.getenv("MARIADB_HOST", "localhost"),
        port=int(os.getenv("MARIADB_PORT", "3306")),
        user=os.getenv("MARIADB_USER", "rag_user"),
        password=os.getenv("MARIADB_PASSWORD", "rag_password"),
        database=os.getenv("MARIADB_DATABASE", "fruits_rag"),
    )


@contextmanager
def db_cursor() -> Iterator[mariadb.Cursor]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
