from utils.db import execute, fetchone, fetchall

# ===============================
#  Faction Service (per server)
# ===============================

def ensure_table(guild_id: int):
    """
    Pastikan tabel factions ada & memiliki kolom guild_id.
    Jika tabel lama tanpa guild_id terdeteksi, lakukan migrasi otomatis.
    """
    # cek struktur tabel lama
    info = fetchall(guild_id, "PRAGMA table_info(factions)")
    existing_cols = {c["name"] for c in info}

    if not info:
        # tabel belum ada → buat baru
        execute(
            guild_id,
            """
            CREATE TABLE IF NOT EXISTS factions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                desc TEXT,
                type TEXT DEFAULT 'general',
                hidden INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, name)
            )
            """
        )
    elif "guild_id" not in existing_cols:
        # tabel lama → MIGRASI
        execute(
            guild_id,
            """
            CREATE TABLE IF NOT EXISTS factions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                desc TEXT,
                type TEXT DEFAULT 'general',
                hidden INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, name)
            )
            """
        )
        # copy data lama → isi guild_id sesuai server sekarang
        execute(
            guild_id,
            """
            INSERT INTO factions_new (guild_id, name, desc, type, hidden, created_at)
            SELECT ?, name, desc, type, hidden, created_at FROM factions
            """,
            (guild_id,)
        )
        execute(guild_id, "DROP TABLE factions")
        execute(guild_id, "ALTER TABLE factions_new RENAME TO factions")

    # index tetap
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_faction_guild_name ON factions(guild_id, name)")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_faction_type ON factions(type)")


# ---------- Exists ----------
def exists_faction(guild_id: int, name: str) -> bool:
    ensure_table(guild_id)
    row = fetchone(
        guild_id,
        "SELECT 1 FROM factions WHERE guild_id=? AND name=?",
        (guild_id, name)
    )
    return row is not None


# ---------- CRUD ----------
def add_faction(guild_id: int, name: str, desc: str = "", ftype: str = "general", hidden: int = 0):
    ensure_table(guild_id)
    execute(
        guild_id,
        """
        INSERT OR IGNORE INTO factions (guild_id, name, desc, type, hidden, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (guild_id, name, desc, ftype, hidden)
    )
    return f"🏷️ Faction **{name}** ditambahkan (type: {ftype})."


def list_factions(guild_id: int, include_hidden=False):
    ensure_table(guild_id)
    if include_hidden:
        return fetchall(guild_id, "SELECT * FROM factions WHERE guild_id=?", (guild_id,))
    return fetchall(guild_id, "SELECT * FROM factions WHERE guild_id=? AND hidden=0", (guild_id,))


def get_faction(guild_id: int, name: str):
    ensure_table(guild_id)
    return fetchone(
        guild_id,
        "SELECT * FROM factions WHERE guild_id=? AND name=?",
        (guild_id, name)
    )


def remove_faction(guild_id: int, name: str):
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM factions WHERE guild_id=? AND name=?", (guild_id, name))
    return f"🗑️ Faction **{name}** dihapus."


def hide_faction(guild_id: int, name: str, hidden: int = 1):
    ensure_table(guild_id)
    execute(guild_id, "UPDATE factions SET hidden=? WHERE guild_id=? AND name=?", (hidden, guild_id, name))
    return f"{'🙈' if hidden else '👁️'} Faction **{name}** {'disembunyikan' if hidden else 'ditampilkan'}."


def set_faction_type(guild_id: int, name: str, ftype: str):
    ensure_table(guild_id)
    execute(guild_id, "UPDATE factions SET type=? WHERE guild_id=? AND name=?", (ftype, guild_id, name))
    return f"🏷️ Faction **{name}** type diubah ke `{ftype}`."
