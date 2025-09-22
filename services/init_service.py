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
def ensure_table():
    execute("""
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_json TEXT DEFAULT '[]',  -- list of [name, score]
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # pastikan selalu ada minimal 1 record
    row = fetchone("SELECT * FROM initiative LIMIT 1")
    if not row:
        execute("INSERT INTO initiative (order_json, ptr, round) VALUES ('[]', 0, 1)")

# ===============================
# Low-level helpers
# ===============================
def _load() -> Dict:
    ensure_table()
    row = fetchone("SELECT * FROM initiative LIMIT 1")
    try:
        order = json.loads(row.get("order_json") or "[]")
    except Exception:
        order = []
    return {
        "order": [(n, int(s)) for (n, s) in order],
        "ptr": int(row.get("ptr") or 0),
        "round": int(row.get("round") or 1),
    }

def _save(state: Dict):
    order_json = json.dumps(state.get("order", []))
    ptr = int(state.get("ptr", 0))
    rnd = int(state.get("round", 1))
    execute("""
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
def get_state() -> Dict:
    return _load()

def set_state(state: Dict) -> Dict:
    _save(state)
    return state

def add_participant(name: str, score: int) -> Dict:
    s = get_state()
    mapping = {n: sc for (n, sc) in s["order"]}
    mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(s)
    return s

def add_many(pairs: List[Tuple[str, int]]) -> Dict:
    s = get_state()
    mapping = {n: sc for (n, sc) in s["order"]}
    for name, score in pairs:
        mapping[name] = int(score)
    s["order"] = _sorted_order(list(mapping.items()))
    s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
    _save(s)
    return s

def remove_participant(name: str) -> Dict:
    s = get_state()
    before = len(s["order"])
    s["order"] = [(n, sc) for (n, sc) in s["order"] if n.lower() != name.lower()]
    if len(s["order"]) < before:
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        _save(s)
    return s

def clear() -> Dict:
    s = {"order": [], "ptr": 0, "round": 1}
    _save(s)
    return s

def next_turn() -> Dict:
    s = get_state()
    if not s["order"]:
        return s
    s["ptr"] = (s["ptr"] + 1) % len(s["order"])
    if s["ptr"] == 0:
        s["round"] += 1
    _save(s)
    return s

def set_pointer(index1: int) -> Dict:
    s = get_state()
    if not s["order"]:
        return s
    idx0 = max(1, min(index1, len(s["order"]))) - 1
    s["ptr"] = idx0
    _save(s)
    return s

def set_round(value: int) -> Dict:
    s = get_state()
    s["round"] = max(1, int(value))
    _save(s)
    return s

def shuffle_first() -> Dict:
    s = get_state()
    if not s["order"]:
        return s
    s["ptr"] = random.randint(0, len(s["order"]) - 1)
    _save(s)
    return s

# ===============================
# Convenience
# ===============================
def format_order_lines(state: Dict, highlight: bool = True) -> str:
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
