import json
from utils.db import execute, fetchone, fetchall
from services import inventory_service, status_service
from cogs.world.timeline import log_event   # konsisten

ICONS = {
    "quest": "📜",
    "check": "✅",
    "fail": "❌",
    "loot": "🎁",
    "favor": "💠",
    "xp": "⭐",
}

# ---------- CRUD ----------
def add_quest(guild_id: int, title, detail="", items_required=None, rewards=None, created_by=None, hidden=False, user_id=0):
    """Tambah quest baru (per server)."""
    status = "hidden" if hidden else "open"
    execute(
        guild_id,
        "INSERT INTO quests (name, desc, status, assigned_to, rewards, favor, tags, archived) VALUES (?,?,?,?,?,?,?,?)",
        (
            title,
            detail,
            status,
            json.dumps([]),
            json.dumps(rewards or {}),
            json.dumps({}),
            json.dumps({}),
            0
        ),
    )
    log_event(
        guild_id,
        user_id,
        code=f"QUEST_ADD_{title.upper()}",
        title=f"{ICONS['quest']} Quest baru ditambahkan: {title}",
        details=detail,
        etype="quest_add",
        actors=[title],
        tags=["quest","add"]
    )
    return True

def get_quest(guild_id: int, title):
    """Ambil 1 quest berdasarkan nama."""
    return fetchone(guild_id, "SELECT * FROM quests WHERE name=?", (title,))

def list_quests(guild_id: int, status="all", include_archived=False):
    """Ambil semua quest per server, bisa filter status. Skip archived jika tidak diminta."""
    rows = fetchall(guild_id, "SELECT * FROM quests")
    if not rows:
        return f"{ICONS['quest']} Tidak ada quest."

    out = []
    for r in rows:
        if not include_archived and r.get("archived", 0) == 1:
            continue
        if status != "all" and r["status"].lower() != status.lower():
            continue
        icon = ICONS["check"] if r["status"] == "completed" else (
            ICONS["fail"] if r["status"] == "failed" else ICONS["quest"]
        )
        label = f"{icon} **{r['name']}** — {r['status']}"
        if r.get("archived", 0) == 1:
            label += " 📦"
        out.append(label)
    return "\n".join(out)

def update_status(guild_id: int, title, new_status, archive=False):
    """Update status quest (dan archive kalau perlu)."""
    if archive:
        execute(guild_id, "UPDATE quests SET status=?, archived=1, updated_at=CURRENT_TIMESTAMP WHERE name=?",
                (new_status, title))
    else:
        execute(guild_id, "UPDATE quests SET status=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
                (new_status, title))
    return True

def set_rewards(guild_id: int, title, rewards: dict):
    """Set rewards quest."""
    execute(guild_id, "UPDATE quests SET rewards=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
            (json.dumps(rewards), title))
    return True

def assign_characters(guild_id: int, title, chars: list):
    """Assign quest ke karakter tertentu."""
    execute(guild_id, "UPDATE quests SET assigned_to=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
            (json.dumps(chars), title))
    return True

# ---------- Penyelesaian Quest ----------
async def complete_quest(guild_id: int, title, targets: list = None, user_id=0):
    """Selesaikan quest, kasih reward ke target characters."""
    quest = get_quest(guild_id, title)
    if not quest:
        return f"{ICONS['fail']} Quest tidak ditemukan."

    if quest["status"] != "open":
        return f"{ICONS['fail']} Quest ini sudah {quest['status']}."

    rewards = json.loads(quest["rewards"] or "{}")
    assigned = json.loads(quest.get("assigned_to") or "[]")

    if not targets:
        targets = assigned or []

    update_status(guild_id, title, "completed", archive=True)

    msg_parts = [f"{ICONS['check']} Quest **{quest['name']}** selesai!"]

    # XP
    if "xp" in rewards and rewards["xp"] > 0:
        for ch in targets:
            old = fetchone(guild_id, "SELECT xp FROM characters WHERE name=?", (ch,))
            if old:
                new_val = old["xp"] + rewards["xp"]
                await status_service.set_status(guild_id, "char", ch, "xp", new_val)
        msg_parts.append(f"{ICONS['xp']} {rewards['xp']} XP")

    # Gold
    if "gold" in rewards and rewards["gold"] > 0:
        for ch in targets:
            old = fetchone(guild_id, "SELECT gold FROM characters WHERE name=?", (ch,))
            if old:
                new_val = old["gold"] + rewards["gold"]
                await status_service.set_status(guild_id, "char", ch, "gold", new_val)
        msg_parts.append(f"💰 {rewards['gold']} Gold")

    # Loot
    if "loot" in rewards:
        for item, qty in rewards["loot"].items():
            for ch in targets:
                await inventory_service.add_item(guild_id, ch, item, qty)
            msg_parts.append(f"{ICONS['loot']} {qty}x {item}")

    # Favor
    if "favor" in rewards:
        fav_txt = []
        for fac, val in rewards["favor"].items():
            fav_txt.append(f"{fac}: {val:+d}")
        msg_parts.append(f"{ICONS['favor']} Favor → " + ", ".join(fav_txt))

    log_event(
        guild_id,
        user_id,
        code=f"QUEST_COMPLETE_{title.upper()}",
        title=f"{ICONS['check']} Quest {title} selesai.",
        details=json.dumps(rewards),
        etype="quest_complete",
        actors=targets,
        tags=["quest","complete"]
    )
    
    return "\n".join(msg_parts)

def fail_quest(guild_id: int, title, user_id=0):
    """Tandai quest gagal."""
    update_status(guild_id, title, "failed", archive=True)
    log_event(
        guild_id,
        user_id,
        code=f"QUEST_FAIL_{title.upper()}",
        title=f"{ICONS['fail']} Quest {title} gagal.",
        details="",
        etype="quest_fail",
        actors=[title],
        tags=["quest","fail"]
    )
    return True

def archive_quest(guild_id: int, title):
    """Arsipkan quest manual."""
    execute(guild_id, "UPDATE quests SET archived=1, updated_at=CURRENT_TIMESTAMP WHERE name=?", (title,))
    return True

def get_detail(guild_id: int, title):
    """Ambil detail quest untuk embed."""
    row = get_quest(guild_id, title)
    if not row:
        return None
    rewards = json.loads(row["rewards"] or "{}")
    assigned = json.loads(row.get("assigned_to") or "[]")
    return {
        "name": row["name"],
        "detail": row.get("desc",""),
        "status": row["status"],
        "rewards": rewards,
        "assigned_to": assigned,
        "archived": row.get("archived", 0),
    }
