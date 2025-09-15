import os
import psycopg2
from psycopg2.extras import RealDictCursor

# 🔧 Buat koneksi ke Postgres pakai ENV dari Railway
def get_conn():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        cursor_factory=RealDictCursor
    )

# 🔨 Eksekusi query (INSERT, UPDATE, DELETE)
def execute(sql: str, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount  # jumlah row terpengaruh

# 🔍 Ambil satu row
def query_one(sql: str, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

# 📋 Ambil banyak row
def query_all(sql: str, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
