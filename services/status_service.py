import json
from utils.db import execute, fetchone, fetchall

# ===============================
# STATUS SERVICE (Global)
# ===============================
# Bisa dipakai untuk character & enemy
# target_type: "char" atau "enemy"

def _table(target_type: str) -> str:
    return "enemies" if target_type == "enemy" else "characters"

ICONS = {
    "buff": "✨",
    "debuff": "☠️",
    "expired": "⌛"
}

# ===============================
# HP / VITALS
# ===============================
async def damage(target_type, name, amount: int):
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None

    new_hp = max(0, row["hp"] - amount)
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    # Log
    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("dmg", json.dumps({"target": name, "type": target_type,
                                "old": row["hp"], "new": new_hp, "amount": amount})))
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{name} menerima {amount} damage → {new_hp}/{row['hp_max']} HP",))
    return new_hp

async def heal(target_type, name, amount: int):
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None

    new_hp = min(row["hp_max"], row["hp"] + amount)
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("heal", json.dumps({"target": name, "type": target_type,
                                 "old": row["hp"], "new": new_hp, "amount": amount})))
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{name} disembuhkan {amount} HP → {new_hp}/{row['hp_max']} HP",))
    return new_hp

async def use_resource(target_type, name, field: str, amount: int, regen=False):
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None

    cur = row[field]
    mx = row[f"{field}_max"]
    new_val = min(mx, cur + amount) if regen else max(0, cur - amount)

    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))

    action = "regen" if regen else "use"
    execute("INSERT INTO history (action, data) VALUES (?,?)",
            (f"{field}_{action}", json.dumps({"target": name, "type": target_type,
                                              "old": cur, "new": new_val, "amount": amount})))
    return new_val

# ===============================
# BUFF / DEBUFF
# ===============================
async def add_effect(target_type, name, effect: str, is_buff=True):
    table = _table(target_type)
    col = "buffs" if is_buff else "debuffs"

    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None

    effects = json.loads(row[col] or "[]")
    effects.append({"text": effect, "duration": -1})
    execute(f"UPDATE {table} SET {col}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(effects), row["id"]))
    return effects

async def clear_effects(target_type, name, is_buff=True):
    table = _table(target_type)
    col = "buffs" if is_buff else "debuffs"
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None
    execute(f"UPDATE {table} SET {col}='[]', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
    return []

async def tick_all_effects():
    """Kurangi durasi semua efek (char & enemy)."""
    results = {"char": {}, "enemy": {}}
    for ttype, table in [("char", "characters"), ("enemy", "enemies")]:
        rows = fetchall(f"SELECT * FROM {table}")
        for r in rows:
            effects = json.loads(r.get("effects") or "[]")
            new_effects = []
            expired = []
            for e in effects:
                dur = e.get("duration", -1)
                if dur == -1:
                    new_effects.append(e)
                elif dur > 1:
                    e["duration"] = dur - 1
                    new_effects.append(e)
                else:
                    expired.append(e)

            execute(f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps(new_effects), r["id"]))

            for e in expired:
                execute("INSERT INTO timeline (event) VALUES (?)",
                        (f"{ICONS['expired']} {r['name']} kehilangan efek: {e['text']}",))

            results[ttype][r["name"]] = {"remaining": new_effects, "expired": expired}
    return results

# ===============================
# EQUIPMENT
# ===============================
async def set_equipment(name, slot: str, item: str):
    row = fetchone("SELECT * FROM characters WHERE name=?", (name,))
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
async def add_companion(name, comp: dict):
    row = fetchone("SELECT * FROM characters WHERE name=?", (name,))
    if not row:
        return None

    comps = json.loads(row.get("companions") or "[]")
    comps.append(comp)
    execute("UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

async def remove_companion(name, comp_name: str):
    row = fetchone("SELECT * FROM characters WHERE name=?", (name,))
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
async def set_status(target_type, name, field: str, value):
    table = _table(target_type)
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if not row:
        return None

    old_value = row.get(field)
    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (value, row["id"]))

    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("set_status", json.dumps({"target": name, "type": target_type,
                                       "field": field, "old": old_value, "new": value})))
    return value
