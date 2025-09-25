# services/init_service.py
import json
import random
from typing import Dict, List, Tuple, Optional
import discord

from utils.db import execute, fetchone

ICONS = {
    "order": "⚔️",
    "next": "⏭️",
    "round": "📜",
    "first": "👉",
    "shuffle": "🎲",
    "clear": "🧹",
    "ok": "✅",
    "warn": "⚠️",
    "trash": "🗑️",
    "victory": "🎉",
    "turn": "🔥",
    "wait": "⏳",
}

# ===============================
# DB bootstrap
# ===============================
def ensure_table(guild_id: int):
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_json TEXT DEFAULT '[]',  -- list of [name, score]
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    row = fetchone(guild_id, "SELECT * FROM initiative LIMIT 1")
    if not row:
        execute(guild_id,
            "INSERT INTO initiative (order_json, ptr, round) VALUES ('[]', 0, 1)"
        )

# ===============================
# Low-level helpers
# ===============================
def _load(guild_id: int) -> Dict:
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT * FROM initiative LIMIT 1")
    try:
        order = json.loads(row.get("order_json") or "[]")
    except Exception:
        order = []
    return {
        "order": [(n, int(s)) for (n, s) in order],
        "ptr": int(row.get("ptr") or 0),
        "round": int(row.get("round") or 1),
    }

def _save(guild_id: int, state: Dict):
    order_json = json.dumps(state.get("order", []))
    ptr = int(state.get("ptr", 0))
    rnd = int(state.get("round", 1))
    execute(guild_id, """
    UPDATE initiative
    SET order_json=?, ptr=?, round=?, updated_at=CURRENT_TIMESTAMP
    WHERE id=(SELECT id FROM initiative LIMIT 1)
    """, (order_json, ptr, rnd))

def _sorted_order(arr: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    # Skor desc, nama asc
    return sorted(arr, key=lambda x: (-int(x[1]), x[0].lower()))

# ===============================
# Public API
# ===============================
def get_state(guild_id: int) -> Dict:
    return _load(guild_id)

def set_state(guild_id: int, state: Dict) -> Dict:
    _save(guild_id, state)
    return state

def add_participant(guild_id: int, name: str, score: int) -> Dict:
    s = get_state(guild_id)
    mapping = {n: sc for (n, sc) in s["order"]}
    mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(guild_id, s)
    return s

def add_many(guild_id: int, pairs: List[Tuple[str, int]]) -> Dict:
    s = get_state(guild_id)
    mapping = {n: sc for (n, sc) in s["order"]}
    for name, score in pairs:
        mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(guild_id, s)
    return s

def remove_participant(guild_id: int, name: str) -> Dict:
    s = get_state(guild_id)
    before = len(s["order"])
    s["order"] = [(n, sc) for (n, sc) in s["order"] if n.lower() != name.lower()]
    if len(s["order"]) < before:
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        _save(guild_id, s)
    return s

def clear(guild_id: int) -> Dict:
    s = {"order": [], "ptr": 0, "round": 1}
    _save(guild_id, s)
    return s

def next_turn(guild_id: int) -> Dict:
    s = get_state(guild_id)
    if not s["order"]:
        return s
    s["ptr"] = (s["ptr"] + 1) % len(s["order"])
    if s["ptr"] == 0:
        s["round"] += 1
    _save(guild_id, s)
    return s

def set_pointer(guild_id: int, index1: int) -> Dict:
    s = get_state(guild_id)
    if not s["order"]:
        return s
    idx0 = max(1, min(index1, len(s["order"]))) - 1
    s["ptr"] = idx0
    _save(guild_id, s)
    return s

def set_round(guild_id: int, value: int) -> Dict:
    s = get_state(guild_id)
    s["round"] = max(1, int(value))
    _save(guild_id, s)
    return s

def shuffle_first(guild_id: int) -> Dict:
    s = get_state(guild_id)
    if not s["order"]:
        return s
    s["ptr"] = random.randint(0, len(s["order"]) - 1)
    _save(guild_id, s)
    return s

# ===============================
# Convenience (Embed builder)
# ===============================
def make_embed(guild_id: int, title: str = "⚔️ Initiative Order", highlight: bool = True) -> discord.Embed:
    s = get_state(guild_id)
    order = s.get("order", [])
    ptr = s.get("ptr", 0)
    rnd = s.get("round", 1)

    embed = discord.Embed(
        title=title,
        description=f"{ICONS['round']} Round **{rnd}** • Total Peserta: **{len(order)}**",
        color=discord.Color.red()
    )

    if not order:
        embed.add_field(name="⚔️ Initiative Order", value="(kosong)", inline=False)
        embed.set_footer(text="Tambahkan peserta dengan !init add <Nama> <Skor>")
        return embed

    lines = []
    for i, (name, score) in enumerate(order):
        if highlight and i == ptr:
            lines.append(f"{ICONS['turn']} **{i+1}. {name}** ({score}) ← Giliran")
        else:
            lines.append(f"{ICONS['wait']} {i+1}. {name} ({score})")

    embed.add_field(name="⚔️ Initiative Order", value="\n".join(lines), inline=False)
    embed.set_footer(text="Gunakan !init next / !next untuk lanjut giliran.")
    return embed

def format_order_lines(state: Dict, highlight: bool = True) -> str:
    order = state.get("order", [])
    ptr = state.get("ptr", 0)
    if not order:
        return "(kosong)"
    lines = []
    for i, (name, score) in enumerate(order):
        marker = ICONS["first"] if (highlight and i == ptr) else ICONS["wait"]
        lines.append(f"{marker} {i+1}. **{name}** ({score})")
    return "\n".join(lines)

def current_actor(state: Dict) -> Optional[str]:
    order = state.get("order", [])
    ptr = state.get("ptr", 0)
    if not order:
        return None
    return order[ptr][0]
