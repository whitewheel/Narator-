import json
from utils.db import execute, fetchone, fetchall

# ===============================
# NPC SERVICE
# ===============================

ICONS = {
    "npc": "🧑‍🤝‍🧑",
    "favor_up": "💠",
    "favor_down": "❌",
    "hidden": "👁️",
    "lore": "📚",
}

async def add_npc(guild_id, channel_id, name, role="", favor=0, traits=None):
    """Tambah NPC baru ke world."""
    execute(
        "INSERT INTO npc (guild_id, channel_id, name, role, favor, traits) VALUES (?,?,?,?,?,?)",
        (guild_id, channel_id, name, role, favor, json.dumps(traits or {}))
    )
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['npc']} NPC baru: {name} ({role})"))
    return True


async def update_favor(guild_id, channel_id, name, amount):
    """Ubah favor NPC (positif / negatif)."""
    npc = fetchone("SELECT * FROM npc WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    new_favor = npc["favor"] + amount
    execute("UPDATE npc SET favor=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_favor, npc["id"]))

    icon = ICONS["favor_up"] if amount > 0 else ICONS["favor_down"]
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{icon} Favor {name}: {npc['favor']} → {new_favor}"))
    return f"{icon} Favor {name} sekarang {new_favor}"


async def reveal_trait(guild_id, channel_id, name, trait_key):
    """Reveal trait tersembunyi NPC."""
    npc = fetchone("SELECT * FROM npc WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    traits = json.loads(npc["traits"] or "{}")
    if trait_key not in traits:
        return f"{ICONS['hidden']} Trait tidak ada."

    trait = traits[trait_key]
    msg = f"{ICONS['hidden']} {name} ternyata: {trait}"
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, msg))
    return msg


async def list_npc(guild_id, channel_id):
    """List semua NPC di channel."""
    rows = fetchall("SELECT * FROM npc WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
    if not rows:
        return f"{ICONS['npc']} Tidak ada NPC."
    out = []
    for r in rows:
        out.append(f"{ICONS['npc']} **{r['name']}** ({r['role']}) Favor: {r['favor']}")
    return "\n".join(out)


async def sync_from_wiki(guild_id, channel_id):
    """Sinkronkan semua NPC dari wiki kategori 'npc'."""
    rows = fetchall("SELECT * FROM wiki WHERE guild_id=? AND channel_id=? AND category='npc'",
                    (guild_id, channel_id))
    added = []
    for r in rows:
        npc = fetchone("SELECT * FROM npc WHERE guild_id=? AND channel_id=? AND name=?",
                       (guild_id, channel_id, r["name"]))
        if not npc:
            execute(
                "INSERT INTO npc (guild_id, channel_id, name, role, favor, traits) VALUES (?,?,?,?,?,?)",
                (guild_id, channel_id, r["name"], "Lore NPC", 0, "{}")
            )
            added.append(r["name"])
    if not added:
        return f"{ICONS['lore']} Tidak ada NPC baru dari lore."
    return f"{ICONS['lore']} NPC ditambahkan dari lore: {', '.join(added)}"
