import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event

ICONS = {
    "favor": "💠",
    "add": "➕",
    "set": "⚖️",
    "remove": "🗑️",
}

def ensure_table(guild_id: int):
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS favors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            faction TEXT NOT NULL,
            favor INTEGER DEFAULT 0,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, faction)
        )
    """)
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_favor_user ON favors(user_id);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_favor_faction ON favors(faction);")

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
async def add_or_set_favor(guild_id: int, user_id: int, faction: str, value: int, notes: str = ""):
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT * FROM favors WHERE user_id=? AND faction=?", (user_id, faction))
    if row:
        execute(guild_id,
                "UPDATE favors SET favor=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND faction=?",
                (value, notes, user_id, faction))
        action = "set"
    else:
        execute(guild_id,
                "INSERT INTO favors (user_id, faction, favor, notes) VALUES (?,?,?,?)",
                (user_id, faction, value, notes))
        action = "add"

    log_event(
        guild_id,
        user_id,
        code=f"FAVOR_{action.upper()}_{faction.upper()}",
        title=f"{ICONS['favor']} Favor {faction} → {value}",
        details=notes,
        etype="favor_" + action,
        actors=[faction],
        tags=["favor", action]
    )
    return f"{ICONS['favor']} Favor {faction} untuk <@{user_id}> di{action} jadi `{value}`."

async def mod_favor(guild_id: int, user_id: int, faction: str, delta: int, notes: str = ""):
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT * FROM favors WHERE user_id=? AND faction=?", (user_id, faction))
    if not row:
        return f"❌ User ini belum punya favor {faction}."
    new_val = row["favor"] + delta
    execute(guild_id,
            "UPDATE favors SET favor=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND faction=?",
            (new_val, notes, user_id, faction))
    return f"{ICONS['favor']} Favor {faction} untuk <@{user_id}> berubah {delta:+d} → `{new_val}`."

async def list_favors(guild_id: int, user_id: int = None):
    ensure_table(guild_id)
    if user_id:
        rows = fetchall(guild_id, "SELECT * FROM favors WHERE user_id=?", (user_id,))
    else:
        rows = fetchall(guild_id, "SELECT * FROM favors", ())
    return rows or []

async def get_detail(guild_id: int, faction: str, user_id: int = None):
    ensure_table(guild_id)
    if user_id:
        return fetchone(guild_id, "SELECT * FROM favors WHERE user_id=? AND faction=?", (user_id, faction))
    return fetchone(guild_id, "SELECT * FROM favors WHERE faction=?", (faction,))

async def remove_favor(guild_id: int, user_id: int, faction: str):
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM favors WHERE user_id=? AND faction=?", (user_id, faction))
    return f"{ICONS['remove']} Favor {faction} untuk <@{user_id}> dihapus."

# ---------- GM & Utility ----------
async def list_all_favors(guild_id: int):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM favors", ())

async def list_factions_status(guild_id: int, user_id: int, factions: list):
    """Return daftar semua faksi dengan nilai Favor player."""
    ensure_table(guild_id)
    out = []
    for fac in factions:
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE user_id=? AND faction=?", (user_id, fac))
        val = row["favor"] if row else 0
        status = favor_status(val)
        out.append((fac, val, status))
    return out

async def add_favor(guild_id: int, targets: list, faction: str, value: int):
    """Dipanggil dari quest_service.complete_quest"""
    ensure_table(guild_id)
    result = []
    for ch in targets:
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE user_id=? AND faction=?", (ch, faction))
        if row:
            new_val = row["favor"] + value
            execute(guild_id,
                    "UPDATE favors SET favor=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND faction=?",
                    (new_val, ch, faction))
            result.append(f"{ch}: {row['favor']} → {new_val}")
        else:
            execute(guild_id,
                    "INSERT INTO favors (user_id, faction, favor, notes, updated_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                    (ch, faction, value, "Quest reward"))
            result.append(f"{ch}: {value} (baru)")
    return f"{ICONS['favor']} Favor {faction} ditambahkan → " + ", ".join(result)
