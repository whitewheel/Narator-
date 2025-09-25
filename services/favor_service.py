# services/favor_service.py
import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event

ICONS = {
    "favor": "🪙",
    "add": "➕",
    "set": "⚖️",
    "remove": "🗑️",
}

def ensure_table(guild_id: int):
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS favor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction TEXT UNIQUE,
            value INTEGER DEFAULT 0,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_favor_faction ON favor(faction);")

# ------------------------------
# CRUD
# ------------------------------

def add_or_set_favor(guild_id: int, faction: str, value: int, notes: str = "", user_id: str = "0"):
    ensure_table(guild_id)
    exists = fetchone(guild_id, "SELECT * FROM favor WHERE faction=?", (faction,))
    if exists:
        execute(
            guild_id,
            "UPDATE favor SET value=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE faction=?",
            (value, notes, faction)
        )
        action = "set"
    else:
        execute(
            guild_id,
            "INSERT INTO favor (faction, value, notes) VALUES (?,?,?)",
            (faction, value, notes)
        )
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
    return True


def get_favor(guild_id: int, faction: str):
    ensure_table(guild_id)
    return fetchone(guild_id, "SELECT * FROM favor WHERE faction=?", (faction,))


def list_favor(guild_id: int):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM favor ORDER BY faction ASC")


def remove_favor(guild_id: int, faction: str, user_id: str = "0"):
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT * FROM favor WHERE faction=?", (faction,))
    if not row:
        return False
    execute(guild_id, "DELETE FROM favor WHERE faction=?", (faction,))
    log_event(
        guild_id,
        user_id,
        code=f"FAVOR_REMOVE_{faction.upper()}",
        title=f"{ICONS['remove']} Favor {faction} dihapus",
        details="Favor entry dihapus",
        etype="favor_remove",
        actors=[faction],
        tags=["favor", "remove"]
    )
    return True
