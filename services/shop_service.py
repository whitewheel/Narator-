# services/shop_service.py
import json
from utils.db import fetchone, fetchall, execute
from services import item_service, inventory_service

ICON = "📦"

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
            quest_req TEXT DEFAULT '[]', -- JSON ["QuestID"]
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

def list_items(guild_id: int, npc_name: str, char_name: str | None = None):
    """List semua dagangan NPC. Favor/Quest req belum dipakai penuh (next step)."""
    ensure_table(guild_id)
    rows = fetchall(guild_id, "SELECT * FROM npc_shop WHERE npc_name=?", (npc_name,))
    if not rows:
        return [f"ℹ️ {npc_name} tidak menjual apa-apa."]
    
    out = []
    for r in rows:
        item_data = item_service.get_item(guild_id, r["item"])
        effect = item_data.get("effect", "-") if item_data else "-"
        price = r["price"]
        stock = r["stock"]
        stock_text = "∞" if stock < 0 else str(stock)
        out.append(f"{ICON} **{r['item']}** — 💰 {price} gold | Stock: {stock_text}\n✨ {effect}")
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

    price = int(r["price"]) * qty
    stock = int(r["stock"])

    # cek karakter punya gold?
    char = fetchone(guild_id, "SELECT gold FROM characters WHERE name=?", (char_name,))
    if not char:
        return False, f"❌ Karakter {char_name} tidak ditemukan."
    gold = int(char.get("gold", 0))
    if gold < price:
        return False, f"❌ {char_name} tidak punya cukup gold ({gold}/{price})."

    # cek stock
    if stock >= 0 and stock < qty:
        return False, f"❌ Stok {item} di {npc_name} hanya {stock}."

    # kurangi gold
    new_gold = gold - price
    execute(guild_id, "UPDATE characters SET gold=? WHERE name=?",
            (new_gold, char_name))

    # kurangi stock (kecuali unlimited)
    if stock >= 0:
        new_stock = stock - qty
        execute(guild_id, "UPDATE npc_shop SET stock=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_stock, r["id"]))

    # tambahkan item ke inventory
    inventory_service.add_item(guild_id, char_name, item, qty, user_id="system")

    return True, f"✅ {char_name} membeli {qty}x {item} dari {npc_name} seharga {price} gold."
