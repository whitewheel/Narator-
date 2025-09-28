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
            char_name TEXT NOT NULL,
            faction TEXT NOT NULL,
            favor INTEGER DEFAULT 0,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(char_name, faction)
        )
    """)
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_favor_char ON favors(char_name);")
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
async def add_or_set_favor(guild_id: int, char_name: str, faction: str, value: int, notes: str = ""):
    ensure_table(guild_id)

    # auto-create faction kalau belum ada
    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    row = fetchone(guild_id, "SELECT * FROM favors WHERE char_name=? AND faction=?", (char_name, faction))
    if row:
        execute(
            guild_id,
            "UPDATE favors SET favor=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE char_name=? AND faction=?",
            (value, notes or row.get("notes",""), char_name, faction)
        )
        action = "set"
    else:
        execute(
            guild_id,
            "INSERT INTO favors (char_name, faction, favor, notes) VALUES (?,?,?,?)",
            (char_name, faction, value, notes)
        )
        action = "add"

    log_event(
        guild_id,
        char_name,
        code=f"FAVOR_{action.upper()}_{faction.upper()}",
        title=f"{ICONS['favor']} Favor {char_name}:{faction} → {value}",
        details=notes,
        etype="favor_" + action,
        actors=[char_name, faction],
        tags=["favor", action]
    )
    return f"{ICONS['favor']} Favor {faction} untuk **{char_name}** di{action} jadi `{value}`."

async def mod_favor(guild_id: int, char_name: str, faction: str, delta: int, notes: str = ""):
    ensure_table(guild_id)

    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    row = fetchone(guild_id, "SELECT * FROM favors WHERE char_name=? AND faction=?", (char_name, faction))
    if not row:
        return f"❌ {char_name} belum punya favor {faction}."
    new_val = row["favor"] + delta
    execute(
        guild_id,
        "UPDATE favors SET favor=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE char_name=? AND faction=?",
        (new_val, notes or row.get("notes",""), char_name, faction)
    )
    return f"{ICONS['favor']} Favor {faction} untuk **{char_name}** berubah {delta:+d} → `{new_val}`."

async def list_favors(guild_id: int, char_name: str = None):
    ensure_table(guild_id)
    if char_name:
        return fetchall(guild_id, "SELECT * FROM favors WHERE char_name=?", (char_name,))
    return fetchall(guild_id, "SELECT * FROM favors")

async def get_detail(guild_id: int, faction: str, char_name: str = None):
    ensure_table(guild_id)
    if char_name:
        return fetchone(guild_id, "SELECT * FROM favors WHERE char_name=? AND faction=?", (char_name, faction))
    return fetchall(guild_id, "SELECT * FROM favors WHERE faction=?", (faction,))

async def remove_favor(guild_id: int, char_name: str, faction: str):
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM favors WHERE char_name=? AND faction=?", (char_name, faction))
    return f"{ICONS['remove']} Favor {faction} untuk **{char_name}** dihapus."

# ---------- GM & Utility ----------
async def list_all_favors(guild_id: int):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM favors")

async def list_factions_status(guild_id: int, char_name: str, factions: list):
    """Return daftar semua faksi dengan nilai Favor karakter."""
    ensure_table(guild_id)
    out = []
    for fac in factions:
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE char_name=? AND faction=?", (char_name, fac))
        val = row["favor"] if row else 0
        status = favor_status(val)
        out.append((fac, val, status))
    return out

async def add_favor(guild_id: int, targets: list, faction: str, value: int):
    """Dipanggil dari quest_service.complete_quest"""
    ensure_table(guild_id)

    if not faction_service.exists_faction(guild_id, faction):
        faction_service.add_faction(guild_id, faction, desc="(auto-generated)", ftype="general")

    result = []
    for ch in targets:
        row = fetchone(guild_id, "SELECT favor FROM favors WHERE char_name=? AND faction=?", (ch, faction))
        if row:
            new_val = row["favor"] + value
            execute(
                guild_id,
                "UPDATE favors SET favor=?, updated_at=CURRENT_TIMESTAMP WHERE char_name=? AND faction=?",
                (new_val, ch, faction)
            )
            result.append(f"{ch}: {row['favor']} → {new_val}")
        else:
            execute(
                guild_id,
                "INSERT INTO favors (char_name, faction, favor, notes, updated_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                (ch, faction, value, "Quest reward")
            )
            result.append(f"{ch}: {value} (baru)")
    return f"{ICONS['favor']} Favor {faction} ditambahkan → " + ", ".join(result)
