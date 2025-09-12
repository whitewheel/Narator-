# memory.py
import os, sqlite3, json, copy

# Tulis ke Railway Volume (persisten)
DB_PATH = os.getenv("DB_PATH", "/data/memory.db")

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS memories(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id TEXT, channel_id TEXT, user_id TEXT,
          category TEXT, content TEXT, meta TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          archived INTEGER DEFAULT 0
        );
        """)

def save_memory(guild_id, channel_id, user_id, category, content, meta=None):
    with _conn() as c:
        c.execute(
            "INSERT INTO memories(guild_id,channel_id,user_id,category,content,meta) VALUES(?,?,?,?,?,?)",
            (str(guild_id), str(channel_id), str(user_id), category, content, json.dumps(meta or {}))
        )

def get_recent(guild_id, channel_id, category=None, limit=10):
    q = "SELECT id,category,content,meta,created_at FROM memories WHERE guild_id=? AND channel_id=? AND archived=0 "
    args = [str(guild_id), str(channel_id)]
    if category:
        q += "AND category=? "
        args.append(category)
    q += "ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with _conn() as c:
        return c.execute(q, args).fetchall()

def get_latest_summary(guild_id, channel_id):
    with _conn() as c:
        row = c.execute("""
            SELECT content FROM memories
            WHERE guild_id=? AND channel_id=? AND category='summary'
            ORDER BY id DESC LIMIT 1
        """, (str(guild_id), str(channel_id))).fetchone()
    return row[0] if row else None

def write_summary(guild_id, channel_id, text, meta=None):
    save_memory(guild_id, channel_id, "system", "summary", text, meta or {})

def mark_archived(guild_id, channel_id, ids):
    if not ids: return
    with _conn() as c:
        placeholders = ",".join("?"*len(ids))
        c.execute(
            f"UPDATE memories SET archived=1 WHERE guild_id=? AND channel_id=? AND id IN ({placeholders})",
            [str(guild_id), str(channel_id), *ids]
        )

def export_all_json(path="/data/memory_export.json"):
    with _conn() as c:
        rows = c.execute("SELECT * FROM memories ORDER BY id ASC").fetchall()
    cols = ["id","guild_id","channel_id","user_id","category","content","meta","created_at","archived"]
    data = [dict(zip(cols, r)) for r in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def count_rows(guild_id=None, channel_id=None):
    q = "SELECT COUNT(*) FROM memories WHERE 1=1"
    args = []
    if guild_id is not None:
        q += " AND guild_id=?"; args.append(str(guild_id))
    if channel_id is not None:
        q += " AND channel_id=?"; args.append(str(channel_id))
    with _conn() as c:
        return c.execute(q, args).fetchone()[0]

def wipe_channel(guild_id, channel_id):
    with _conn() as c:
        c.execute("DELETE FROM memories WHERE guild_id=? AND channel_id=?",
                  (str(guild_id), str(channel_id)))

def wipe_guild(guild_id):
    with _conn() as c:
        c.execute("DELETE FROM memories WHERE guild_id=?", (str(guild_id),))

# ==== Taksonomi kategori + ikon (tanpa seed row; dipakai saat render/prompt) ====
CATEGORY = {
  "history":   {"icon":"🗂️", "desc":"Catatan narasi & aksi"},
  "story":     {"icon":"📜", "desc":"Lore/storyline dunia"},
  "zone":      {"icon":"📍", "desc":"Lokasi/daerah"},
  "character": {"icon":"🧬", "desc":"Karakter pemain"},
  "npc":       {"icon":"👤", "desc":"Non-player character"},
  "enemy":     {"icon":"☠️", "desc":"Musuh/ancaman"},
  "item":      {"icon":"🧰", "desc":"Item/gear/loot"},
  "quest":     {"icon":"📜", "desc":"Quest log"},
  "battle":    {"icon":"⚔️", "desc":"State pertempuran"},
  "summary":   {"icon":"🧾", "desc":"Ringkasan sesi"}
}

TEMPLATE = {
  "character": {"name":"","class":"","race":"","hp":0,"stats":{},"tags":[]},
  "npc":       {"name":"","role":"","attitude":"neutral","notes":"","tags":[]},
  "enemy":     {"name":"","type":"","hp":0,"abilities":[],"tags":[]},
  "item":      {"name":"","type":"","rarity":"","effect":"","tags":[]},
  "quest":     {"title":"","objective":"","reward":"","deadline":None,"status":"pending","hidden":False},
  "zone":      {"name":"","desc":"","factions":[],"danger":""},
  "battle":    {"round":0,"turn":0,"participants":[]}  # participants: [{id,name,hp,team}]
}

def category_icon(cat:str)->str:
    return CATEGORY.get(cat,{}).get("icon","🟣")

def template_for(cat:str)->dict:
    return copy.deepcopy(TEMPLATE.get(cat,{}))

def peek_related(guild_id, channel_id, terms:list[str],
                 cats=("npc","quest","zone","story","item","character"), limit=5):
    """Cari fakta singkat dari memori berdasarkan terms (LIKE) untuk dipakai di prompt GM."""
    if not terms: return []
    terms = [t.strip() for t in terms if t and t.strip()]
    if not terms: return []
    facts = []
    with _conn() as c:
        for cat in cats:
            for term in terms:
                like = f"%{term}%"
                rows = c.execute(
                    "SELECT category, content FROM memories "
                    "WHERE guild_id=? AND channel_id=? AND category=? AND content LIKE ? "
                    "AND archived=0 ORDER BY id DESC LIMIT ?",
                    (str(guild_id), str(channel_id), cat, like, limit)
                ).fetchall()
                for (cc, content) in rows:
                    icon = category_icon(cc)
                    snippet = content.strip().replace("\n"," ")
                    if len(snippet) > 100: snippet = snippet[:100] + "…"
                    facts.append(f"{icon} {cc}: {snippet}")
    # dedupe
    out, seen = [], set()
    for f in facts:
        if f in seen: continue
        seen.add(f); out.append(f)
    return out[:10]
