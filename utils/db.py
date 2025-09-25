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
def save_memory(user_id, mtype, value, meta=None):
    """Simpan log memory ke DB (global, tanpa guild/channel)."""
    meta_json = json.dumps(meta or {})
    execute(
        """
        INSERT INTO memories (user_id, type, value, meta, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (user_id, mtype, value, meta_json)
    )

def get_recent(mtype=None, limit=10):
    """Ambil log terakhir dari DB berdasarkan tipe (global)."""
    if mtype:
        rows = fetchall(
            """
            SELECT * FROM memories
            WHERE type=? 
            ORDER BY id DESC LIMIT ?
            """,
            (mtype, limit)
        )
    else:
        rows = fetchall(
            """
            SELECT * FROM memories
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
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
    2) Pastikan tabel global ada.
    3) Pastikan kolom tambahan yang dipakai cogs sudah ada (auto-migrate).
    """
    # 1) Load schema.sql (opsional)
    schema_file = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        _exec_script(schema)

    # 2) Tabel dasar (global)
    _ensure_table("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        class TEXT,
        race TEXT,
        level INTEGER DEFAULT 1,
        hp INTEGER DEFAULT 0,
        hp_max INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 0,
        energy_max INTEGER DEFAULT 0,
        stamina INTEGER DEFAULT 0,
        stamina_max INTEGER DEFAULT 0,
        str INTEGER DEFAULT 0,
        dex INTEGER DEFAULT 0,
        con INTEGER DEFAULT 0,
        int INTEGER DEFAULT 0,
        wis INTEGER DEFAULT 0,
        cha INTEGER DEFAULT 0,
        ac INTEGER DEFAULT 10,
        init_mod INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 0,
        speed INTEGER DEFAULT 30,
        buffs TEXT DEFAULT '[]',
        debuffs TEXT DEFAULT '[]',
        effects TEXT DEFAULT '[]',
        equipment TEXT DEFAULT '{}',
        companions TEXT DEFAULT '[]',
        inventory TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS enemies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        hp INTEGER DEFAULT 0,
        hp_max INTEGER DEFAULT 0,
        ac INTEGER DEFAULT 10,
        effects TEXT DEFAULT '[]',
        xp_reward INTEGER DEFAULT 0,
        gold_reward INTEGER DEFAULT 0,
        loot TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        desc TEXT,
        status TEXT,
        assigned_to TEXT DEFAULT '[]',
        rewards TEXT DEFAULT '{}',
        favor TEXT DEFAULT '{}',
        tags TEXT DEFAULT '{}',
        archived INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS npc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        role TEXT,
        favor INTEGER DEFAULT 0,
        traits TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        item TEXT,
        qty INTEGER DEFAULT 1,
        metadata TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_json TEXT DEFAULT '[]',
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        type TEXT,
        value TEXT,
        meta TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3) Auto-migrate kolom tambahan
    _ensure_columns("characters", {
        "effects": "TEXT DEFAULT '[]'",
        "equipment": "TEXT DEFAULT '{}'",
        "companions": "TEXT DEFAULT '[]'",
        "inventory": "TEXT DEFAULT '[]'",
        "xp": "INTEGER DEFAULT 0",
        "gold": "INTEGER DEFAULT 0",
        "speed": "INTEGER DEFAULT 30"
    })

    _ensure_columns("enemies", {
        "effects": "TEXT DEFAULT '[]'",
        "xp_reward": "INTEGER DEFAULT 0",
        "gold_reward": "INTEGER DEFAULT 0",
        "loot": "TEXT DEFAULT '[]'"
    })

    _ensure_columns("quests", {
        "assigned_to": "TEXT DEFAULT '[]'",
        "rewards": "TEXT DEFAULT '{}'",
        "favor": "TEXT DEFAULT '{}'",
        "tags": "TEXT DEFAULT '{}'",
        "archived": "INTEGER DEFAULT 0"
    })

    _ensure_columns("npc", {
        "role": "TEXT",
        "favor": "INTEGER DEFAULT 0",
        "traits": "TEXT DEFAULT '{}'"
    })

    # --- MIGRASI QUESTS (lama -> baru) ---
    info = fetchall("PRAGMA table_info(quests)")
    cols = {c["name"] for c in info}

    if "name" not in cols:
        execute("ALTER TABLE quests ADD COLUMN name TEXT")
        if "title" in cols:
            execute("UPDATE quests SET name = COALESCE(name, title)")

    if "desc" not in cols:
        execute("ALTER TABLE quests ADD COLUMN desc TEXT")
        if "detail" in cols:
            execute("UPDATE quests SET desc = COALESCE(desc, detail)")

    _ensure_columns("quests", {
        "assigned_to": "TEXT DEFAULT '[]'",
        "rewards": "TEXT DEFAULT '{}'",
        "favor": "TEXT DEFAULT '{}'",
        "tags": "TEXT DEFAULT '{}'",
        "archived": "INTEGER DEFAULT 0"
    })

    execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_name ON quests(name);")

    # 4) Indexes
    execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_char_name ON characters(name);")
    execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_enemy_name ON enemies(name);")
    execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_npc_name ON npc(name);")
    execute("CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(owner);")


# ===== Auto-create DB kalau kosong =====
try:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        init_db()
except Exception:
    pass
