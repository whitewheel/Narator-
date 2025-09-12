# memory.py
import os, sqlite3, json

DB_PATH = os.getenv("DB_PATH", "/data/memory.db")  # tulis ke Volume Railway

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
            SELECT content FROM memories WHERE guild_id=? AND channel_id=? AND category='summary'
            ORDER BY id DESC LIMIT 1
        """, (str(guild_id), str(channel_id))).fetchone()
    return row[0] if row else None

def write_summary(guild_id, channel_id, text, meta=None):
    save_memory(guild_id, channel_id, "system", "summary", text, meta or {})

def mark_archived(guild_id, channel_id, ids):
    if not ids: return
    with _conn() as c:
        placeholders = ",".join("?"*len(ids))
        c.execute(f"UPDATE memories SET archived=1 WHERE guild_id=? AND channel_id=? AND id IN ({placeholders})",
                  [str(guild_id), str(channel_id), *ids])

def export_all_json(path="/data/memory_export.json"):
    with _conn() as c:
        rows = c.execute("SELECT * FROM memories ORDER BY id ASC").fetchall()
    cols = ["id","guild_id","channel_id","user_id","category","content","meta","created_at","archived"]
    data = [dict(zip(cols, r)) for r in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
