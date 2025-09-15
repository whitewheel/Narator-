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

# ---------- CRUD ----------
async def add_quest(guild_id, channel_id, title, detail="", items_required=None, rewards=None, created_by=None, hidden=False):
    """Tambah quest baru."""
    status = "hidden" if hidden else "open"
    execute(
        "INSERT INTO quests (guild_id, channel_id, title, detail, status, items_required, rewards, created_by) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (guild_id, channel_id, title, detail, status,
         json.dumps(items_required or []),
         json.dumps(rewards or {}),
         created_by),
    )
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['quest']} Quest baru ditambahkan: **{title}**"))
    return True


def get_quest(guild_id, channel_id, title):
    """Ambil 1 quest berdasarkan judul."""
    return fetchone("SELECT * FROM quests WHERE guild_id=? AND channel_id=? AND title=?",
                    (guild_id, channel_id, title))


def list_quests(guild_id, channel_id, status="all"):
    """Ambil semua quest di channel ini, bisa filter status."""
    rows = fetchall("SELECT * FROM quests WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
    if not rows:
        return f"{ICONS['quest']} Tidak ada quest."

    out = []
    for r in rows:
        if status != "all" and r["status"].lower() != status.lower():
            continue
        icon = ICONS["check"] if r["status"] == "completed" else (
            ICONS["fail"] if r["status"] == "failed" else ICONS["quest"]
        )
        out.append(f"{icon} **{r['title']}** — {r['status']}")
    return "\n".join(out)


def update_status(guild_id, channel_id, title, new_status):
    """Update status quest (open/completed/failed/hidden)."""
    execute(
        "UPDATE quests SET status=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND channel_id=? AND title=?",
        (new_status, guild_id, channel_id, title),
    )
    return True


def set_rewards(guild_id, channel_id, title, rewards: dict):
    """Set rewards quest."""
    execute(
        "UPDATE quests SET rewards=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND channel_id=? AND title=?",
        (json.dumps(rewards), guild_id, channel_id, title),
    )
    return True


def assign_characters(guild_id, channel_id, title, chars: list):
    """Assign quest ke karakter tertentu."""
    execute(
        "UPDATE quests SET assigned_to=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND channel_id=? AND title=?",
        (json.dumps(chars), guild_id, channel_id, title),
    )
    return True


# ---------- Penyelesaian Quest ----------
async def complete_quest(guild_id, channel_id, title, targets: list = None, owner="party"):
    """Selesaikan quest, cek item, kasih reward ke target characters."""
    quest = get_quest(guild_id, channel_id, title)
    if not quest:
        return f"{ICONS['fail']} Quest tidak ditemukan."

    if quest["status"] != "open":
        return f"{ICONS['fail']} Quest ini sudah {quest['status']}."

    items_required = json.loads(quest["items_required"] or "[]")
    rewards = json.loads(quest["rewards"] or "{}")
    assigned = json.loads(quest.get("assigned_to") or "[]")

    # Tentukan target
    if not targets:
        targets = assigned or [owner]

    # cek item requirement
    missing = []
    for item in items_required:
        rows = await inventory_service.get_inventory(guild_id, channel_id, owner)
        if not any(r["item"].lower() == item.lower() and r["qty"] > 0 for r in rows):
            missing.append(item)

    if missing:
        return f"{ICONS['fail']} Tidak bisa selesaikan quest. Item kurang: {', '.join(missing)}"

    # update quest status
    update_status(guild_id, channel_id, title, "completed")

    # berikan reward
    msg_parts = [f"{ICONS['check']} Quest **{quest['title']}** selesai!"]

    # XP
    if "xp" in rewards and rewards["xp"] > 0:
        for ch in targets:
            await status_service.set_status(guild_id, channel_id, "char", ch, "xp", rewards["xp"])
        msg_parts.append(f"{ICONS['xp']} {rewards['xp']} XP")

    # Gold
    if "gold" in rewards and rewards["gold"] > 0:
        for ch in targets:
            await status_service.set_status(guild_id, channel_id, "char", ch, "gold", rewards["gold"])
        msg_parts.append(f"💰 {rewards['gold']} Gold")

    # Loot
    if "loot" in rewards:
        for item, qty in rewards["loot"].items():
            for ch in targets:
                await inventory_service.add_item(guild_id, channel_id, ch, item, qty)
            msg_parts.append(f"{ICONS['loot']} {qty}x {item}")

    # Favor
    if "favor" in rewards:
        fav_txt = []
        for fac, val in rewards["favor"].items():
            fav_txt.append(f"{fac}: {val:+d}")
        msg_parts.append(f"{ICONS['favor']} Favor → " + ", ".join(fav_txt))

    # log timeline
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['check']} Quest **{quest['title']}** selesai."))

    return "\n".join(msg_parts)


def fail_quest(guild_id, channel_id, title):
    """Tandai quest gagal."""
    update_status(guild_id, channel_id, title, "failed")
    execute("INSERT INTO timeline (guild_id, channel_id, event) VALUES (?,?,?)",
            (guild_id, channel_id, f"{ICONS['fail']} Quest **{title}** gagal."))
    return True


def get_detail(guild_id, channel_id, title):
    """Ambil detail quest untuk embed."""
    row = get_quest(guild_id, channel_id, title)
    if not row:
        return None
    rewards = json.loads(row["rewards"] or "{}")
    items_required = json.loads(row["items_required"] or "[]")
    assigned = json.loads(row.get("assigned_to") or "[]")
    return {
        "title": row["title"],
        "detail": row["detail"],
        "status": row["status"],
        "items_required": items_required,
        "rewards": rewards,
        "assigned_to": assigned,
        "created_by": row.get("created_by"),
    }
