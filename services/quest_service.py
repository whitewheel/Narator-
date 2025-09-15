import json
from utils.db import execute, fetchone, fetchall
from services import inventory_service, status_service

# ===============================
# QUEST SERVICE
# ===============================

ICONS = {
    "quest": "📜",
    "check": "✅",
    "fail": "❌",
    "loot": "🎁",
    "favor": "💠",
    "xp": "⭐",
}

async def add_quest(guild_id, channel_id, title, detail="", items_required=None, rewards=None, created_by=None):
    """Tambah quest baru."""
    execute(
        "INSERT INTO quests (guild_id, channel_id, title, detail, items_required, rewards, created_by) VALUES (?,?,?,?,?,?,?)",
        (guild_id, channel_id, title, detail, json.dumps(items_required or []), json.dumps(rewards or {}), created_by),
    )

    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['quest']} Quest baru ditambahkan: **{title}**"))
    return True


async def complete_quest(guild_id, channel_id, title, owner="party"):
    """Selesaikan quest (cek item lalu kasih reward)."""
    quest = fetchone("SELECT * FROM quests WHERE guild_id=? AND channel_id=? AND title=?",
                     (guild_id, channel_id, title))
    if not quest:
        return f"{ICONS['fail']} Quest tidak ditemukan."

    if quest["status"] != "open":
        return f"{ICONS['fail']} Quest ini sudah {quest['status']}."

    items_required = json.loads(quest["items_required"] or "[]")
    rewards = json.loads(quest["rewards"] or "{}")

    # cek inventory
    missing = []
    for item in items_required:
        rows = await inventory_service.get_inventory(guild_id, channel_id, owner)
        if not any(r["item"].lower() == item.lower() and r["qty"] > 0 for r in rows):
            missing.append(item)

    if missing:
        return f"{ICONS['fail']} Tidak bisa selesaikan quest. Item kurang: {', '.join(missing)}"

    # update quest status
    execute("UPDATE quests SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (quest["id"],))

    # berikan reward
    msg_parts = [f"{ICONS['check']} Quest **{quest['title']}** selesai!"]
    if "loot" in rewards:
        for item, qty in rewards["loot"].items():
            await inventory_service.add_item(guild_id, channel_id, owner, item, qty)
            msg_parts.append(f"{ICONS['loot']} {qty}x {item}")
    if "favor" in rewards:
        msg_parts.append(f"{ICONS['favor']} Favor +{rewards['favor']}")
    if "xp" in rewards:
        # XP bisa dimasukkan ke karakter status (contoh pakai notes / custom field)
        msg_parts.append(f"{ICONS['xp']} {rewards['xp']} XP")

    # log timeline
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['check']} Quest **{quest['title']}** selesai."))

    return "\n".join(msg_parts)


async def list_quests(guild_id, channel_id):
    """Ambil semua quest di channel ini."""
    rows = fetchall("SELECT * FROM quests WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
    if not rows:
        return f"{ICONS['quest']} Tidak ada quest."

    out = []
    for r in rows:
        icon = ICONS["check"] if r["status"] == "completed" else ICONS["quest"]
        out.append(f"{icon} **{r['title']}** — {r['status']}")
    return "\n".join(out)
