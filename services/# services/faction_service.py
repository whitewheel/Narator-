# services/faction_service.py
from utils.db import execute, fetchone, fetchall

ICONS = {
    "faction": "🏷️",
    "remove": "🗑️",
    "hide": "🙈",
    "show": "👁️",
}

# ------------------------------
# CRUD Faction Registry
# ------------------------------

def add_faction(guild_id: int, name: str, desc: str = "", hidden: int = 0):
    """Tambah faction baru ke registry (GM only)."""
    execute(
        guild_id,
        "INSERT OR IGNORE INTO factions (name, desc, hidden) VALUES (?, ?, ?)",
        (name, desc, hidden)
    )
    return f"{ICONS['faction']} Faction **{name}** ditambahkan."

def list_factions(guild_id: int, include_hidden: bool = False):
    """Ambil semua faction (bisa pilih include hidden)."""
    if include_hidden:
        rows = fetchall(guild_id, "SELECT * FROM factions ORDER BY name ASC")
    else:
        rows = fetchall(guild_id, "SELECT * FROM factions WHERE hidden=0 ORDER BY name ASC")
    return rows or []

def get_faction(guild_id: int, name: str):
    """Detail 1 faction."""
    return fetchone(guild_id, "SELECT * FROM factions WHERE name=?", (name,))

def remove_faction(guild_id: int, name: str):
    """Hapus faction dari registry."""
    execute(guild_id, "DELETE FROM factions WHERE name=?", (name,))
    return f"{ICONS['remove']} Faction **{name}** dihapus."

def hide_faction(guild_id: int, name: str, hidden: int = 1):
    """Sembunyikan / tampilkan faction di list publik."""
    execute(
        guild_id,
        "UPDATE factions SET hidden=?, created_at=CURRENT_TIMESTAMP WHERE name=?",
        (hidden, name)
    )
    if hidden:
        return f"{ICONS['hide']} Faction **{name}** disembunyikan."
    else:
        return f"{ICONS['show']} Faction **{name}** ditampilkan."
