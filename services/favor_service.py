import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event
from services import faction_service   # supaya bisa auto-create faction

ICONS = {
    "favor": "💠",
    "add": "➕",
    "set": "⚖️",
    "remove": "🗑️",
}

# ---------- Setup ----------
def ensure_table(guild_id: int):
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS favors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            char_name TEXT NOT NULL,
            faction TEXT NOT NULL,
            favor INTEGER DEFAULT 0,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, char_name, faction)
        )
    """)
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_favor_char ON favor(char_name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_favor_faction ON favor(faction);")

# ---------- Helper ----------
def favor_status(value: int) -> str:
    if value <= -10:
        return "Hostile 😡"
    elif value < 0:
        return "Unfriendly 😒"
    elif value < 5:
        return "Neutral 😐"
    elif value < 10:
        return "Friendly 🙂"
    else:
        return "Allied 🤝"

# ---------- CRUD ----------
async def add_or_set_favor(guild_id: int, char_name: str, faction: str, value: int, notes: str = ""):
    ensure_table(guild_id)

    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    execute(
        guild_id,
        """
        INSERT INTO favors (guild_id, char_name, faction, favor, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(guild_id, char_name, faction)
        DO UPDATE SET favor=excluded.favor,
                      notes=excluded.notes,
                      updated_at=CURRENT_TIMESTAMP
        """,
        (guild_id, char_name, faction, value, notes)
    )
    log_event(
        guild_id,
        char_name,
        code=f"FAVOR_SET_{faction.upper()}",
        title=f"{ICONS['favor']} Favor {char_name}:{faction} → {value}",
        details=notes,
        etype="favor_set",
        actors=[char_name, faction],
        tags=["favor", "set"]
    )
    return f"{ICONS['favor']} Favor {faction} untuk **{char_name}** di-set ke `{value}`."

async def mod_favor(guild_id: int, char_name: str, faction: str, delta: int, notes: str = ""):
    ensure_table(guild_id)

    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    execute(
        guild_id,
        """
        INSERT INTO favors (guild_id, char_name, faction, favor, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(guild_id, char_name, faction)
        DO UPDATE SET favor=favors.favor + excluded.favor,
                      notes=excluded.notes,
                      updated_at=CURRENT_TIMESTAMP
        """,
        (guild_id, char_name, faction, delta, notes)
    )
    row = fetchone(guild_id, "SELECT favor FROM favors WHERE guild_id=? AND char_name=? AND faction=?", (guild_id, char_name, faction))
    return f"{ICONS['favor']} Favor {faction} untuk **{char_name}** berubah {delta:+d} → `{row['favor']}`."

async def remove_favor(guild_id: int, char_name: str, faction: str):
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM favors WHERE guild_id=? AND char_name=? AND faction=?", (guild_id, char_name, faction))
    return f"{ICONS['remove']} Favor {faction} untuk **{char_name}** dihapus."

# ---------- Query ----------
async def list_favors(guild_id: int, char_name: str = None):
    ensure_table(guild_id)
    if char_name:
        return fetchall(guild_id, "SELECT * FROM favors WHERE guild_id=? AND char_name=?", (guild_id, char_name))
    return fetchall(guild_id, "SELECT * FROM favors WHERE guild_id=?", (guild_id,))

async def get_detail(guild_id: int, faction: str, char_name: str = None):
    ensure_table(guild_id)
    if char_name:
        return fetchone(guild_id, "SELECT * FROM favors WHERE guild_id=? AND char_name=? AND faction=?", (guild_id, char_name, faction))
    return fetchall(guild_id, "SELECT * FROM favors WHERE guild_id=? AND faction=?", (guild_id, faction))

async def list_all_favors(guild_id: int):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM favors WHERE guild_id=?", (guild_id,))

async def list_factions_status(guild_id: int, char_name: str, factions: list):
    ensure_table(guild_id)
    out = []
    for fac in factions:
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE guild_id=? AND char_name=? AND faction=?", (guild_id, char_name, fac))
        val = row["favor"] if row else 0
        status = favor_status(val)
        out.append((fac, val, status))
    return out

# ---------- Quest Integration ----------
async def add_favor(guild_id: int, targets: list, faction: str, value: int):
    ensure_table(guild_id)

    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    result = []
    for ch in targets:
        execute(
            guild_id,
            """
            INSERT INTO favors (guild_id, char_name, faction, favor, notes, updated_at)
            VALUES (?, ?, ?, ?, 'Quest reward', CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, char_name, faction)
            DO UPDATE SET favor=favors.favor + excluded.favor,
                          updated_at=CURRENT_TIMESTAMP
            """,
            (guild_id, ch, faction, value)
        )
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE guild_id=? AND char_name=? AND faction=?", (guild_id, ch, faction))
        result.append(f"{ch}: {row['favor']}")
    return f"{ICONS['favor']} Favor {faction} ditambahkan → " + ", ".join(result)
