# utils/db.py
import os
import sqlite3
from typing import Any, Iterable, Iterable as Iter, List, Optional, Dict

# ===== Path DB di volume (Railway / Docker) =====
DB_PATH = os.getenv("DB_PATH", "/data/narator.db")


# ===== Low-level helpers =====
def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """Jalankan 1 statement (INSERT/UPDATE/DELETE). Return lastrowid (kalau ada)."""
    with get_conn() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.lastrowid

def executemany(sql: str, seq_of_params: Iter[Iter[Any]]) -> None:
    """Jalankan banyak statement sekaligus."""
    with get_conn() as conn:
        conn.executemany(sql, seq_of_params)

def fetchone(sql: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    """Ambil satu row (dict) atau None."""
    with get_conn() as conn:
        cur = conn.execute(sql, tuple(params))
        row = cur.fetchone()
        return dict(row) if row else None

def fetchall(sql: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    """Ambil list row (list of dict)."""
    with get_conn() as conn:
        cur = conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]

# ===== Aliases untuk kompatibilitas kode lama =====
def query_one(sql: str, params: Iterable[Any] = ()):
    return fetchone(sql, params)

def query_all(sql: str, params: Iterable[Any] = ()):
    return fetchall(sql, params)


# ===== Schema bootstrap & auto-migration =====
def _exec_script(sql: str) -> None:
    with get_conn() as conn:
        conn.executescript(sql)

def _ensure_table(create_sql: str) -> None:
    execute(create_sql)

def _ensure_columns(table: str, columns: Dict[str, str]) -> None:
    """Tambahkan kolom yang belum ada. columns = { 'col_name': 'SQL_TYPE DEFAULT ...'}"""
    info = fetchall(f"PRAGMA table_info({table})")
    existing = {c["name"] for c in info}
    for col, decl in columns.items():
        if col not in existing:
            execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")

def init_db() -> None:
    """
    1) Jalankan schema.sql kalau ada.
    2) Pastikan kolom-kolom tambahan yang dipakai cogs sudah ada (auto-migrate).
    3) Pastikan tabel initiative ada.
    """
    # 1) Load schema.sql (opsional)
    schema_file = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        _exec_script(schema)

    # 2) Auto-migrate kolom characters yang dipakai di cogs
    _ensure_columns("characters", {
        "energy": "INTEGER DEFAULT 0",
        "energy_max": "INTEGER DEFAULT 0",
        "stamina": "INTEGER DEFAULT 0",
        "stamina_max": "INTEGER DEFAULT 0",
        "buffs": "TEXT DEFAULT '[]'",
        "debuffs": "TEXT DEFAULT '[]'",
        "level": "INTEGER DEFAULT 1",
        "xp": "INTEGER DEFAULT 0",
        "gold": "INTEGER DEFAULT 0",
        "speed": "INTEGER DEFAULT 30",
        "equipment": "TEXT DEFAULT '{}'",
        "companions": "TEXT DEFAULT '[]'",
        "inventory": "TEXT DEFAULT '[]'",
    })

    # 3) Pastikan kolom enemies yang dipakai
    _ensure_columns("enemies", {
        "effects": "TEXT DEFAULT '[]'",
        "xp_reward": "INTEGER DEFAULT 0",
        "gold_reward": "INTEGER DEFAULT 0",
        "loot": "TEXT DEFAULT '[]'",
    })

    # 4) Pastikan kolom quests (assigned_to, hidden mungkin belum ada di schema lama)
    _ensure_columns("quests", {
        "assigned_to": "TEXT DEFAULT '[]'",
        "hidden": "INTEGER DEFAULT 0",
    })

    # 5) Tabel initiative untuk init_service / initmem baru
    _ensure_table("""
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        channel_id TEXT,
        order_json TEXT DEFAULT '[]',
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_initiative_gc
    ON initiative(guild_id, channel_id);
    """)

    # 6) Nice-to-have indexes
    execute("CREATE INDEX IF NOT EXISTS idx_char_gcn ON characters(guild_id, channel_id, name);")
    execute("CREATE INDEX IF NOT EXISTS idx_enemy_gcn ON enemies(guild_id, channel_id, name);")
    execute("CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(guild_id, channel_id, owner);")


# ===== Auto-create DB kalau kosong =====
# Kalau file belum ada / kosong, pastikan folder /data ada, lalu init_db()
try:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        init_db()
except Exception:
    # Jangan matiin proses kalau gagal cek; init_db akan dipanggil dari main juga.
    pass
