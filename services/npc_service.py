import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event   # ✅ konsisten pakai timeline

# ===============================
# NPC SERVICE (per-server)
# ===============================

ICONS = {
    "npc": "🧑‍🤝‍🧑",
    "hidden": "👁️",
    "lore": "📚",
    "remove": "🗑️",
}

def get_npc(guild_id: int, name: str):
    """Ambil 1 NPC berdasarkan nama."""
    return fetchone(guild_id, "SELECT * FROM npc WHERE name=?", (name,))

async def add_npc(guild_id: int, user_id, name, role="", traits=None):
    """Tambah NPC baru ke world (per-server)."""
    exists = get_npc(guild_id, name)
    if exists:
        return f"⚠️ NPC **{name}** sudah ada."

    # default struktur JSON
    traits = traits or {}
    traits = {k: {"value": v, "visible": False} for k, v in traits.items()}

    execute(
        guild_id,
        "INSERT INTO npc (name, role, traits, info, status, affiliation) VALUES (?,?,?,?,?,?)",
        (name, role, json.dumps(traits), json.dumps({"value": "", "visible": True}), "Alive", None)
    )
    log_event(
        guild_id,
        user_id,
        code=f"NPC_ADD_{name.upper()}",
        title=f"{ICONS['npc']} NPC baru: {name}",
        details=f"Role: {role}",
        etype="npc_add",
        actors=[name],
        tags=["npc","add"]
    )
    return f"{ICONS['npc']} NPC **{name}** berhasil ditambahkan."

# ===== TRAITS =====

