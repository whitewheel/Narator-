from utils.db import execute, fetchone, fetchall

# ==========================
# Faction Service
# ==========================

def ensure_table(guild_id: int):
    """Pastikan tabel factions ada"""
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS factions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            desc TEXT,
            type TEXT DEFAULT 'general',
            hidden INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_faction_name ON factions(name);")

# ---------- CRUD ----------
def add_faction(guild_id: int, name: str, desc: str = "", ftype: str = "general", hidden: int = 0):
    """Tambah faction baru"""
    ensure_table(guild_id)
    execute(
        guild_id,
        "INSERT OR IGNORE INTO factions (name, desc, type, hidden) VALUES (?,?,?,?)",
        (name.strip(), desc.strip(), ftype.lower(), hidden)
    )
    return f"🏷️ Faction **{name}** ditambahkan (type: {ftype})."

def list_factions(guild_id: int, include_hidden: bool = False):
    """List semua faction (opsi tampilkan hidden)"""
    ensure_table(guild_id)
    if include_hidden:
        return fetchall(guild_id, "SELECT * FROM factions ORDER BY name ASC")
    return fetchall(guild_id, "SELECT * FROM factions WHERE hidden=0 ORDER BY name ASC")

def get_faction(guild_id: int, name: str):
    """Ambil 1 faction berdasarkan nama"""
    ensure_table(guild_id)
    return fetchone(guild_id, "SELECT * FROM factions WHERE name=?", (name,))

def exists_faction(guild_id: int, name: str) -> bool:
    """Cek apakah faction dengan nama tertentu ada"""
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT 1 FROM factions WHERE name=?", (name,))
    return row is not None

def remove_faction(guild_id: int, name: str):
    """Hapus faction"""
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM factions WHERE name=?", (name,))
    return f"🗑️ Faction **{name}** dihapus."

def hide_faction(guild_id: int, name: str, hidden: int = 1):
    """Sembunyikan / tampilkan faction"""
    ensure_table(guild_id)
    execute(guild_id, "UPDATE factions SET hidden=? WHERE name=?", (hidden, name))
    if hidden:
        return f"🙈 Faction **{name}** disembunyikan."
    else:
        return f"👁️ Faction **{name}** ditampilkan."

def set_faction_type(guild_id: int, name: str, ftype: str):
    """Update type faction (city/region/corp/gang/etc)"""
    ensure_table(guild_id)
    execute(guild_id, "UPDATE factions SET type=? WHERE name=?", (ftype.lower(), name))
    return f"🏷️ Faction **{name}** diubah jadi type `{ftype}`."
