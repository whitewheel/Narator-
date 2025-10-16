# services/hollow_service.py
import json
import random
from datetime import datetime
from utils.db import execute, fetchone, fetchall

# ======================================================
# 📦 HELPER
# ======================================================
def _json_load(s, default):
    try:
        return json.loads(s) if s else default
    except Exception:
        return default

def _json_dump(v):
    try:
        return json.dumps(v)
    except Exception:
        return "[]"

def _color_from_rarity(rarity: str):
    rarity = rarity.lower()
    return {
        "common": 0x808080,
        "uncommon": 0x3498db,
        "rare": 0x9b59b6,
        "epic": 0xe67e22,
        "legendary": 0xf1c40f,
    }.get(rarity, 0x95a5a6)

# ======================================================
# 🧭 NODE CONTROL
# ======================================================
def ensure_table(guild_id: int):
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        zone TEXT,
        type TEXT,
        traits TEXT DEFAULT '[]',
        types TEXT DEFAULT '[]',
        npcs TEXT DEFAULT '[]',
        visitors TEXT DEFAULT '[]',
        events TEXT DEFAULT '[]',
        vendors_today TEXT DEFAULT '[]',
        event_today TEXT DEFAULT '{}',
        visitors_today TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node TEXT,
        vendors TEXT,
        visitors TEXT,
        event TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 50,
        desc TEXT DEFAULT ''
    );
    """)
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 10,
        desc TEXT DEFAULT '',
        effect TEXT DEFAULT ''
    );
    """)

def add_node(guild_id, name, zone, node_type):
    ensure_table(guild_id)
    row = fetchone(guild_id, "SELECT * FROM hollow_nodes WHERE name=?", (name,))
    if row:
        return f"⚠️ Node `{name}` sudah ada."
    execute(guild_id,
        "INSERT INTO hollow_nodes (name, zone, type) VALUES (?, ?, ?)",
        (name, zone, node_type)
    )
    return f"✅ Node `{name}` ditambahkan di zona `{zone}` dengan type `{node_type}`."

def list_nodes(guild_id):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM hollow_nodes ORDER BY name")

def get_node(guild_id, name):
    ensure_table(guild_id)
    return fetchone(guild_id, "SELECT * FROM hollow_nodes WHERE name=?", (name,))

def remove_node(guild_id, name):
    execute(guild_id, "DELETE FROM hollow_nodes WHERE name=?", (name,))
    return f"🗑️ Node `{name}` dihapus."

def edit_node(guild_id, name, entry):
    row = get_node(guild_id, name)
    if not row:
        return f"❌ Node `{name}` tidak ditemukan."
    updates = {}
    for part in entry.split():
        if "=" in part:
            k, v = part.split("=", 1)
            updates[k.strip()] = v.strip()
    if not updates:
        return "⚠️ Tidak ada perubahan."
    set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
    params = list(updates.values()) + [name]
    execute(guild_id, f"UPDATE hollow_nodes SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE name=?", params)
    return f"📝 Node `{name}` diperbarui: {updates}"

def clone_node(guild_id, src, target):
    n = get_node(guild_id, src)
    if not n:
        return f"❌ Sumber `{src}` tidak ditemukan."
    if get_node(guild_id, target):
        return f"⚠️ Target `{target}` sudah ada."
    execute(
        guild_id,
        "INSERT INTO hollow_nodes (name, zone, type, traits, types, npcs, visitors, events) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            target, n["zone"], n["type"], n["traits"], n["types"],
            n["npcs"], n["visitors"], n["events"]
        )
    )
    return f"✅ Node `{target}` berhasil di-clone dari `{src}`."

def reset_node(guild_id, node_name):
    execute(guild_id,
        "UPDATE hollow_nodes SET vendors_today='[]', event_today='{}', visitors_today='[]', updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (node_name,)
    )
    return f"♻️ Node `{node_name}` direset (kosongkan vendor, visitor, event hari ini)."

# ======================================================
# 🧍‍♂️ NPC MANAGEMENT
# ======================================================
def add_npc(guild_id, node_name, npc):
    node = get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    npcs = _json_load(node["npcs"], [])
    if npc in npcs:
        return f"⚠️ `{npc}` sudah ada di {node_name}."
    npcs.append(npc)
    execute(guild_id, "UPDATE hollow_nodes SET npcs=? WHERE name=?", (_json_dump(npcs), node_name))
    return f"✅ NPC `{npc}` ditambahkan ke `{node_name}`."

def remove_npc(guild_id, node_name, npc):
    node = get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    npcs = _json_load(node["npcs"], [])
    if npc not in npcs:
        return f"⚠️ `{npc}` tidak ada di {node_name}."
    npcs.remove(npc)
    execute(guild_id, "UPDATE hollow_nodes SET npcs=? WHERE name=?", (_json_dump(npcs), node_name))
    return f"🗑️ NPC `{npc}` dihapus dari `{node_name}`."

def list_npc(guild_id, node_name):
    node = get_node(guild_id, node_name)
    if not node:
        return []
    return _json_load(node["npcs"], [])

