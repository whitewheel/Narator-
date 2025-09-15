import sqlite3
import os
from typing import Any, Iterable

# Path DB diarahkan ke Volume Railway
DB_PATH = "/data/narator.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

def query_one(sql: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

def query_all(sql: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

def init_db():
    schema_file = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        with get_conn() as conn:
            conn.executescript(schema)

# Auto-create DB kalau belum ada
if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
    os.makedirs("/data", exist_ok=True)
    init_db()
