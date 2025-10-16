import os
import sqlite3
import json
from typing import Any, Iterable, Iterable as Iter, List, Optional, Dict

# ===== Path DB per server =====
def get_db_path(guild_id: int) -> str:
    return f"/data/narator_{guild_id}.db"

# ===== Low-level helpers =====
def get_conn(guild_id: int) -> sqlite3.Connection:
    path = get_db_path(guild_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def execute(guild_id: int, sql: str, params: Iterable[Any] = ()) -> int:
    """Jalankan 1 statement (INSERT/UPDATE/DELETE). Return lastrowid (kalau ada)."""
    with get_conn(guild_id) as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return cur.lastrowid

def executemany(guild_id: int, sql: str, seq_of_params: Iter[Iter[Any]]) -> None:
    """Jalankan banyak statement sekaligus."""
    with get_conn(guild_id) as conn:
        conn.executemany(sql, seq_of_params)
        conn.commit()

def fetchone(guild_id: int, sql: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    """Ambil satu row (dict) atau None."""
    with get_conn(guild_id) as conn:
        cur = conn.execute(sql, tuple(params))
        row = cur.fetchone()
        return dict(row) if row else None

def fetchall(guild_id: int, sql: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    """Ambil list row (list of dict)."""
    with get_conn(guild_id) as conn:
        cur = conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]

def check_schema(guild_id: int) -> dict:
    """
    Kembalikan dict {tabel: [list kolom]} untuk semua tabel di DB guild ini.
    Bisa dipakai buat debug schema lama.
    """
    result = {}
    with get_conn(guild_id) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        for t in tables:
            cur2 = conn.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in cur2.fetchall()]
            result[t] = cols
    return result

# ===== Aliases untuk kompatibilitas kode lama =====
def query_one(guild_id: int, sql: str, params: Iterable[Any] = ()):
    return fetchone(guild_id, sql, params)

def query_all(guild_id: int, sql: str, params: Iterable[Any] = ()):
    return fetchall(guild_id, sql, params)

# ===== Memory-like helper =====
def save_memory(guild_id: int, user_id, mtype, value, meta=None):
    """Simpan log memory ke DB (per server)."""
    meta_json = json.dumps(meta or {})
    execute(
        guild_id,
        """
        INSERT INTO memories (user_id, type, value, meta, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (user_id, mtype, value, meta_json)
    )

def get_recent(guild_id: int, mtype=None, limit=10):
    """Ambil log terakhir dari DB (per server)."""
    if mtype:
        rows = fetchall(
            guild_id,
            """
            SELECT * FROM memories
            WHERE type=? 
            ORDER BY id DESC LIMIT ?
            """,
            (mtype, limit)
        )
    else:
        rows = fetchall(
            guild_id,
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
        "ally": {"name": "", "hp": 0}
    }
    return templates.get(mtype, {})

# ===== Schema bootstrap & auto-migration =====
def _exec_script(guild_id: int, sql: str) -> None:
    with get_conn(guild_id) as conn:
        conn.executescript(sql)
        conn.commit()

def _ensure_table(guild_id: int, create_sql: str) -> None:
    execute(guild_id, create_sql)

def _ensure_columns(guild_id: int, table: str, columns: Dict[str, str]) -> None:
    """Tambahkan kolom yang belum ada. columns = { 'col_name': 'SQL_TYPE DEFAULT ...'}"""
    info = fetchall(guild_id, f"PRAGMA table_info({table})")
    existing = {c["name"] for c in info}
    for col, decl in columns.items():
        if col not in existing:
            execute(guild_id, f"ALTER TABLE {table} ADD COLUMN {col} {decl}")

def init_db(guild_id: int) -> None:
    from services import hollow_service
    hollow_service.ensure_table(guild_id)
    """
    Buat DB untuk server tertentu jika belum ada, lalu pastikan tabel dan kolom lengkap.
    """
    # 1) Load schema.sql (opsional)
    schema_file = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = f.read()
        _exec_script(guild_id, schema)

    # 2) Characters
    _ensure_table(guild_id, """
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
        carry_capacity INTEGER DEFAULT 0,
        carry_used REAL DEFAULT 0,
        buffs TEXT DEFAULT '[]',
        debuffs TEXT DEFAULT '[]',
        effects TEXT DEFAULT '[]',
        equipment TEXT DEFAULT '{}',
        companions TEXT DEFAULT '[]',
        inventory TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3) Enemies
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS enemies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        hp INTEGER DEFAULT 0,
        hp_max INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 0,
        energy_max INTEGER DEFAULT 0,
        stamina INTEGER DEFAULT 0,
        stamina_max INTEGER DEFAULT 0,
        ac INTEGER DEFAULT 10,
        effects TEXT DEFAULT '[]',
        xp_reward INTEGER DEFAULT 0,
        gold_reward INTEGER DEFAULT 0,
        loot TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4) Allies
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS allies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        hp INTEGER DEFAULT 0,
        hp_max INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 0,
        energy_max INTEGER DEFAULT 0,
        stamina INTEGER DEFAULT 0,
        stamina_max INTEGER DEFAULT 0,
        ac INTEGER DEFAULT 10,
        effects TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5) Quests
    _ensure_table(guild_id, """
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

    # 6) NPC
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS npc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        role TEXT,
        favor INTEGER DEFAULT 0,
        traits TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7) Inventory
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        item TEXT,
        qty INTEGER DEFAULT 1,
        metadata TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8) History
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9) Timeline
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10) Initiative
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_json TEXT DEFAULT '[]',
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 11) Memories
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        type TEXT,
        value TEXT,
        meta TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 12) Favors (FIXED → pakai plural)
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS favors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        char_name TEXT,
        faction TEXT NOT NULL,
        favor INTEGER DEFAULT 0,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, char_name, faction)
    );
    """)

    # 13) Factions
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS factions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        desc TEXT,
        type TEXT DEFAULT 'general',
        hidden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, name)
    );
    """)

        # 4.5) Companions (baru)
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS companions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        owner TEXT,                    -- karakter pemilik
        hp INTEGER DEFAULT 0,
        hp_max INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 0,
        energy_max INTEGER DEFAULT 0,
        stamina INTEGER DEFAULT 0,
        stamina_max INTEGER DEFAULT 0,
        ac INTEGER DEFAULT 10,
        effects TEXT DEFAULT '[]',     -- buff/debuff JSON
        modules TEXT DEFAULT '[]',     -- module JSON
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        zone TEXT,
        type TEXT,
        traits TEXT DEFAULT '[]',
        types TEXT DEFAULT '[]',
        npcs TEXT DEFAULT '[]',
        visitors TEXT DEFAULT '[]',
        events TEXT DEFAULT '[]',
        vendors_today TEXT DEFAULT '[]',
        event_today TEXT DEFAULT '{}',
        visitors_today TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node TEXT,
        vendors TEXT,
        visitors TEXT,
        event TEXT,
        slot TEXT DEFAULT 'day',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 50,
        desc TEXT DEFAULT ''
    );
    """)

    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 10,
        desc TEXT DEFAULT '',
        effect TEXT DEFAULT ''
    );
    """)

    # --- MIGRASI untuk factions lama ---
    info = fetchall(guild_id, "PRAGMA table_info(factions)")
    cols = {c["name"] for c in info}
    if "guild_id" not in cols:
        execute(guild_id, """
            CREATE TABLE IF NOT EXISTS factions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                desc TEXT,
                type TEXT DEFAULT 'general',
                hidden INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, name)
            );
        """)
        execute(guild_id, """
            INSERT INTO factions_new (guild_id, name, desc, type, hidden, created_at)
            SELECT ?, name, desc, type, hidden, created_at
            FROM factions;
        """, (guild_id,))
        execute(guild_id, "DROP TABLE factions")
        execute(guild_id, "ALTER TABLE factions_new RENAME TO factions")

    # 14) Shops
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS npc_shop (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npc_name TEXT NOT NULL,
        item TEXT NOT NULL,
        price INTEGER DEFAULT 0,
        stock INTEGER DEFAULT -1,
        favor_req TEXT DEFAULT '{}',
        quest_req TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(npc_name, item)
    );
    """)

    # 15) Items
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        effect TEXT,
        rarity TEXT DEFAULT 'Common',
        value INTEGER DEFAULT 0,
        weight REAL DEFAULT 0.1,
        slot TEXT,
        notes TEXT,
        rules TEXT,
        requirement TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 16) Skill Library
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS skill_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        name TEXT,
        category TEXT,
        effect TEXT,
        drawback TEXT,
        cost TEXT
    );
    """)

    # 17) Character Skills
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        char_name TEXT,
        skill_id INTEGER,
        category TEXT,
        name TEXT,
        level INTEGER DEFAULT 0
    );
    """)

        # 18) Effects
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS effects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT,
        target_stat TEXT,
        formula TEXT,
        duration INTEGER DEFAULT 0,
        stack_mode TEXT DEFAULT 'add',
        description TEXT,
        max_stack INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, name)
    );
    """)
    
    # 19) Crafting Blueprints
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS blueprints (
        name TEXT PRIMARY KEY,
        desc TEXT,
        req TEXT,
        result TEXT,
        target_progress INTEGER DEFAULT 100
    );
    """)

    # 20) Active Crafting
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS crafting (
        player TEXT PRIMARY KEY,
        blueprint TEXT,
        progress INTEGER DEFAULT 0
    );
    """)

    # 21) Known Blueprints per Player
    _ensure_table(guild_id, """
    CREATE TABLE IF NOT EXISTS known_blueprints (
        player TEXT,
        blueprint TEXT,
        PRIMARY KEY (player, blueprint)
    );
    """)

    # Auto-migrate
    _ensure_columns(guild_id, "factions", {
        "type": "TEXT DEFAULT 'general'"
    })

    _ensure_columns(guild_id, "characters", {
        "effects": "TEXT DEFAULT '[]'",
        "equipment": "TEXT DEFAULT '{}' ",
        "companions": "TEXT DEFAULT '[]'",
        "inventory": "TEXT DEFAULT '[]'",
        "xp": "INTEGER DEFAULT 0",
        "gold": "INTEGER DEFAULT 0",
        "speed": "INTEGER DEFAULT 30",
        "carry_capacity": "INTEGER DEFAULT 0",
        "carry_used": "REAL DEFAULT 0"
    })

    _ensure_columns(guild_id, "enemies", {
        "effects": "TEXT DEFAULT '[]'",
        "xp_reward": "INTEGER DEFAULT 0",
        "gold_reward": "INTEGER DEFAULT 0",
        "loot": "TEXT DEFAULT '[]'"
    })

    _ensure_columns(guild_id, "quests", {
        "assigned_to": "TEXT DEFAULT '[]'",
        "rewards": "TEXT DEFAULT '{}'",
        "favor": "TEXT DEFAULT '{}'",
        "tags": "TEXT DEFAULT '{}'",
        "archived": "INTEGER DEFAULT 0",
        "rewards_visible": "INTEGER DEFAULT 1"
    })

    _ensure_columns(guild_id, "npc", {
        "role": "TEXT",
        "traits": "TEXT DEFAULT '{}'",
        "info": "TEXT DEFAULT '{\"value\": \"\", \"visible\": 1}'",
        "status": "TEXT DEFAULT 'Alive'",
        "affiliation": "TEXT"
    })

    _ensure_columns(guild_id, "effects", {
        "max_stack": "INTEGER DEFAULT 3",
        "description": "TEXT"
    })

    _ensure_columns(guild_id, "favors", {
        "char_name": "TEXT"
    })
    
    _ensure_columns(guild_id, "items", {
        "requirement": "TEXT"
    })

    # Indexes
    # Auto-ensure kolom baru (desc, effect, effect_formula)
    execute(guild_id, "ALTER TABLE hollow_events ADD COLUMN desc TEXT DEFAULT ''") if not any(c['name']=='desc' for c in fetchall(guild_id, 'PRAGMA table_info(hollow_events)')) else None
    execute(guild_id, "ALTER TABLE hollow_events ADD COLUMN effect TEXT DEFAULT ''") if not any(c['name']=='effect' for c in fetchall(guild_id, 'PRAGMA table_info(hollow_events)')) else None
    execute(guild_id, "ALTER TABLE hollow_events ADD COLUMN effect_formula TEXT DEFAULT ''") if not any(c['name']=='effect_formula' for c in fetchall(guild_id, 'PRAGMA table_info(hollow_events)')) else None
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_nodes_name ON hollow_nodes(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_hollow_log_node ON hollow_log(node);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_hollow_log_slot ON hollow_log(slot);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_visitors_name ON hollow_visitors(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_events_name ON hollow_events(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_companion_name ON companions(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_companion_owner ON companions(owner);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_blueprints_name ON blueprints(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_crafting_player ON crafting(player);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_faction_guild_name ON factions(guild_id, name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_name ON quests(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_char_name ON characters(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_enemy_name ON enemies(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_npc_name ON npc(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(owner);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_effects_name ON effects(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_shop_npc ON npc_shop(npc_name);")