# ======================================================
# 👁 VISITOR MANAGEMENT
# ======================================================
def add_visitor(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_visitors (name) VALUES (?)", (name,))
    return f"✅ Visitor `{name}` ditambahkan."

def remove_visitor(guild_id, name):
    execute(guild_id, "DELETE FROM hollow_visitors WHERE name=?", (name,))
    return f"🗑️ Visitor `{name}` dihapus."

def edit_visitor(guild_id, name, entry):
    row = fetchone(guild_id, "SELECT * FROM hollow_visitors WHERE name=?", (name,))
    if not row:
        return f"❌ Visitor `{name}` tidak ditemukan."
    updates = {}
    for part in entry.split():
        if "=" in part:
            k, v = part.split("=", 1)
            updates[k.strip()] = v.strip()
    set_clause = ", ".join([f"{k}=?" for k in updates])
    params = list(updates.values()) + [name]
    execute(guild_id, f"UPDATE hollow_visitors SET {set_clause} WHERE name=?", params)
    return f"📝 Visitor `{name}` diperbarui: {updates}"

def list_visitors(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_visitors ORDER BY rarity DESC")

# ======================================================
# 🎯 EVENT MANAGEMENT
# ======================================================
def add_event(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_events (name) VALUES (?)", (name,))
    return f"✅ Event `{name}` ditambahkan."

def remove_event(guild_id, name):
    execute(guild_id, "DELETE FROM hollow_events WHERE name=?", (name,))
    return f"🗑️ Event `{name}` dihapus."

def edit_event(guild_id, name, entry):
    row = fetchone(guild_id, "SELECT * FROM hollow_events WHERE name=?", (name,))
    if not row:
        return f"❌ Event `{name}` tidak ditemukan."
    updates = {}
    for part in entry.split():
        if "=" in part:
            k, v = part.split("=", 1)
            updates[k.strip()] = v.strip()
    set_clause = ", ".join([f"{k}=?" for k in updates])
    params = list(updates.values()) + [name]
    execute(guild_id, f"UPDATE hollow_events SET {set_clause} WHERE name=?", params)
    return f"📝 Event `{name}` diperbarui: {updates}"

def list_events(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_events ORDER BY rarity DESC")

# ======================================================
# ⚙ TRAITS & TYPES
# ======================================================
def add_trait(guild_id, node_name, trait):
    node = get_node(guild_id, node_name)
    traits = _json_load(node["traits"], [])
    if trait not in traits:
        traits.append(trait)
    execute(guild_id, "UPDATE hollow_nodes SET traits=? WHERE name=?", (_json_dump(traits), node_name))
    return f"✅ Trait `{trait}` ditambahkan."

def remove_trait(guild_id, node_name, trait):
    node = get_node(guild_id, node_name)
    traits = _json_load(node["traits"], [])
    if trait in traits:
        traits.remove(trait)
    execute(guild_id, "UPDATE hollow_nodes SET traits=? WHERE name=?", (_json_dump(traits), node_name))
    return f"🗑️ Trait `{trait}` dihapus."

def list_traits(guild_id, node_name):
    node = get_node(guild_id, node_name)
    return _json_load(node["traits"], [])

def add_type(guild_id, node_name, t):
    node = get_node(guild_id, node_name)
    types = _json_load(node["types"], [])
    if t not in types:
        types.append(t)
    execute(guild_id, "UPDATE hollow_nodes SET types=? WHERE name=?", (_json_dump(types), node_name))
    return f"✅ Type `{t}` ditambahkan."

def remove_type(guild_id, node_name, t):
    node = get_node(guild_id, node_name)
    types = _json_load(node["types"], [])
    if t in types:
        types.remove(t)
    execute(guild_id, "UPDATE hollow_nodes SET types=? WHERE name=?", (_json_dump(types), node_name))
    return f"🗑️ Type `{t}` dihapus."

def list_types(guild_id, node_name):
    node = get_node(guild_id, node_name)
    return _json_load(node["types"], [])

# ======================================================
# 🎲 ROLL SYSTEM
# ======================================================
def roll_daily(guild_id, node_name):
    node = get_node(guild_id, node_name)
    if not node:
        return discord.Embed(title="❌ Node tidak ditemukan.", color=0xe74c3c)

    # Vendors (random subset)
    npcs = _json_load(node["npcs"], [])
    vendors_today = random.sample(npcs, k=min(len(npcs), random.randint(1, max(1, len(npcs)//2 or 1)))) if npcs else []

    # Visitors (based on chance)
    all_visitors = list_visitors(guild_id)
    visitors_today = []
    for v in all_visitors:
        if random.randint(1, 100) <= int(v["chance"]):
            visitors_today.append(v["name"])

    # Event
    all_events = list_events(guild_id)
    event_today = {}
    if all_events:
        pool = [e for e in all_events if random.randint(1, 100) <= int(e["chance"])]
        if pool:
            ev = random.choice(pool)
            event_today = {"name": ev["name"], "desc": ev["desc"], "rarity": ev["rarity"], "effect": ev["effect"]}

    # Update DB
    execute(
        guild_id,
        "UPDATE hollow_nodes SET vendors_today=?, visitors_today=?, event_today=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (_json_dump(vendors_today), _json_dump(visitors_today), json.dumps(event_today), node_name)
    )
    execute(
        guild_id,
        "INSERT INTO hollow_log (node, vendors, visitors, event) VALUES (?, ?, ?, ?)",
        (node_name, _json_dump(vendors_today), _json_dump(visitors_today), event_today.get("name", "-"))
    )

    # Build Embed
    color = _color_from_rarity(event_today.get("rarity", "common"))
    embed = discord.Embed(
        title=f"🎲 Hollow Roll — {node_name}",
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="💰 Vendors", value=", ".join(vendors_today) if vendors_today else "-", inline=False)
    embed.add_field(name="👁 Visitors", value=", ".join(visitors_today) if visitors_today else "-", inline=False)
    if event_today:
        embed.add_field(name="🎯 Event", value=f"**{event_today['name']}** — {event_today.get('desc','-')}", inline=False)
    else:
        embed.add_field(name="🎯 Event", value="-", inline=False)
    embed.set_footer(text="Technonesia Hollow System — Daily Roll")
    return embed

def make_announcement(guild_id, node_name):
    node = get_node(guild_id, node_name)
    if not node:
        return None
    vendors = _json_load(node["vendors_today"], [])
    visitors = _json_load(node["visitors_today"], [])
    event = _json_load(node["event_today"], {})
    color = _color_from_rarity(event.get("rarity", "common"))
    embed = discord.Embed(
        title=f"📢 The Hollow Shifts — {node_name}",
        color=color,
        timestamp=datetime.utcnow()
    )
    text = "⚡ Aktivitas meningkat di pasar bawah tanah.\n\n"
    if event:
        text += f"🎯 **{event['name']}** — {event.get('desc','-')}\n\n"
    if visitors:
        text += f"👁 **Visitors:** {', '.join(visitors)}\n"
    if vendors:
        text += f"💰 **Vendors aktif:** {', '.join(vendors)}"
    embed.description = text
    embed.set_footer(text="Technonesia Hollow Announcement")
    return embed

def sync_all(guild_id):
    rows = list_nodes(guild_id)
    embeds = []
    for r in rows:
        embeds.append(roll_daily(guild_id, r["name"]))
    return embeds

# ======================================================
# 📜 LOG
# ======================================================
def get_logs(guild_id, node_name, n=5):
    return fetchall(guild_id, "SELECT * FROM hollow_log WHERE node=? ORDER BY id DESC LIMIT ?", (node_name, n))

# ======================================================
# 🧾 EMBED BUILDERS
# ======================================================
import discord

def make_node_embed(node):
    vendors = _json_load(node["vendors_today"], [])
    visitors = _json_load(node["visitors_today"], [])
    event = _json_load(node["event_today"], {})
    traits = _json_load(node["traits"], [])
    types = _json_load(node["types"], [])
    npcs = _json_load(node["npcs"], [])

    embed = discord.Embed(
        title=f"🌀 {node['name']} — Hollow Node",
        color=discord.Color.teal(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="📍 Zone", value=node.get("zone","-"), inline=True)
    embed.add_field(name="🏷 Type", value=node.get("type","-"), inline=True)
    embed.add_field(name="💠 Traits", value="\n".join(traits) if traits else "-", inline=False)
    embed.add_field(name="💎 Types", value=", ".join(types) if types else "-", inline=False)
    embed.add_field(name="💰 Vendors", value=", ".join(vendors) if vendors else "-", inline=False)
    embed.add_field(name="👁 Visitors", value=", ".join(visitors) if visitors else "-", inline=False)
    if event:
        embed.add_field(name="🎯 Event", value=f"**{event['name']}** — {event.get('desc','-')}", inline=False)
    embed.add_field(name="📚 NPC Total", value=str(len(npcs)), inline=True)
    embed.set_footer(text="Technonesia Hollow System — GM View")
    return embed

def make_visitor_list_embed(visitors):
    embed = discord.Embed(title="👁 Global Visitors", color=discord.Color.green())
    for v in visitors:
        embed.add_field(
            name=f"{v['name']} ({v['rarity'].capitalize()})",
            value=f"Chance: {v['chance']}% | {v.get('desc','-')}",
            inline=False
        )
    embed.set_footer(text="Technonesia Hollow Visitors")
    return embed

def make_event_list_embed(events):
    embed = discord.Embed(title="🎯 Global Hollow Events", color=discord.Color.orange())
    for e in events:
        embed.add_field(
            name=f"{e['name']} ({e['rarity'].capitalize()})",
            value=f"Chance: {e['chance']}% | {e.get('desc','-')}\nEffect: {e.get('effect','-')}",
            inline=False
        )
    embed.set_footer(text="Technonesia Hollow Events")
    return embed
