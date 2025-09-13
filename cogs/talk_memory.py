from typing import List, Tuple
from memory import save_memory, get_recent

def _pack_meta(key_name: str, key_value: str):
    return {key_name: key_value}

def append_chat(
    guild_id: str,
    channel_id: str,
    user_id: int,
    category: str,
    key_name: str,
    key_value: str,
    role: str,
    text: str
):
    """Simpan 1 baris chat ke memory.
    role: 'user' | 'npc' | 'enemy' | 'system'
    """
    content = f"{role.upper()}: {text}"
    save_memory(guild_id, channel_id, user_id, category, content, _pack_meta(key_name, key_value))

def load_chat_history(
    guild_id: str,
    channel_id: str,
    category: str,
    key_name: str,
    key_value: str,
    limit: int = 30
) -> List[Tuple[str, str]]:
    """Ambil riwayat chat (role, text) dari memory sesuai kategori & meta key.
    Return list (role, text) secara kronologis.
    """
    rows = get_recent(guild_id, channel_id, category, limit)
    out = []
    for (_id, cat, content, meta, ts) in rows:
        if cat != category:
            continue
        if (meta or {}).get(key_name, "").lower() != key_value.lower():
            continue
        # content format: "ROLE: text"
        if ":" in content:
            role, text = content.split(":", 1)
            out.append((role.strip().lower(), text.strip()))
        else:
            out.append(("system", content.strip()))
    # reverse supaya kronologis
    out.reverse()
    return out
