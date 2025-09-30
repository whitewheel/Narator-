import json
from utils.db import fetchone, execute
from services import inventory_service, item_service
from cogs.world.timeline import log_event

# ===============================
# EQUIPMENT SERVICE
# ===============================

SLOTS = [
    "main_hand", "off_hand",
    "armor_inner", "armor_outer",
    "accessory1", "accessory2", "accessory3",
    "augment1", "augment2", "augment3",
]

# Ikon default untuk setiap slot
SLOT_ICONS = {
    "main_hand": "🗡️",
    "off_hand": "🔪",
    "armor_inner": "👕",
    "armor_outer": "🛡️",
    "accessory1": "💍",
    "accessory2": "💍",
    "accessory3": "💍",
    "augment1": "🧬",
    "augment2": "🧬",
    "augment3": "🧬",
}

def _norm_name(x: str) -> str:
    try:
        return item_service.normalize_name(x)
    except Exception:
        return (x or "").strip()

def _get_char(guild_id: int, char: str):
    return fetchone(guild_id, "SELECT * FROM characters WHERE name=?", (char,))

def _update_equipment(guild_id: int, char: str, eq: dict):
    execute(
        guild_id,
        "UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (json.dumps(eq), char)
    )

def equip_item(guild_id: int, char: str, slot: str, item_name: str, user_id="0"):
    """Equip item dari inventory ke slot equipment karakter (cek carry)."""
    slot = (slot or "").lower()
    if slot not in SLOTS:
        return False, f"❌ Slot tidak valid. Pilih: {', '.join(SLOTS)}"

    # cek karakter
    c = _get_char(guild_id, char)
    if not c:
        return False, f"❌ Karakter {char} tidak ditemukan."

    # cek item di inventory (case-insens + normalisasi)
    inv = inventory_service.get_inventory(guild_id, char)
    target = _norm_name(item_name)
    found = next(
        (it for it in inv if _norm_name(it["item"]) == target and (it["qty"] or 0) > 0),
        None
    )
    if not found:
        return False, f"❌ {char} tidak punya \"{item_name}\" di inventory."

    # cek data item (ambil weight)
    item_data = item_service.get_item(guild_id, target)
    weight = float(item_data.get("weight", 0)) if item_data else 0.0

    carry_capacity = c.get("carry_capacity", 0) or 0
    carry_used = c.get("carry_used", 0.0) or 0.0
    if carry_capacity > 0 and carry_used + weight > carry_capacity:
        return False, f"❌ {char} tidak sanggup equip {item_name} (melebihi kapasitas)."

    # ambil equipment json
    eq = json.loads(c.get("equipment") or "{}")
    if not eq:
        eq = {s: "" for s in SLOTS}

    # kalau slot sudah terisi, balikin ke inventory
    if eq.get(slot):
        inventory_service.add_item(guild_id, char, eq[slot], 1, user_id=user_id)

    # pasang item
    eq[slot] = found["item"]  # simpan nama persis dari inventory
    _update_equipment(guild_id, char, eq)

    # kurangi inventory
    inventory_service.remove_item(guild_id, char, found["item"], 1, user_id=user_id)

    # sync carry
    inventory_service.calc_carry(guild_id, char)

    # log
    log_event(
        guild_id,
        user_id,
        code="EQUIP",
        title=f"⚔️ {char} equip {found['item']} ke {slot}",
        details=f"{char} equip {found['item']} di slot {slot}",
        etype="equip",
        actors=[char],
        tags=["equipment", "equip"]
    )

    return True, f"⚔️ {char} sekarang memakai {found['item']} di slot {slot}."

def unequip_item(guild_id: int, char: str, slot: str, user_id="0"):
    """Unequip item dari slot ke inventory karakter (boleh overload)."""
    slot = (slot or "").lower()
    if slot not in SLOTS:
        return False, f"❌ Slot tidak valid. Pilih: {', '.join(SLOTS)}"

    c = _get_char(guild_id, char)
    if not c:
        return False, f"❌ Karakter {char} tidak ditemukan."

    eq = json.loads(c.get("equipment") or "{}")
    if not eq:
        eq = {s: "" for s in SLOTS}
    if not eq.get(slot):
        return False, f"❌ Slot {slot} kosong."

    item_name = eq[slot]

    # balikin ke inventory
    inventory_service.add_item(guild_id, char, item_name, 1, user_id=user_id)

    # kosongkan slot
    eq[slot] = ""
    _update_equipment(guild_id, char, eq)

    # sync carry
    inventory_service.calc_carry(guild_id, char)

    log_event(
        guild_id,
        user_id,
        code="UNEQUIP",
        title=f"🛑 {char} melepas {item_name} dari {slot}",
        details=f"{char} unequip {item_name} dari slot {slot}",
        etype="unequip",
        actors=[char],
        tags=["equipment", "unequip"]
    )

    return True, f"🛑 {char} melepas {item_name} dari slot {slot}."

def show_equipment(guild_id: int, char: str):
    """Ambil daftar equipment karakter."""
    c = _get_char(guild_id, char)
    if not c:
        return None

    eq = json.loads(c.get("equipment") or "{}")
    if not eq:
        eq = {s: "" for s in SLOTS}

    out = []
    for s in SLOTS:
        item = eq.get(s, "")
        icon = SLOT_ICONS.get(s, "▫️")
        if item:
            it = item_service.get_item(guild_id, item)
            item_icon = it["icon"] if it else "📦"
            out.append(f"{icon} **{s}**: {item_icon} {item}")
        else:
            out.append(f"{icon} **{s}**: (kosong)")
    return out
