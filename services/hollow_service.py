# services/hollow_service.py
import json, random
from datetime import datetime
from utils.db import execute, fetchone, fetchall
import discord
import re

# ======================================================
# 📦 HELPERS
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
        "common": 0x7f8c8d,
        "uncommon": 0x3498db,
        "rare": 0x9b59b6,
        "epic": 0xe67e22,
        "legendary": 0xf1c40f,
        "mythic": 0xff0066,
    }.get(rarity, 0x95a5a6)

RARITY_ICON = {
    "common": "⚪",
    "uncommon": "🔵",
    "rare": "🟣",
    "epic": "🟠",
    "legendary": "🟡",
    "mythic": "❤️‍🔥",
}

# ======================================================
# TRAIT EFFECT LIBRARY
# ======================================================
TRAIT_EFFECTS = {
    "market": {"vendor_mod": +10},
    "chaotic": {"event_mod": +5},
    "quiet": {"visitor_mod": -15},
    "industrial": {"vendor_mod": +5},
    "haunted": {"event_mod": +8, "visitor_mod": +3},
}

def _apply_trait_effects(traits, base, category):
    total = base
    for t in traits:
        eff = TRAIT_EFFECTS.get(t.lower(), {})
        total += eff.get(f"{category}_mod", 0)
    return max(0, min(100, total))

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
        tags TEXT DEFAULT '[]',
        cooldown_until TIMESTAMP DEFAULT NULL,
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
        time TEXT DEFAULT 'day',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 50,
        desc TEXT DEFAULT '',
        origin TEXT DEFAULT '',
        hook TEXT DEFAULT ''
    );
    """)
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS hollow_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        rarity TEXT DEFAULT 'common',
        chance INTEGER DEFAULT 10,
        desc TEXT DEFAULT '',
        effect TEXT DEFAULT '',
        effect_formula TEXT DEFAULT ''
    );
    """)

def add_node(guild_id, name, zone, node_type):
    ensure_table(guild_id)
    if fetchone(guild_id, "SELECT * FROM hollow_nodes WHERE name=?", (name,)):
        return f"⚠️ Node `{name}` sudah ada."
    execute(guild_id,
        "INSERT INTO hollow_nodes (name, zone, type) VALUES (?, ?, ?)",
        (name, zone, node_type))
    return f"✅ Node `{name}` ditambahkan di zona `{zone}` (type `{node_type}`)."

def list_nodes(guild_id):
    ensure_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM hollow_nodes ORDER BY name")

def get_node(guild_id, name):
    ensure_table(guild_id)
    return fetchone(guild_id, "SELECT * FROM hollow_nodes WHERE LOWER(name)=?", (name.lower(),))

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
    execute(guild_id, f"UPDATE hollow_nodes SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE LOWER(name)=?", params)
    return f"📝 Node `{name}` diperbarui: {updates}"

def add_tag(guild_id, node_name, tag):
    node = get_node(guild_id, node_name)
    tags = _json_load(node.get("tags"), [])
    if tag not in tags:
        tags.append(tag)
    execute(guild_id, "UPDATE hollow_nodes SET tags=? WHERE name=?", (_json_dump(tags), node_name))
    return f"🏷️ Tag `{tag}` ditambahkan ke `{node_name}`."

def remove_tag(guild_id, node_name, tag):
    node = get_node(guild_id, node_name)
    tags = _json_load(node.get("tags"), [])
    if tag in tags:
        tags.remove(tag)
    execute(guild_id, "UPDATE hollow_nodes SET tags=? WHERE name=?", (_json_dump(tags), node_name))
    return f"🗑️ Tag `{tag}` dihapus dari `{node_name}`."

# ======================================================
# 🧍‍♂️ NPC MANAGEMENT
# ======================================================
def add_npc(guild_id, node_name, npc_name, chance=50, rarity="common"):
    node = get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    npcs = _json_load(node["npcs"], [])
    if npcs and isinstance(npcs[0], str):
        npcs = [{"name": n, "chance": 50, "rarity": "common"} for n in npcs]
    if any(n["name"].lower() == npc_name.lower() for n in npcs):
        return f"⚠️ Vendor `{npc_name}` sudah ada di `{node_name}`."
    npcs.append({"name": npc_name, "chance": int(chance), "rarity": rarity.lower()})
    execute(guild_id, "UPDATE hollow_nodes SET npcs=? WHERE name=?", (_json_dump(npcs), node_name))
    return f"✅ Vendor `{npc_name}` ditambahkan ke `{node_name}` (Chance {chance}%, Rarity {rarity})."

def list_npc(guild_id, node_name):
    node = get_node(guild_id, node_name)
    if not node: return []
    npcs = _json_load(node["npcs"], [])
    if npcs and isinstance(npcs[0], str):
        npcs = [{"name": n, "chance": 50, "rarity": "common"} for n in npcs]
    return npcs

