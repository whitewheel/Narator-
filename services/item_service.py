import json
from utils.db import execute, fetchone, fetchall

# ===============================
# ITEM SERVICE (per-server) + ICONS
# ===============================

ICONS = {
    "weapon": "🗡️",
    "armor": "🛡️",
    "accessory": "💍",
    "consumable": "🧪",
    "gadget": "🔧",
    "misc": "📦",
}

RARITY_ORDER = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 3,
    "Very Rare": 4,
    "Legendary": 5
}

RARITY_ICON = {
    "Common": "🟢",
    "Uncommon": "🔵",
    "Rare": "🟣",
    "Very Rare": "🟡",
    "Legendary": "🔴"
}

def ensure_table(guild_id: int):
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            effect TEXT,
            rarity TEXT DEFAULT 'Common',
            value INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.1,
            slot TEXT,
            notes TEXT,
            rules TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def add_item(guild_id: int, data: dict):
    """Tambah atau update item di katalog (per-server)."""
    ensure_table(guild_id)

    # --- Validasi weight ---
    weight = data.get("weight", 0.1)
    try:
        weight = float(weight)
    except Exception:
        weight = 0.1
    if weight <= 0:
        weight = 0.1

    execute(guild_id, """
        INSERT INTO items (name, type, effect, rarity, value, weight, slot, notes, rules)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            type=excluded.type,
            effect=excluded.effect,
            rarity=excluded.rarity,
            value=excluded.value,
            weight=excluded.weight,
            slot=excluded.slot,
            notes=excluded.notes,
            rules=excluded.rules,
            updated_at=CURRENT_TIMESTAMP
    """, (
        data.get("name"),
        data.get("type"),
        data.get("effect"),
        data.get("rarity","Common"),
        data.get("value",0),
        weight,
        data.get("slot"),
        data.get("notes",""),
        data.get("rules","")
    ))
    return True

def update_item(guild_id: int, name: str, updates: dict):
    """Update sebagian field item (dipakai untuk !item edit)."""
    row = get_item(guild_id, name)
    if not row:
        return False

    row.update(updates)
    return add_item(guild_id, row)

def get_item(guild_id: int, name: str):
    """Ambil detail 1 item dengan ikon."""
    row = fetchone(guild_id, "SELECT * FROM items WHERE name=?", (name,))
    if not row:
        return None
    item = dict(row)
    item["icon"] = ICONS.get(item.get("type","").lower(), ICONS["misc"])
    return item

def list_items(guild_id: int, limit: int = 50):
    """Ambil semua item, urut per Type → Rarity → Nama (A–Z), dengan ikon rarity."""
    rows = fetchall(guild_id, "SELECT * FROM items", ())
    if not rows:
        return []

    categories = {}
    for r in rows:
        type_key = (r.get("type") or "Misc").capitalize()
        rarity = r.get("rarity", "Common")
        base_icon = ICONS.get(r.get("type","").lower(), ICONS["misc"])
        rarity_icon = RARITY_ICON.get(rarity, "⬜")
        entry = {
            "name": r["name"],
            "rarity": rarity,
            "text": f"{rarity_icon} {base_icon} **{r['name']}** ({rarity})"
        }
        categories.setdefault(type_key, []).append(entry)

    out = []
    for cat in sorted(categories.keys()):
        out.append(f"__**{cat}**__")

        sorted_entries = sorted(
            categories[cat],
            key=lambda e: (RARITY_ORDER.get(e["rarity"], 99), e["name"].lower())
        )

        for e in sorted_entries:
            out.append(e["text"])

        out.append("")  # spasi antar kategori

    return out[:limit] if limit else out

def remove_item(guild_id: int, name: str):
    """Hapus item dari katalog."""
    execute(guild_id, "DELETE FROM items WHERE name=?", (name,))
    return True

def search_items(guild_id: int, keyword: str, limit: int = 20):
    """Cari item by keyword (nama/tipe/efek) + ikon."""
    rows = fetchall(
        guild_id,
        "SELECT * FROM items WHERE name LIKE ? OR type LIKE ? OR effect LIKE ? LIMIT ?",
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit)
    )
    out = []
    for r in rows:
        icon = ICONS.get(r.get("type","").lower(), ICONS["misc"])
        out.append(f"{icon} **{r['name']}** — {r.get('effect','')}")
    return out
