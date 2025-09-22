import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event   # ✅ konsisten pakai timeline

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
    exists = fetchone("SELECT id FROM npc WHERE name=?", (name,))
    if exists:
        return f"⚠️ NPC **{name}** sudah ada."

    execute(
        "INSERT INTO npc (name, role, favor, traits) VALUES (?,?,?,?)",
        (name, role, favor, json.dumps(traits or {}))
    )
    log_event("0", "0", user_id,
              code=f"NPC_ADD_{name.upper()}",
              title=f"{ICONS['npc']} NPC baru: {name}",
              details=f"Role: {role}, Favor: {favor}",
              etype="npc_add",
              actors=[name],
              tags=["npc","add"])
    return f"{ICONS['npc']} NPC **{name}** berhasil ditambahkan."


async def update_favor(name, amount, user_id=None):
    """Ubah favor NPC (positif / negatif)."""
    npc = fetchone("SELECT * FROM npc WHERE name=?", (name,))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    new_favor = npc["favor"] + amount
    execute("UPDATE npc SET favor=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_favor, npc["id"]))

    icon = ICONS["favor_up"] if amount > 0 else ICONS["favor_down"]
    log_event("0", "0", user_id or 0,
              code=f"NPC_FAVOR_{name.upper()}",
              title=f"{icon} Favor {name}: {npc['favor']} → {new_favor}",
              details=f"Change: {amount:+d}",
              etype="npc_favor",
              actors=[name],
              tags=["npc","favor"])
    return f"{icon} Favor {name} sekarang {new_favor}"


async def reveal_trait(name, trait_key, user_id=None):
    """Reveal trait tersembunyi NPC."""
    npc = fetchone("SELECT * FROM npc WHERE name=?", (name,))
    if not npc:
        return f"{ICONS['favor_down']} NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    if trait_key not in traits:
        return f"{ICONS['hidden']} Trait tidak ada."

    trait = traits[trait_key]
    msg = f"{ICONS['hidden']} {name} ternyata: {trait}"

    # update log
    log_event("0", "0", user_id or 0,
              code=f"NPC_TRAIT_{name.upper()}",
              title=msg,
              details=f"Trait: {trait_key}",
              etype="npc_trait",
              actors=[name],
              tags=["npc","trait"])
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


async def sync_from_wiki(user_id=None):
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
        log_event("0", "0", user_id or 0,
                  code="NPC_SYNC_EMPTY",
                  title=f"{ICONS['lore']} Sinkronisasi NPC (kosong)",
                  details="Tidak ada NPC baru dari wiki.",
                  etype="npc_sync",
                  actors=[],
                  tags=["npc","lore","sync"])
        return f"{ICONS['lore']} Tidak ada NPC baru dari lore."

    log_event("0", "0", user_id or 0,
              code="NPC_SYNC",
              title=f"{ICONS['lore']} NPC ditambahkan dari lore",
              details=f"Added: {', '.join(added)}",
              etype="npc_sync",
              actors=added,
              tags=["npc","lore","sync"])
    return f"{ICONS['lore']} NPC ditambahkan dari lore: {', '.join(added)}"