# ======================================================
# 👁 VISITORS
# ======================================================
def add_visitor(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_visitors (name) VALUES (?)", (name,))
    return f"✅ Visitor `{name}` ditambahkan."

def edit_visitor(guild_id, name, entry):
    row = fetchone(guild_id, "SELECT * FROM hollow_visitors WHERE LOWER(name)=?", (name.lower(),))
    if not row:
        return f"❌ Visitor `{name}` tidak ditemukan."
    updates = {}
    for part in entry.split():
        if "=" in part:
            k, v = part.split("=", 1)
            updates[k.strip()] = v.strip()
    set_clause = ", ".join([f"{k}=?" for k in updates])
    params = list(updates.values()) + [name.lower()]
    execute(guild_id, f"UPDATE hollow_visitors SET {set_clause} WHERE LOWER(name)=?", params)
    return f"📝 Visitor `{name}` diperbarui: {updates}"

def list_visitors(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_visitors ORDER BY rarity DESC")

# ======================================================
# 🎯 EVENTS
# ======================================================
def add_event(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_events (name) VALUES (?)", (name,))
    return f"✅ Event `{name}` ditambahkan."

def edit_event(guild_id, name, entry):
    # Bersihkan kutipan dan lowercase untuk lookup
    clean_name = name.strip().strip('"').strip("'").lower()
    row = fetchone(guild_id, "SELECT * FROM hollow_events WHERE LOWER(name)=?", (clean_name,))
    if not row:
        return f"❌ Event `{name}` tidak ditemukan."

    # Pakai regex biar bisa parse kutipan: key=value atau key="multi word"
    pattern = re.findall(r'(\w+)=("[^"]+"|\'[^\']+\'|[^\s]+)', entry)
    updates = {k: v.strip('"').strip("'") for k, v in pattern}

    if not updates:
        return "⚠️ Tidak ada field valid untuk diupdate. Format: key=value."

    # Bangun query update
    set_clause = ", ".join([f"{k}=?" for k in updates])
    params = list(updates.values()) + [clean_name]
    execute(guild_id, f"UPDATE hollow_events SET {set_clause} WHERE LOWER(name)=?", params)

    # Feedback
    fields = ", ".join([f"`{k}` → `{v}`" for k, v in updates.items()])
    return f"📝 Event `{row['name']}` diperbarui: {fields}"

def trigger_event(guild_id, node_name, event_name):
    ev = fetchone(guild_id, "SELECT * FROM hollow_events WHERE LOWER(name)=?", (event_name.lower(),))
    if not ev:
        return f"❌ Event `{event_name}` tidak ditemukan."
    desc = ev.get("desc", "-")
    effect = ev.get("effect", "-")
    formula = ev.get("effect_formula", "")
    return f"🎯 Event `{event_name}` aktif di `{node_name}`!\n🧠 {desc}\n⚙️ Efek: {effect or formula or '-'}"

def list_events(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_events ORDER BY rarity DESC")

# ======================================================
# 🎲 ROLL SYSTEM
# ======================================================
def roll_daily(guild_id, node_name, full_cycle=False):
    node = get_node(guild_id, node_name)
    if not node:
        return discord.Embed(title="❌ Node tidak ditemukan.", color=0xe74c3c)

    traits = _json_load(node.get("traits"), [])

    all_npcs = list_npc(guild_id, node_name)
    vendors_today = [
        n["name"] for n in all_npcs
        if random.randint(1, 100) <= _apply_trait_effects(traits, int(n.get("chance", 50)), "vendor")
    ]

    all_visitors = list_visitors(guild_id)
    visitors_today = [
        v["name"] for v in all_visitors
        if random.randint(1, 100) <= _apply_trait_effects(traits, int(v["chance"]), "visitor")
    ]

    all_events = list_events(guild_id)
    event_today = {}
    if all_events:
        pool = [e for e in all_events if random.randint(1, 100) <= _apply_trait_effects(traits, int(e["chance"]), "event")]
        if pool:
            ev = random.choice(pool)
            event_today = {"name": ev["name"], "desc": ev["desc"], "rarity": ev["rarity"], "effect": ev["effect"]}

    execute(guild_id,
        "UPDATE hollow_nodes SET vendors_today=?, visitors_today=?, event_today=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (_json_dump(vendors_today), _json_dump(visitors_today), json.dumps(event_today), node_name))
    execute(guild_id,
        "INSERT INTO hollow_log (node, vendors, visitors, event, time) VALUES (?, ?, ?, ?, ?)",
        (node_name, _json_dump(vendors_today), _json_dump(visitors_today), event_today.get("name", "-"), "day"))

    rarity = event_today.get("rarity", "common")
    icon = RARITY_ICON.get(rarity, "⚪")
    color = _color_from_rarity(rarity)

    embed = discord.Embed(
        title=f"{icon} Hollow Roll — {node_name}",
        color=color,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="💰 Vendors", value=", ".join(vendors_today) or "-", inline=False)
    embed.add_field(name="👁 Visitors", value=", ".join(visitors_today) or "-", inline=False)
    embed.add_field(name="🎯 Event", value=f"**{event_today.get('name','-')}** — {event_today.get('desc','-')}" if event_today else "-", inline=False)
    embed.add_field(name="🕐 Time", value="day", inline=False)
    embed.set_footer(text="Technonesia Hollow System — Daily Roll")
    return embed

# ======================================================
# 📢 ANNOUNCE + ADMIN
# ======================================================
def make_announcement(guild_id, node_name):
    node = get_node(guild_id, node_name)
    if not node: return None
    vendors = _json_load(node["vendors_today"], [])
    visitors = _json_load(node["visitors_today"], [])
    event = _json_load(node["event_today"], {})
    color = _color_from_rarity(event.get("rarity", "common"))
    icon = RARITY_ICON.get(event.get("rarity", "common"), "⚪")

    embed = discord.Embed(
        title=f"{icon} The Hollow Shifts — {node_name}",
        color=color,
        timestamp=datetime.utcnow(),
    )
    desc = "⚡ Aktivitas pasar bawah tanah berubah.\n\n"
    if event:
        desc += f"🎯 **{event.get('name','-')}** — {event.get('desc','-')}\n\n"
    if visitors:
        desc += f"👁 Visitors: {', '.join(visitors)}\n"
    if vendors:
        desc += f"💰 Vendors aktif: {', '.join(vendors)}"
    embed.description = desc
    embed.set_footer(text="Technonesia Hollow Announcement")
    return embed

# ======================================================
# LOG / EXPORT / MAINTENANCE
# ======================================================
def get_logs(guild_id, node_name, n=5):
    return fetchall(guild_id, "SELECT * FROM hollow_log WHERE node=? ORDER BY id DESC LIMIT ?", (node_name, n))

def export_log(guild_id, node_name, n=20):
    return json.dumps(get_logs(guild_id, node_name, n), indent=2, ensure_ascii=False)

def clean_orphans(guild_id):
    execute(guild_id, "DELETE FROM hollow_log WHERE node NOT IN (SELECT name FROM hollow_nodes)")
    return "🧹 Orphan log dibersihkan."

# ======================================================
# EMBED BUILDERS
# ======================================================
def make_node_embed(node):
    vendors = _json_load(node.get("vendors_today"), [])
    visitors = _json_load(node.get("visitors_today"), [])
    event = _json_load(node.get("event_today"), {})
    traits = _json_load(node.get("traits"), [])
    types = _json_load(node.get("types"), [])
    tags = _json_load(node.get("tags"), [])
    npcs = _json_load(node.get("npcs"), [])

    embed = discord.Embed(
        title=f"🌀 {node['name']} — Hollow Node",
        color=discord.Color.teal(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="📍 Zone", value=node.get("zone", "-"), inline=True)
    embed.add_field(name="🏷 Type", value=node.get("type", "-"), inline=True)
    embed.add_field(name="💠 Traits", value="\n".join(traits) or "-", inline=False)
    embed.add_field(name="💎 Types", value=", ".join(types) or "-", inline=False)
    embed.add_field(name="🏷 Tags", value=", ".join(tags) or "-", inline=False)
    vendornames = [v["name"] if isinstance(v, dict) else v for v in npcs]
    embed.add_field(name="💰 Vendors Registered", value=", ".join(vendornames) or "-", inline=False)
    embed.add_field(name="👁 Visitors Active", value=", ".join(visitors) or "-", inline=False)
    if event:
        embed.add_field(name="🎯 Event", value=f"**{event.get('name','-')}** — {event.get('desc','-')}", inline=False)
    embed.add_field(name="🧩 NPC Total", value=str(len(npcs)), inline=False)
    embed.set_footer(text="Technonesia Hollow System — GM View")
    return embed

def make_visitor_list_embed(visitors):
    embed = discord.Embed(title="👁 Global Visitors", color=discord.Color.green())
    for v in visitors:
        embed.add_field(
            name=f"{v['name']} ({v['rarity'].capitalize()})",
            value=f"Chance: {v['chance']}% | {v.get('desc','-')}\n🌍 {v.get('origin','-')} | 🪤 Hook: {v.get('hook','-')}",
            inline=False,
        )
    embed.set_footer(text="Technonesia Hollow Visitors")
    return embed

def make_event_list_embed(events):
    embed = discord.Embed(title="🎯 Global Hollow Events", color=discord.Color.orange())
    for e in events:
        embed.add_field(
            name=f"{e['name']} ({e['rarity'].capitalize()})",
            value=f"Chance: {e['chance']}% | {e.get('desc','-')}\nEffect: {e.get('effect','-')} | Formula: {e.get('effect_formula','-')}",
            inline=False,
        )
    embed.set_footer(text="Technonesia Hollow Events")
    return embed
