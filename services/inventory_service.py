import json
from utils.db import execute, fetchone, fetchall

# ===============================
# INVENTORY SERVICE
# ===============================

async def add_item(guild_id, channel_id, owner, item_name, qty=1, metadata=None):
    """Tambah item ke inventory (owner = karakter / 'party')."""
    row = fetchone(
        "SELECT * FROM inventory WHERE guild_id=? AND channel_id=? AND owner=? AND item=?",
        (guild_id, channel_id, owner, item_name)
    )
    if row:
        new_qty = row["qty"] + qty
        execute("UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute("INSERT INTO inventory (guild_id, channel_id, owner, item, qty, metadata) VALUES (?,?,?,?,?,?)",
                (guild_id, channel_id, owner, item_name, qty, json.dumps(metadata or {})))

    # log history
    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "loot_add",
             json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    # log timeline
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{owner} mendapatkan {qty}x {item_name}"))
    return True


async def remove_item(guild_id, channel_id, owner, item_name, qty=1):
    """Kurangi item dari inventory."""
    row = fetchone(
        "SELECT * FROM inventory WHERE guild_id=? AND channel_id=? AND owner=? AND item=?",
        (guild_id, channel_id, owner, item_name)
    )
    if not row or row["qty"] < qty:
        return False

    new_qty = row["qty"] - qty
    if new_qty > 0:
        execute("UPDATE inventory SET qty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_qty, row["id"]))
    else:
        execute("DELETE FROM inventory WHERE id=?", (row["id"],))

    # log history
    execute("INSERT INTO history (guild_id, channel_id, action, data) VALUES (?,?,?,?)",
            (guild_id, channel_id, "loot_remove",
             json.dumps({"owner": owner, "item": item_name, "qty": qty})))

    # log timeline
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{owner} kehilangan {qty}x {item_name}"))
    return True


async def get_inventory(guild_id, channel_id, owner):
    """Ambil semua item milik karakter/party."""
    rows = fetchall(
        "SELECT item, qty, metadata FROM inventory WHERE guild_id=? AND channel_id=? AND owner=?",
        (guild_id, channel_id, owner)
    )
    return [{"item": r["item"], "qty": r["qty"], "meta": json.loads(r["metadata"] or "{}")} for r in rows]


async def transfer_item(guild_id, channel_id, from_owner, to_owner, item_name, qty=1):
    """Transfer item antar pemilik."""
    removed = await remove_item(guild_id, channel_id, from_owner, item_name, qty)
    if not removed:
        return False
    await add_item(guild_id, channel_id, to_owner, item_name, qty)
    return True


async def update_metadata(guild_id, channel_id, owner, item_name, metadata: dict):
    """Update metadata item (rarity, type, notes)."""
    row = fetchone(
        "SELECT * FROM inventory WHERE guild_id=? AND channel_id=? AND owner=? AND item=?",
        (guild_id, channel_id, owner, item_name)
    )
    if not row:
        return False

    meta = json.loads(row["metadata"] or "{}")
    meta.update(metadata)
    execute("UPDATE inventory SET metadata=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(meta), row["id"]))
    return True
