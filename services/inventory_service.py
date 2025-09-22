import json
from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event   # pakai log_event biar konsisten

# ===============================
# INVENTORY SERVICE (Global)
# ===============================

def add_item(owner, item_name, qty=1, metadata=None, user_id="0"):
    """Tambah item ke inventory (owner = karakter / 'party')."""
    row = fetchone(
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if row:
        new_qty = row["qty"] + qty
        execute("UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute("INSERT INTO inventory (owner, item, qty, metadata) VALUES (?,?,?,?)",
                (owner, item_name, qty, json.dumps(metadata or {})))

    # history
    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("loot_add", json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    # timeline log_event
    log_event("0", "0", user_id,
              code="INV_ADD",
              title=f"{owner} mendapatkan {qty}x {item_name}",
              details=f"Item: {item_name}, Qty: {qty}",
              etype="inventory_add",
              actors=[owner],
              tags=["inventory","add"])
    return True


def remove_item(owner, item_name, qty=1, user_id="0"):
    """Kurangi item dari inventory."""
    row = fetchone(
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if not row or row["qty"] < qty:
        return False

    new_qty = row["qty"] - qty
    if new_qty > 0:
        execute("UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute("DELETE FROM inventory WHERE id=?", (row["id"],))

    execute("INSERT INTO history (action, data) VALUES (?,?)",
            ("loot_remove", json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    log_event("0", "0", user_id,
              code="INV_REMOVE",
              title=f"{owner} kehilangan {qty}x {item_name}",
              details=f"Item: {item_name}, Qty: {qty}",
              etype="inventory_remove",
              actors=[owner],
              tags=["inventory","remove"])
    return True


def get_inventory(owner):
    """Ambil semua item milik karakter/party."""
    rows = fetchall(
        "SELECT item, qty, metadata FROM inventory WHERE owner=?",
        (owner,)
    )
    return [{"item": r["item"], "qty": r["qty"], "meta": json.loads(r["metadata"] or "{}")} for r in rows]


def transfer_item(from_owner, to_owner, item_name, qty=1, user_id="0"):
    """Transfer item antar pemilik (metadata ikut terbawa)."""
    row = fetchone("SELECT * FROM inventory WHERE owner=? AND item=?", (from_owner, item_name))
    if not row or row["qty"] < qty:
        return False

    meta = json.loads(row["metadata"] or "{}")
    removed = remove_item(from_owner, item_name, qty, user_id=user_id)
    if not removed:
        return False
    add_item(to_owner, item_name, qty, metadata=meta, user_id=user_id)
    return True


def update_metadata(owner, item_name, metadata: dict):
    """Update metadata item (rarity, type, notes)."""
    row = fetchone(
        "SELECT * FROM inventory WHERE owner=? AND item=?",
        (owner, item_name)
    )
    if not row:
        return False

    meta = json.loads(row["metadata"] or "{}")
    meta.update(metadata)
    execute("UPDATE inventory SET metadata=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(meta), row["id"]))
    return True
