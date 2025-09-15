# services/init_service.py
import json
import random
from typing import Dict, List, Tuple, Optional

from utils.db import execute, fetchone, fetchall

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
}

# ===============================
# DB bootstrap
# ===============================

def ensure_tables():
    execute("""
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        channel_id TEXT,
        order_json TEXT DEFAULT '[]',  -- list of [name, score]
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_initiative_gc
    ON initiative(guild_id, channel_id);
    """)

# ===============================
# Low-level helpers
# ===============================

def _sorted_order(arr: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    # Skor desc, nama asc
    return sorted(arr, key=lambda x: (-int(x[1]), x[0].lower()))

def _load(guild_id: str, channel_id: str) -> Dict:
    row = fetchone("SELECT * FROM initiative WHERE guild_id=? AND channel_id=?",
                   (guild_id, channel_id))
    if not row:
        return {"order": [], "ptr": 0, "round": 1}
    try:
        order = json.loads(row.get("order_json") or "[]")
    except Exception:
        order = []
    return {
        "order": [(n, int(s)) for (n, s) in order],
        "ptr": int(row.get("ptr") or 0),
        "round": int(row.get("round") or 1),
    }

def _save(guild_id: str, channel_id: str, state: Dict):
    order_json = json.dumps(state.get("order", []))
    ptr = int(state.get("ptr", 0))
    rnd = int(state.get("round", 1))
    execute("""
    INSERT INTO initiative (guild_id, channel_id, order_json, ptr, round)
    VALUES (?,?,?,?,?)
    ON CONFLICT(guild_id, channel_id)
    DO UPDATE SET order_json=excluded.order_json,
                  ptr=excluded.ptr,
                  round=excluded.round,
                  updated_at=CURRENT_TIMESTAMP;
    """, (guild_id, channel_id, order_json, ptr, rnd))

def _clear(guild_id: str, channel_id: str):
    execute("DELETE FROM initiative WHERE guild_id=? AND channel_id=?",
            (guild_id, channel_id))

# ===============================
# Public API
# ===============================

def get_state(guild_id: str, channel_id: str) -> Dict:
    """Ambil state initiative channel."""
    ensure_tables()
    return _load(guild_id, channel_id)

def set_state(guild_id: str, channel_id: str, state: Dict) -> Dict:
    """Timpa seluruh state initiative channel."""
    ensure_tables()
    _save(guild_id, channel_id, state)
    return state

def add_participant(guild_id: str, channel_id: str, name: str, score: int) -> Dict:
    """Tambah/overwrite 1 peserta."""
    s = get_state(guild_id, channel_id)
    mapping = {n: sc for (n, sc) in s["order"]}
    mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(guild_id, channel_id, s)
    return s

def add_many(guild_id: str, channel_id: str, pairs: List[Tuple[str, int]]) -> Dict:
    """
    Tambah banyak peserta.
    pairs: [(name, score), ...]
    """
    s = get_state(guild_id, channel_id)
    mapping = {n: sc for (n, sc) in s["order"]}
    for name, score in pairs:
        mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(guild_id, channel_id, s)
    return s

def remove_participant(guild_id: str, channel_id: str, name: str) -> Dict:
    s = get_state(guild_id, channel_id)
    before = len(s["order"])
    s["order"] = [(n, sc) for (n, sc) in s["order"] if n.lower() != name.lower()]
    if len(s["order"]) < before:
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        _save(guild_id, channel_id, s)
    return s

def clear(guild_id: str, channel_id: str) -> Dict:
    """Reset state initiative channel."""
    s = {"order": [], "ptr": 0, "round": 1}
    _save(guild_id, channel_id, s)
    return s

def next_turn(guild_id: str, channel_id: str) -> Dict:
    """
    Maju ke giliran berikutnya.
    Jika kembali ke indeks 0, round bertambah 1.
    """
    s = get_state(guild_id, channel_id)
    if not s["order"]:
        return s
    s["ptr"] = (s["ptr"] + 1) % len(s["order"])
    if s["ptr"] == 0:
        s["round"] += 1
    _save(guild_id, channel_id, s)
    return s

def set_pointer(guild_id: str, channel_id: str, index1: int) -> Dict:
    """Set pointer giliran (index mulai dari 1)."""
    s = get_state(guild_id, channel_id)
    if not s["order"]:
        return s
    idx0 = max(1, min(index1, len(s["order"]))) - 1
    s["ptr"] = idx0
    _save(guild_id, channel_id, s)
    return s

def set_round(guild_id: str, channel_id: str, value: int) -> Dict:
    """Set nilai round (min 1)."""
    s = get_state(guild_id, channel_id)
    s["round"] = max(1, int(value))
    _save(guild_id, channel_id, s)
    return s

def shuffle_first(guild_id: str, channel_id: str) -> Dict:
    """
    Acak siapa yang jalan dulu (hanya pointer).
    Tidak mengubah urutan initiative.
    """
    s = get_state(guild_id, channel_id)
    if not s["order"]:
        return s
    s["ptr"] = random.randint(0, len(s["order"]) - 1)
    _save(guild_id, channel_id, s)
    return s

# ===============================
# Convenience (string builders)
# ===============================

def format_order_lines(state: Dict, highlight: bool = True) -> str:
    """Bikin teks daftar order yang siap dikirim ke chat."""
    order = state.get("order", [])
    ptr = state.get("ptr", 0)
    if not order:
        return "(kosong)"

    lines = []
    for i, (name, score) in enumerate(order):
        marker = "👉" if (highlight and i == ptr) else "  "
        lines.append(f"{marker} {i+1}. **{name}** ({score})")
    return "\n".join(lines)

def current_actor(state: Dict) -> Optional[str]:
    order = state.get("order", [])
    ptr = state.get("ptr", 0)
    if not order:
        return None
    return order[ptr][0]
