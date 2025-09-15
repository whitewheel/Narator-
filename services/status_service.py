import json
from utils.db import execute, fetchone

# ===============================
# STATUS SERVICE
# ===============================
# Bisa dipakai untuk character & enemy
# target_type: "char" atau "enemy"

def _table(target_type: str) -> str:
    if target_type == "enemy":
        return "enemies"
    return "characters"

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

    # Log ke history
    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "dmg",
             json.dumps({"target": name, "type": target_type, "old": row["hp"], "new": new_hp, "amount": amount})))

    # Log ke timeline
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

    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{name} {field} berubah dari {old_value} → {value}"))
    return value
