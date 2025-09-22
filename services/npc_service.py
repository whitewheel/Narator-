import json
from utils.db import execute, fetchone, fetchall

# ===============================
# NPC SERVICE (Global)
# ===============================

ICONS = {
    "npc": "🧑‍🤝‍🧑",
    "favor_up": "💠",
    "favor_down": "❌",
    "hidden": "👁️",
    "lore": "📚",
}

async def add_npc(user_id, name, role="", favor=0, traits=None):
    """Tambah NPC baru ke world (global)."""
    execute(
        "INSERT INTO npc (name, role, favor, traits) VALUES (?,?,?,?)",
        (name, role, favor, json.dumps(traits or {}))
    )
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{ICONS['npc']} NPC baru: {name} ({role})",))
    return True


async def update_favor(name, amount):
    """Ubah favor NPC (positif / negatif)."""
    npc = fetchone("SELECT * FROM npc WHERE name=?", (name,))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    new_favor = npc["favor"] + amount
    execute("UPDATE npc SET favor=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_favor, npc["id"]))

    icon = ICONS["favor_up"] if amount > 0 else ICONS["favor_down"]
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{icon} Favor {name}: {npc['favor']} → {new_favor}",))
    return f"{icon} Favor {name} sekarang {new_favor}"


async def reveal_trait(name, trait_key):
    """Reveal trait tersembunyi NPC."""
    npc = fetchone("SELECT * FROM npc WHERE name=?", (name,))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    if trait_key not in traits:
        return f"{ICONS['hidden']} Trait tidak ada."

    trait = traits[trait_key]
    msg = f"{ICONS['hidden']} {name} ternyata: {trait}"
    execute("INSERT INTO timeline (event) VALUES (?)", (msg,))
    return msg


async def list_npc():
    """List semua NPC (global)."""
    rows = fetchall("SELECT * FROM npc")
    if not rows:
        return f"{ICONS['npc']} Tidak ada NPC."
    out = []
    for r in rows:
        out.append(f"{ICONS['npc']} **{r['name']}** ({r['role']}) Favor: {r['favor']}")
    return "\n".join(out)


async def sync_from_wiki():
    """Sinkronkan semua NPC dari wiki kategori 'npc'."""
    rows = fetchall("SELECT * FROM wiki WHERE category='npc'")
    added = []
    for r in rows:
        npc = fetchone("SELECT * FROM npc WHERE name=?", (r["name"],))
        if not npc:
            execute(
                "INSERT INTO npc (name, role, favor, traits) VALUES (?,?,?,?)",
                (r["name"], "Lore NPC", 0, "{}")
            )
            added.append(r["name"])
    if not added:
        return f"{ICONS['lore']} Tidak ada NPC baru dari lore."
    return f"{ICONS['lore']} NPC ditambahkan dari lore: {', '.join(added)}"
