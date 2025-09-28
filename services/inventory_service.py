import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event   # pakai log_event biar konsisten
from services import item_service

# ===============================
# INVENTORY SERVICE (per-server) + ICONS + Carry System + Hard Limit
# ===============================

ICONS = {
    "add": "📥",
    "remove": "📤",
    "transfer": "🔄",
    "update": "📝",
    "bag": "🎒",
    "fail": "❌",
}

# ---------- Carry Calculation ----------
def calc_carry(guild_id: int, owner: str):
    """Hitung total weight dari inventory + equipment owner dan update ke characters.carry_used"""
    total_weight = 0.0

    # --- Inventory items ---
    rows = fetchall(
        guild_id,
        "SELECT qty, metadata FROM inventory WHERE owner=?",
        (owner,)
    )
    for r in rows:
        try:
            meta = json.loads(r["metadata"] or "{}")
            weight = float(meta.get("weight", 0))
            total_weight += weight * r["qty"]
        except Exception:
            continue

    # --- Equipment items ---
    row = fetchone(guild_id, "SELECT equipment FROM characters WHERE name=?", (owner,))
    if row and row.get("equipment"):
        try:
            eq = json.loads(row["equipment"] or "{}")
            for slot, item_name in eq.items():
                if not item_name:
                    continue
                item = item_service.get_item(guild_id, item_name)
                if item:
                    try:
                        total_weight += float(item.get("weight", 0))
                    except Exception:
                        continue
        except Exception:
            pass

    execute(
        guild_id,
        "UPDATE characters SET carry_used=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (total_weight, owner)
    )
    return total_weight

# ---------- CRUD ----------
def add_item(guild_id: int, owner, item_name, qty=1, metadata=None, user_id="0"):
    """Tambah item ke inventory (owner = karakter / 'party')."""

    # --- Ambil detail dari katalog kalau weight kosong ---
    if not metadata or "weight" not in metadata:
        item = item_service.get_item(guild_id, item_name)
        metadata = metadata or {}
        if item:
            metadata.setdefault("weight", item.get("weight", 0.1))
            metadata.setdefault("slot", item.get("slot", None))
            metadata.setdefault("rarity", item.get("rarity", "Common"))
            metadata.setdefault("effect", item.get("effect", ""))
        else:
            metadata.setdefault("weight", 0.1)

    # --- Validasi berat ---
    try:
        weight = float(metadata.get("weight", 0.1))
    except Exception:
        weight = 0.1
    if weight <= 0:
        weight = 0.1
        metadata["weight"] = weight

    # --- Cek kapasitas karakter (kalau ada) ---
    char = fetchone(guild_id, "SELECT carry_capacity, carry_used FROM characters WHERE name=?", (owner,))
    if char and char.get("carry_capacity", 0) > 0:
        projected = float(char.get("carry_used", 0) or 0) + (weight * qty)
        if projected > char["carry_capacity"]:
            return False  # overload

    # --- Tambah / update inventory ---
    row = fetchone(
        guild_id,
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if row:
        new_qty = row["qty"] + qty
        execute(guild_id, "UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute(guild_id, "INSERT INTO inventory (owner, item, qty, metadata) VALUES (?,?,?,?)",
                (owner, item_name, qty, json.dumps(metadata or {})))

    # sync carry
    calc_carry(guild_id, owner)

    # history
    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            ("loot_add", json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    # timeline log_event
    log_event(
        guild_id,
        user_id,
        code="INV_ADD",
        title=f"{ICONS['add']} {owner} mendapatkan {qty}x {item_name}",
        details=f"Item: {item_name}, Qty: {qty}",
        etype="inventory_add",
        actors=[owner],
        tags=["inventory","add"]
    )
    return True

def remove_item(guild_id: int, owner, item_name, qty=1, user_id="0"):
    """Kurangi item dari inventory."""
    row = fetchone(
        guild_id,
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if not row or row["qty"] < qty:
        return False

    new_qty = row["qty"] - qty
    if new_qty > 0:
        execute(guild_id, "UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute(guild_id, "DELETE FROM inventory WHERE id=?", (row["id"],))

    # sync carry
    calc_carry(guild_id, owner)

    execute(guild_id, "INSERT INTO history (action, data) VALUES (?,?)",
            ("loot_remove", json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    log_event(
        guild_id,
        user_id,
        code="INV_REMOVE",
        title=f"{ICONS['remove']} {owner} kehilangan {qty}x {item_name}",
        details=f"Item: {item_name}, Qty: {qty}",
        etype="inventory_remove",
        actors=[owner],
        tags=["inventory","remove"]
    )
    return True

def get_inventory(guild_id: int, owner):
    """Ambil semua item milik karakter/party."""
    rows = fetchall(
        guild_id,
        "SELECT item, qty, metadata FROM inventory WHERE owner=?",
        (owner,)
    )
    return [{"item": r["item"], "qty": r["qty"], "meta": json.loads(r["metadata"] or "{}")} for r in rows]

def transfer_item(guild_id: int, from_owner, to_owner, item_name, qty=1, user_id="0"):
    """Transfer item antar pemilik (metadata ikut terbawa)."""
    row = fetchone(guild_id, "SELECT * FROM inventory WHERE owner=? AND item=?", (from_owner, item_name))
    if not row or row["qty"] < qty:
        return False

    meta = json.loads(row["metadata"] or "{}")
    removed = remove_item(guild_id, from_owner, item_name, qty, user_id=user_id)
    if not removed:
        return False
    ok = add_item(guild_id, to_owner, item_name, qty, metadata=meta, user_id=user_id)

    if not ok:
        add_item(guild_id, from_owner, item_name, qty, metadata=meta, user_id=user_id)
        return False

    # sync carry untuk kedua owner
    calc_carry(guild_id, from_owner)
    calc_carry(guild_id, to_owner)

    log_event(
        guild_id,
        user_id,
        code="INV_TRANSFER",
        title=f"{ICONS['transfer']} {from_owner} → {to_owner}: {qty}x {item_name}",
        details=f"Transfer {qty} {item_name} dari {from_owner} ke {to_owner}",
        etype="inventory_transfer",
        actors=[from_owner, to_owner],
        tags=["inventory","transfer"]
    )
    return True

def update_metadata(guild_id: int, owner, item_name, metadata: dict, user_id="0"):
    """Update metadata item (rarity, type, notes, weight)."""
    row = fetchone(
        guild_id,
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if not row:
        return False

    meta = json.loads(row["metadata"] or "{}")
    meta.update(metadata)
    execute(guild_id, "UPDATE inventory SET metadata=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(meta), row["id"]))

    # sync carry
    calc_carry(guild_id, owner)

    log_event(
        guild_id,
        user_id,
        code="INV_UPDATE",
        title=f"{ICONS['update']} Metadata {owner}:{item_name} diperbarui",
        details=json.dumps(metadata),
        etype="inventory_update",
        actors=[owner],
        tags=["inventory","update"]
    )
    return True
