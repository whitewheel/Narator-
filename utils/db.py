# utils/db.py
import os
import sqlite3
import json
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


# ===== Memory-like helper =====
def save_memory(guild_id, channel_id, user_id, mtype, value, meta=None):
    """Simpan log memory ke DB."""
    meta_json = json.dumps(meta or {})
    execute(
        """
        INSERT INTO memories (guild_id, channel_id, user_id, type, value, meta, created_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (guild_id, channel_id, user_id, mtype, value, meta_json)
    )

def get_recent(guild_id, channel_id, mtype=None, limit=10):
    """Ambil log terakhir dari DB berdasarkan tipe."""
    if mtype:
        rows = fetchall(
            """
            SELECT * FROM memories
            WHERE guild_id=? AND channel_id=? AND type=?
            ORDER BY id DESC LIMIT ?
            """,
            (guild_id, channel_id, mtype, limit)
        )
    else:
        rows = fetchall(
            """
            SELECT * FROM memories
            WHERE guild_id=? AND channel_id=?
            ORDER BY id DESC LIMIT ?
            """,
            (guild_id, channel_id, limit)
        )
    return [dict(r) for r in rows]

def template_for(mtype: str) -> dict:
    """Template dasar untuk tipe memory tertentu."""
    templates = {
        "character": {"name": "", "level": 1, "hp": 0},
        "quest": {"name": "", "status": "active"},
        "item": {"name": "", "desc": ""},
        "favor": {"faction": "", "points": 0},
        "enemy": {"name": "", "hp": 0, "xp_reward": 0},
    }
    return templates.get(mtype, {})


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
    3) Pastikan tabel initiative & memories ada.
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

    # 3) Pastikan kolom enemies
    _ensure_columns("enemies", {
        "effects": "TEXT DEFAULT '[]'",
        "xp_reward": "INTEGER DEFAULT 0",
        "gold_reward": "INTEGER DEFAULT 0",
        "loot": "TEXT DEFAULT '[]'",
    })

    # 4) Pastikan kolom quests
    _ensure_columns("quests", {
        "assigned_to": "TEXT DEFAULT '[]'",
        "hidden": "INTEGER DEFAULT 0",
    })

    # 5) Tabel initiative
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

    # 6) Tabel memories
    _ensure_table("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        channel_id TEXT,
        user_id TEXT,
        type TEXT,
        value TEXT,
        meta TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7) Indexes
    execute("CREATE INDEX IF NOT EXISTS idx_char_gcn ON characters(guild_id, channel_id, name);")
    execute("CREATE INDEX IF NOT EXISTS idx_enemy_gcn ON enemies(guild_id, channel_id, name);")
    execute("CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(guild_id, channel_id, owner);")


# ===== Auto-create DB kalau kosong =====
try:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        init_db()
except Exception:
    pass