async def add_trait(guild_id: int, name: str, key: str, value: str, visible=False, user_id=None):
    npc = get_npc(guild_id, name)
    if not npc:
        return "❌ NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    traits[key] = {"value": value, "visible": visible}
    execute(guild_id, "UPDATE npc SET traits=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(traits), npc["id"]))

    log_event(
        guild_id,
        user_id or 0,
        code=f"NPC_TRAIT_ADD_{name.upper()}",
        title=f"➕ Trait {key} ditambahkan ke {name}",
        details=f"Value: {value}, Visible: {visible}",
        etype="npc_trait_add",
        actors=[name],
        tags=["npc","trait","add"]
    )
    return f"✅ Trait **{key}={value}** ditambahkan ke **{name}** (visible={visible})."

async def remove_trait(guild_id: int, name: str, key: str, user_id=None):
    npc = get_npc(guild_id, name)
    if not npc:
        return "❌ NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    if key not in traits:
        return "❌ Trait tidak ditemukan."

    traits.pop(key)
    execute(guild_id, "UPDATE npc SET traits=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(traits), npc["id"]))

    log_event(
        guild_id,
        user_id or 0,
        code=f"NPC_TRAIT_REMOVE_{name.upper()}",
        title=f"➖ Trait {key} dihapus dari {name}",
        details=f"Removed: {key}",
        etype="npc_trait_remove",
        actors=[name],
        tags=["npc","trait","remove"]
    )
    return f"🗑️ Trait **{key}** dihapus dari **{name}**."

async def reveal_trait(guild_id: int, name: str, key: str, user_id=None):
    npc = get_npc(guild_id, name)
    if not npc:
        return "❌ NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    if key not in traits:
        return "❌ Trait tidak ada."

    traits[key]["visible"] = True
    execute(guild_id, "UPDATE npc SET traits=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(traits), npc["id"]))

    val = traits[key]["value"]
    msg = f"{ICONS['hidden']} {name} ternyata: {val}"

    log_event(
        guild_id,
        user_id or 0,
        code=f"NPC_TRAIT_REVEAL_{name.upper()}",
        title=msg,
        details=f"Trait: {key} → {val}",
        etype="npc_trait_reveal",
        actors=[name],
        tags=["npc","trait","reveal"]
    )
    return msg

async def all_reveal(guild_id: int, name: str, user_id=None):
    npc = get_npc(guild_id, name)
    if not npc:
        return "❌ NPC tidak ditemukan."

    traits = json.loads(npc.get("traits") or "{}")
    for k in traits:
        traits[k]["visible"] = True
    info = npc.get("info")
    if info:
        try:
            info_data = json.loads(info)
            if isinstance(info_data, dict):
                info_data["visible"] = True
                info = json.dumps(info_data)
        except:
            pass

    execute(guild_id,
            "UPDATE npc SET traits=?, info=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(traits), info, npc["id"]))

    log_event(
        guild_id,
        user_id or 0,
        code=f"NPC_ALLREVEAL_{name.upper()}",
        title=f"{ICONS['hidden']} Semua trait & info {name} dibuka",
        details="All traits and info set visible=True",
        etype="npc_allreveal",
        actors=[name],
        tags=["npc","trait","info","reveal"]
    )
    return f"👁️ Semua trait & info **{name}** sudah terbuka."

# ===== INFO =====

async def set_info(guild_id: int, name: str, text: str, hidden=False, user_id=None):
    npc = get_npc(guild_id, name)
    if not npc:
        return "❌ NPC tidak ditemukan."

    info = {"value": text, "visible": not hidden}
    execute(guild_id, "UPDATE npc SET info=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(info), npc["id"]))

    log_event(
        guild_id,
        user_id or 0,
        code=f"NPC_INFO_SET_{name.upper()}",
        title=f"📖 Info NPC {name} diupdate",
        details=f"Hidden={hidden}",
        etype="npc_info",
        actors=[name],
        tags=["npc","info"]
    )
    return f"📖 Info untuk **{name}** diupdate. (hidden={hidden})"

# ===== LIST & SYNC =====

async def list_npc(guild_id: int):
    rows = fetchall(guild_id, "SELECT * FROM npc ORDER BY name COLLATE NOCASE ASC")
    if not rows:
        return f"{ICONS['npc']} Tidak ada NPC."
    out = []
    for r in rows:
        out.append(f"{ICONS['npc']} **{r['name']}** ({r['role']})")
    return "\n".join(out)

async def sync_from_wiki(guild_id: int, user_id=None):
    rows = fetchall(guild_id, "SELECT * FROM wiki WHERE category='npc'")
    added = []
    for r in rows:
        npc = get_npc(guild_id, r["name"])
        if not npc:
            execute(
                guild_id,
                "INSERT INTO npc (name, role, traits, info, status, affiliation) VALUES (?,?,?,?,?,?)",
                (r["name"], "Lore NPC", "{}", json.dumps({"value":"", "visible":True}), "Alive", None)
            )
            added.append(r["name"])

    if not added:
        log_event(
            guild_id,
            user_id or 0,
            code="NPC_SYNC_EMPTY",
            title=f"{ICONS['lore']} Sinkronisasi NPC (kosong)",
            details="Tidak ada NPC baru dari wiki.",
            etype="npc_sync",
            actors=[],
            tags=["npc","lore","sync"]
        )
        return f"{ICONS['lore']} Tidak ada NPC baru dari lore."

    log_event(
        guild_id,
        user_id or 0,
        code="NPC_SYNC",
        title=f"{ICONS['lore']} NPC ditambahkan dari lore",
        details=f"Added: {', '.join(added)}",
        etype="npc_sync",
        actors=added,
        tags=["npc","lore","sync"]
    )
    return f"{ICONS['lore']} NPC ditambahkan dari lore: {', '.join(added)}"

# ===== REMOVE =====

async def remove_npc(guild_id: int, user_id: int, name: str):
    npc = get_npc(guild_id, name)
    if not npc:
        return f"❌ NPC **{name}** tidak ditemukan."
    
    execute(guild_id, "DELETE FROM npc WHERE name=?", (name,))
    log_event(
        guild_id,
        user_id,
        code=f"NPC_REMOVE_{name.upper()}",
        title=f"{ICONS['remove']} NPC {name} dihapus.",
        details=f"Role: {npc.get('role','-')}",
        etype="npc_remove",
        actors=[name],
        tags=["npc","remove"]
    )
    return f"{ICONS['remove']} NPC **{name}** dihapus."
