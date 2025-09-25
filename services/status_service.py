# services/status_service.py
import json
from utils.db import execute, fetchone, fetchall

# ===============================
# STATUS SERVICE (per-server)
# ===============================
# target_type: "char" atau "enemy"

def _table(target_type: str) -> str:
    return "enemies" if target_type == "enemy" else "characters"

ICONS = {
    "buff": "✨",
    "debuff": "☠️",
    "expired": "⌛"
}

# -------------------------------
# Helpers
# -------------------------------
def _baseline_row(table: str, name: str) -> dict:
    """Nilai baseline aman untuk INSERT awal."""
    base = {
        "name": name,
        "hp": 0, "hp_max": 0,
        "energy": 0, "energy_max": 0,
        "stamina": 0, "stamina_max": 0,
        "ac": 10, "init_mod": 0,
        "str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0,
        "level": 1, "xp": 0, "gold": 0, "speed": 30,
        "equipment": "{}", "companions": "[]", "inventory": "[]",
        "effects": "[]"
    }
    if table == "enemies":
        base.update({
            "xp_reward": 0, "gold_reward": 0, "loot": "[]"
        })
    return base

def _ensure_exists(guild_id: int, table: str, name: str) -> dict:
    """Pastikan row ada. Kalau belum, INSERT baseline."""
    row = fetchone(guild_id, f"SELECT * FROM {table} WHERE name=?", (name,))
    if row:
        return row

    base = _baseline_row(table, name)
    cols = ", ".join(base.keys())
    placeholders = ", ".join(["?"] * len(base))
    execute(guild_id, f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", tuple(base.values()))

    return fetchone(guild_id, f"SELECT * FROM {table} WHERE name=?", (name,))

# ===============================
# HP / VITALS
# ===============================
async def damage(guild_id: int, target_type, name, amount: int):
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)

    hp_max = int(row.get("hp_max") or 0)
    cur_hp = int(row.get("hp") or 0)
    new_hp = max(0, cur_hp - int(amount))

    execute(guild_id, f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            ("dmg", json.dumps({"target": name, "type": target_type,
                                "old": cur_hp, "new": new_hp, "amount": int(amount)})))
    execute(guild_id, "INSERT INTO timeline (event) VALUES (?)",
            (f"{name} menerima {int(amount)} damage → {new_hp}/{hp_max} HP",))
    return new_hp

async def heal(guild_id: int, target_type, name, amount: int):
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)

    hp_max = int(row.get("hp_max") or 0)
    cur_hp = int(row.get("hp") or 0)
    if hp_max <= 0:
        hp_max = cur_hp + int(amount)
        execute(guild_id, f"UPDATE {table} SET hp_max=? WHERE id=?", (hp_max, row["id"]))

    new_hp = min(hp_max, cur_hp + int(amount))
    execute(guild_id, f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            ("heal", json.dumps({"target": name, "type": target_type,
                                 "old": cur_hp, "new": new_hp, "amount": int(amount)})))
    execute(guild_id, "INSERT INTO timeline (event) VALUES (?)",
            (f"{name} disembuhkan {int(amount)} HP → {new_hp}/{hp_max} HP",))
    return new_hp

async def use_resource(guild_id: int, target_type, name, field: str, amount: int, regen=False):
    """Kurangi / regen resource (energy/stamina)."""
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)

    cur = int(row.get(field) or 0)
    mx = int(row.get(f"{field}_max") or 0)

    if regen and mx <= 0:
        mx = cur + int(amount)
        execute(guild_id, f"UPDATE {table} SET {field}_max=? WHERE id=?", (mx, row["id"]))

    new_val = min(mx, cur + int(amount)) if regen else max(0, cur - int(amount))
    execute(guild_id, f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))

    action = "regen" if regen else "use"
    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            (f"{field}_{action}", json.dumps({"target": name, "type": target_type,
                                              "old": cur, "new": new_val, "amount": int(amount)})))
    return new_val

# ===============================
# EFFECTS
# ===============================
async def add_effect(guild_id: int, target_type, name, effect: str, is_buff=True):
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)
    effects = json.loads(row.get("effects") or "[]")
    effects.append({"text": effect, "type": "buff" if is_buff else "debuff", "duration": -1})
    execute(guild_id, f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(effects), row["id"]))
    return effects

async def clear_effects(guild_id: int, target_type, name, is_buff=True):
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)
    effects = json.loads(row.get("effects") or "[]")
    keep = [e for e in effects if (e.get("type") or "").lower() != ("buff" if is_buff else "debuff")]
    execute(guild_id, f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(keep), row["id"]))
    return keep

async def tick_all_effects(guild_id: int):
    results = {"char": {}, "enemy": {}}
    for ttype, table in [("char", "characters"), ("enemy", "enemies")]:
        rows = fetchall(guild_id, f"SELECT * FROM {table}")
        for r in rows:
            effects = json.loads(r.get("effects") or "[]")
            new_effects, expired = [], []
            for e in effects:
                dur = int(e.get("duration", -1))
                if dur == -1:
                    new_effects.append(e)
                elif dur > 1:
                    e["duration"] = dur - 1
                    new_effects.append(e)
                else:
                    expired.append(e)

            execute(guild_id, f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps(new_effects), r["id"]))

            for e in expired:
                execute(guild_id, "INSERT INTO timeline (event) VALUES (?)",
                        (f"{ICONS['expired']} {r['name']} kehilangan efek: {e.get('text','')}",))

            results[ttype][r["name"]] = {"remaining": new_effects, "expired": expired}
    return results

# ===============================
# EQUIPMENT
# ===============================
async def set_equipment(guild_id: int, name, slot: str, item: str):
    row = _ensure_exists(guild_id, "characters", name)
    eq = json.loads(row.get("equipment") or "{}")
    eq[slot] = item
    execute(guild_id, "UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(eq), row["id"]))
    return eq

# ===============================
# COMPANIONS
# ===============================
async def add_companion(guild_id: int, name, comp: dict):
    row = _ensure_exists(guild_id, "characters", name)
    comps = json.loads(row.get("companions") or "[]")
    comps.append(comp)
    execute(guild_id, "UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

async def remove_companion(guild_id: int, name, comp_name: str):
    row = _ensure_exists(guild_id, "characters", name)
    comps = json.loads(row.get("companions") or "[]")
    comps = [c for c in comps if c.get("name","").lower() != comp_name.lower()]
    execute(guild_id, "UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

# ===============================
# GENERIC FIELD UPDATE
# ===============================
async def set_status(guild_id: int, target_type, name, field: str, value):
    table = _table(target_type)
    row = _ensure_exists(guild_id, table, name)
    old_value = row.get(field)
    execute(guild_id, f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (value, row["id"]))
    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            ("set_status", json.dumps({"target": name, "type": target_type,
                                       "field": field, "old": old_value, "new": value})))
    return value

# ===============================
# GOLD & XP HELPERS
# ===============================
async def add_gold(guild_id: int, name, amount: int):
    row = _ensure_exists(guild_id, "characters", name)
    cur = int(row.get("gold") or 0)
    new_val = max(0, cur + int(amount))
    execute(guild_id, "UPDATE characters SET gold=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))
    return new_val

async def add_xp(guild_id: int, name, amount: int):
    row = _ensure_exists(guild_id, "characters", name)
    cur = int(row.get("xp") or 0)
    new_val = cur + int(amount)
    execute(guild_id, "UPDATE characters SET xp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))
    return new_val
