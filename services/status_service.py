import json
from utils.db import execute, fetchone, fetchall

# ===============================
# STATUS SERVICE (Global)
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
    """
    Nilai baseline aman untuk INSERT awal (jaga kolom penting terisi).
    Sesuaikan dengan schema kamu; kalau ada kolom tambahan, SQLite akan isi defaultnya.
    """
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
        # kolom reward & loot untuk enemies
        base.update({
            "xp_reward": 0, "gold_reward": 0, "loot": "[]"
        })
    return base

def _ensure_exists(table: str, name: str) -> dict:
    """
    Pastikan row ada. Kalau belum, INSERT minimal baseline.
    Return row (dict).
    """
    row = fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))
    if row:
        return row

    base = _baseline_row(table, name)

    cols = ", ".join(base.keys())
    placeholders = ", ".join(["?"] * len(base))
    values = tuple(base.values())
    execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)

    return fetchone(f"SELECT * FROM {table} WHERE name=?", (name,))

# ===============================
# HP / VITALS
# ===============================
async def damage(target_type, name, amount: int):
    table = _table(target_type)
    row = _ensure_exists(table, name)

    # jaga hp_max supaya tidak None
    hp_max = int(row.get("hp_max") or 0)
    cur_hp = int(row.get("hp") or 0)

    new_hp = max(0, cur_hp - int(amount))
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    # Log
    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("dmg", json.dumps({
                "target": name, "type": target_type,
                "old": cur_hp, "new": new_hp, "amount": int(amount)
            })))
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{name} menerima {int(amount)} damage → {new_hp}/{hp_max} HP",))
    return new_hp

async def heal(target_type, name, amount: int):
    table = _table(target_type)
    row = _ensure_exists(table, name)

    hp_max = int(row.get("hp_max") or 0)
    cur_hp = int(row.get("hp") or 0)

    # kalau hp_max = 0 dan kita heal, anggap hp_max = cur_hp + amount (biar tidak kunci di 0)
    if hp_max <= 0:
        hp_max = cur_hp + int(amount)
        execute(f"UPDATE {table} SET hp_max=? WHERE id=?", (hp_max, row["id"]))

    new_hp = min(hp_max, cur_hp + int(amount))
    execute(f"UPDATE {table} SET hp=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_hp, row["id"]))

    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("heal", json.dumps({
                "target": name, "type": target_type,
                "old": cur_hp, "new": new_hp, "amount": int(amount)
            })))
    execute("INSERT INTO timeline (event) VALUES (?)",
            (f"{name} disembuhkan {int(amount)} HP → {new_hp}/{hp_max} HP",))
    return new_hp

async def use_resource(target_type, name, field: str, amount: int, regen=False):
    """
    field: "energy" atau "stamina" (atau field lain yang punya _max)
    """
    table = _table(target_type)
    row = _ensure_exists(table, name)

    cur = int(row.get(field) or 0)
    mx = int(row.get(f"{field}_max") or 0)

    # kalau max = 0 dan mau regen, set max = cur + amount biar tidak mentok 0
    if regen and mx <= 0:
        mx = cur + int(amount)
        execute(f"UPDATE {table} SET {field}_max=? WHERE id=?", (mx, row["id"]))

    new_val = min(mx, cur + int(amount)) if regen else max(0, cur - int(amount))

    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_val, row["id"]))

    action = "regen" if regen else "use"
    execute("INSERT INTO history (action, data) VALUES (?,?)",
            (f"{field}_{action}", json.dumps({
                "target": name, "type": target_type,
                "old": cur, "new": new_val, "amount": int(amount)
            })))
    return new_val

# ===============================
# EFFECTS (single column: effects)
# ===============================
async def add_effect(target_type, name, effect: str, is_buff=True):
    """
    Semua efek disimpan di kolom 'effects' (JSON array).
    Item: {"text": "...", "type": "buff"/"debuff", "duration": -1}
    """
    table = _table(target_type)
    row = _ensure_exists(table, name)

    effects = json.loads(row.get("effects") or "[]")
    effects.append({"text": effect, "type": "buff" if is_buff else "debuff", "duration": -1})
    execute(f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(effects), row["id"]))
    return effects

async def clear_effects(target_type, name, is_buff=True):
    """
    Hapus efek berdasarkan tipe (buff/debuff) dari kolom 'effects'.
    """
    table = _table(target_type)
    row = _ensure_exists(table, name)

    effects = json.loads(row.get("effects") or "[]")
    keep = [e for e in effects if (e.get("type") or "").lower() != ("buff" if is_buff else "debuff")]
    execute(f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(keep), row["id"]))
    return keep

async def tick_all_effects():
    """Kurangi durasi semua efek (char & enemy). Hanya kolom 'effects' yang dipakai."""
    results = {"char": {}, "enemy": {}}
    for ttype, table in [("char", "characters"), ("enemy", "enemies")]:
        rows = fetchall(f"SELECT * FROM {table}")
        for r in rows:
            effects = json.loads(r.get("effects") or "[]")
            new_effects, expired = [], []
            for e in effects:
                dur = int(e.get("duration", -1))
                if dur == -1:              # permanent
                    new_effects.append(e)
                elif dur > 1:              # masih sisa
                    e["duration"] = dur - 1
                    new_effects.append(e)
                else:                      # habis
                    expired.append(e)

            execute(f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps(new_effects), r["id"]))

            for e in expired:
                execute("INSERT INTO timeline (event) VALUES (?)",
                        (f"{ICONS['expired']} {r['name']} kehilangan efek: {e.get('text','')}",))

            results[ttype][r["name"]] = {"remaining": new_effects, "expired": expired}
    return results

# ===============================
# EQUIPMENT
# ===============================
async def set_equipment(name, slot: str, item: str):
    row = _ensure_exists("characters", name)
    eq = json.loads(row.get("equipment") or "{}")
    eq[slot] = item
    execute("UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(eq), row["id"]))
    return eq

# ===============================
# COMPANIONS
# ===============================
async def add_companion(name, comp: dict):
    row = _ensure_exists("characters", name)
    comps = json.loads(row.get("companions") or "[]")
    comps.append(comp)
    execute("UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

async def remove_companion(name, comp_name: str):
    row = _ensure_exists("characters", name)
    comps = json.loads(row.get("companions") or "[]")
    comps = [c for c in comps if c.get("name","").lower() != comp_name.lower()]
    execute("UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(comps), row["id"]))
    return comps

# ===============================
# GENERIC FIELD UPDATE (Upsert)
# ===============================
async def set_status(target_type, name, field: str, value):
    """
    Update field tertentu; bila row belum ada → auto INSERT baseline lalu UPDATE.
    """
    table = _table(target_type)
    row = _ensure_exists(table, name)

    old_value = row.get(field)
    execute(f"UPDATE {table} SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (value, row["id"]))

    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("set_status", json.dumps({
                "target": name, "type": target_type,
                "field": field, "old": old_value, "new": value
            })))
    return value
