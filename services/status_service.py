import json
from utils.db import execute, fetchone

# ===============================
# STATUS SERVICE
# ===============================
# Bisa dipakai untuk character & enemy
# target_type: "char" atau "enemy"

def _table(target_type: str) -> str:
    return "enemies" if target_type == "enemy" else "characters"

# ===============================
# HP / VITALS
# ===============================
async def damage(guild_id, channel_id, target_type, name, amount: int):
    """Kurangi HP (damage)."""
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    new_hp = max(0, row["hp"] - amount)
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    # Log
    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "dmg",
             json.dumps({"target": name, "type": target_type, "old": row["hp"], "new": new_hp, "amount": amount})))
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{name} menerima {amount} damage → {new_hp}/{row['hp_max']} HP"))
    return new_hp


async def heal(guild_id, channel_id, target_type, name, amount: int):
    """Tambah HP (heal)."""
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    new_hp = min(row["hp_max"], row["hp"] + amount)
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "heal",
             json.dumps({"target": name, "type": target_type, "old": row["hp"], "new": new_hp, "amount": amount})))
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{name} disembuhkan {amount} HP → {new_hp}/{row['hp_max']} HP"))
    return new_hp


async def use_resource(guild_id, channel_id, target_type, name, field: str, amount: int, regen=False):
    """
    Gunakan / pulihkan energy atau stamina.
    field: "energy" atau "stamina"
    """
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    cur = row[field]
    mx = row[f"{field}_max"]
    new_val = min(mx, cur + amount) if regen else max(0, cur - amount)

    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))

    action = "regen" if regen else "use"
    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, f"{field}_{action}",
             json.dumps({"target": name, "type": target_type, "old": cur, "new": new_val, "amount": amount})))
    return new_val

# ===============================
# BUFF / DEBUFF
# ===============================
async def add_effect(guild_id, channel_id, target_type, name, effect: str, is_buff=True):
    table = _table(target_type)
    col = "buffs" if is_buff else "debuffs"

    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?", 
                   (guild_id, channel_id, name))
    if not row:
        return None

    effects = json.loads(row[col] or "[]")
    effects.append({"text": effect, "duration": -1})
    execute(f"UPDATE {table} SET {col}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(effects), row["id"]))
    return effects

async def clear_effects(guild_id, channel_id, target_type, name, is_buff=True):
    table = _table(target_type)
    col = "buffs" if is_buff else "debuffs"
    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?", 
                   (guild_id, channel_id, name))
    if not row:
        return None
    execute(f"UPDATE {table} SET {col}='[]', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
    return []

# ===============================
# EQUIPMENT
# ===============================
async def set_equipment(guild_id, channel_id, name, slot: str, item: str):
    """slot: weapon/armor/accessory"""
    row = fetchone("SELECT * FROM characters WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    eq = json.loads(row.get("equipment") or "{}")
    eq[slot] = item
    execute("UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(eq), row["id"]))
    return eq

# ===============================
# COMPANIONS
# ===============================
async def add_companion(guild_id, channel_id, name, comp: dict):
    row = fetchone("SELECT * FROM characters WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    comps = json.loads(row.get("companions") or "[]")
    comps.append(comp)
    execute("UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

async def remove_companion(guild_id, channel_id, name, comp_name: str):
    row = fetchone("SELECT * FROM characters WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    comps = json.loads(row.get("companions") or "[]")
    comps = [c for c in comps if c["name"].lower() != comp_name.lower()]
    execute("UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

# ===============================
# GENERIC FIELD UPDATE
# ===============================
async def set_status(guild_id, channel_id, target_type, name, field: str, value):
    """Update field tertentu (misal AC, MP, dll)."""
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE guild_id=? AND channel_id=? AND name=?",
                   (guild_id, channel_id, name))
    if not row:
        return None

    old_value = row.get(field)
    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (value, row["id"]))

    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "set_status",
             json.dumps({"target": name, "type": target_type, "field": field, "old": old_value, "new": value})))
    return value
