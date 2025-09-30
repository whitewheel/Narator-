import json
from utils.db import fetchone, fetchall, execute
from services import item_service, inventory_service, favor_service, quest_service

ICON_DEFAULT = "📦"

# ===============================
# TABLE ENSURE
# ===============================
def ensure_table(guild_id: int):
    execute(guild_id, """
        CREATE TABLE IF NOT EXISTS npc_shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npc_name TEXT,
            item TEXT,
            price INTEGER DEFAULT 0,
            stock INTEGER DEFAULT -1,   -- -1 = unlimited
            favor_req TEXT DEFAULT '{}', -- JSON {"Faction":2}
            quest_req TEXT DEFAULT '[]', -- JSON ["QuestName"]
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(npc_name, item)
        )
    """)

# ===============================
# CRUD SHOP
# ===============================
def add_item(guild_id: int, npc_name: str, item: str, price: int, stock: int = -1,
             favor_req: dict | None = None, quest_req: list | None = None):
    """Tambah/update item ke shop NPC."""
    ensure_table(guild_id)
    execute(
        guild_id,
        """
        INSERT INTO npc_shop (npc_name, item, price, stock, favor_req, quest_req)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(npc_name,item) DO UPDATE SET
            price=excluded.price,
            stock=excluded.stock,
            favor_req=excluded.favor_req,
            quest_req=excluded.quest_req,
            updated_at=CURRENT_TIMESTAMP
        """,
        (npc_name, item, price, stock,
         json.dumps(favor_req or {}),
         json.dumps(quest_req or []))
    )
    return True

def remove_item(guild_id: int, npc_name: str, item: str):
    """Hapus 1 item dari shop NPC."""
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM npc_shop WHERE npc_name=? AND item=?",
            (npc_name, item))
    return True

def clear_shop(guild_id: int, npc_name: str):
    """Hapus semua dagangan NPC."""
    ensure_table(guild_id)
    execute(guild_id, "DELETE FROM npc_shop WHERE npc_name=?", (npc_name,))
    return True

# ===============================
# HELPERS
# ===============================
def _check_requirements(guild_id: int, row, char_name: str):
    """Cek apakah character memenuhi syarat favor & quest."""
    favor_req = json.loads(row.get("favor_req") or "{}")
    quest_req = json.loads(row.get("quest_req") or "[]")

    # Favor check
    if favor_req:
        for fac, need in favor_req.items():
            f = fetchone(guild_id,
                         "SELECT favor FROM favors WHERE char_name=? AND faction=?",
                         (char_name, fac))
            have = f["favor"] if f else 0
            if have < need:
                return False

    # Quest check
    if quest_req:
        for qname in quest_req:
            q = quest_service.get_quest(guild_id, qname)
            if not q or q["status"] != "completed":
                return False

    return True

# ===============================
# LIST
# ===============================
def list_items(guild_id: int, npc_name: str, char_name: str | None = None, gm_view: bool = False):
    """List semua dagangan NPC. Kalau char_name diberikan → cek lock quest/favor."""
    ensure_table(guild_id)
    rows = fetchall(
        guild_id,
        """
        SELECT s.*
        FROM npc_shop s
        LEFT JOIN items i ON s.item = i.name
        WHERE s.npc_name=?
        ORDER BY i.name COLLATE NOCASE ASC
        """,
        (npc_name,)
    )

    if not rows:
        return [f"ℹ️ {npc_name} tidak menjual apa-apa."]

    out = []
    for r in rows:
        item_data = item_service.get_item(guild_id, r["item"])
        effect = item_data.get("effect", "-") if item_data else "-"
        requirement = item_data.get("requirement", "") if item_data else ""  # ✅ baru
        req_text = f"\n⚠️ Req: {requirement}" if requirement else ""         # ✅ baru
        icon = item_data.get("icon", ICON_DEFAULT) if item_data else ICON_DEFAULT

        price = r["price"]
        stock = r["stock"]
        stock_text = "∞" if stock < 0 else str(stock)

        locked = False
        if not gm_view and char_name:
            locked = not _check_requirements(guild_id, r, char_name)

        if locked:
            out.append(
                f"{icon} **{r['item']}** — 💰 - gold | Stock: -\n"
                f"🔒 Sebuah misi harus selesai / butuh syarat tertentu"
            )
        else:
            out.append(
                f"{icon} **{r['item']}** — 💰 {price} gold | Stock: {stock_text}\n"
                f"✨ {effect}{req_text}"
            )
    return out

# ===============================
# BUY
# ===============================
def buy_item(guild_id: int, npc_name: str, char_name: str, item: str, qty: int = 1):
    """Player beli item dari NPC shop."""
    ensure_table(guild_id)

    # cek dagangan
    r = fetchone(
        guild_id,
        "SELECT * FROM npc_shop WHERE npc_name=? AND item=?",
        (npc_name, item)
    )
    if not r:
        return False, f"❌ {npc_name} tidak menjual {item}."

    # cek requirements
    if not _check_requirements(guild_id, r, char_name):
        return False, f"🔒 {char_name} belum memenuhi syarat untuk membeli {item}."

    price = int(r["price"]) * qty
    stock = int(r["stock"])

    # cek karakter punya gold?
    char = fetchone(guild_id, "SELECT gold, carry_capacity, carry_used FROM characters WHERE name=?", (char_name,))
    if not char:
        return False, f"❌ Karakter {char_name} tidak ditemukan."
    gold = int(char.get("gold", 0))
    if gold < price:
        return False, f"❌ {char_name} tidak punya cukup gold ({gold}/{price})."

    # cek stock
    if stock >= 0 and stock < qty:
        return False, f"❌ Stok {item} di {npc_name} hanya {stock}."

    # cek carry capacity
    item_data = item_service.get_item(guild_id, item)
    weight = float(item_data.get("weight", 0)) if item_data else 0
    new_carry = (char.get("carry_used", 0) or 0) + weight * qty
    if new_carry > (char.get("carry_capacity", 0) or 0):
        return False, f"⚖️ {char_name} kelebihan beban! Tidak bisa membeli {item}."

    # kurangi gold
    new_gold = gold - price
    execute(guild_id, "UPDATE characters SET gold=?, carry_used=? WHERE name=?",
            (new_gold, new_carry, char_name))

    # kurangi stock (kecuali unlimited)
    if stock >= 0:
        new_stock = stock - qty
        execute(guild_id, "UPDATE npc_shop SET stock=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_stock, r["id"]))

    # tambahkan item ke inventory
    inventory_service.add_item(guild_id, char_name, item, qty, user_id="system")

    return True, f"✅ {char_name} membeli {qty}x {item} dari {npc_name} seharga {price} gold."
