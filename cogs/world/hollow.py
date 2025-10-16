# cogs/world/hollow.py
import json
import random
import re
from datetime import datetime

import discord
from discord.ext import commands

from utils.db import execute, fetchone, fetchall

# ======================================================
# 📦 HELPERS (JSON, Warna, Ikon, Trait Effects)
# ======================================================
def _json_load(s, default):
    try:
        return json.loads(s) if s else default
    except Exception:
        return default

def _json_dump(v):
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return "[]"

def _color_from_rarity(rarity: str):
    rarity = (rarity or "").lower()
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
# 🗄️ DB ENSURE (tabel & index Hollow saja)
# ======================================================
def _ensure_tables(guild_id: int):
    # Nodes
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

    # Log
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

    # Visitor Library
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

    # Event Library
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

    # Indexes
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_nodes_name ON hollow_nodes(name);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_hollow_log_node ON hollow_log(node);")
    execute(guild_id, "CREATE INDEX IF NOT EXISTS idx_hollow_log_time ON hollow_log(time);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_visitors_name ON hollow_visitors(name);")
    execute(guild_id, "CREATE UNIQUE INDEX IF NOT EXISTS idx_hollow_events_name ON hollow_events(name);")

# ======================================================
# 🔧 HOLLOW CORE (CRUD & Operasi)
# ======================================================
def _get_node(guild_id, name):
    _ensure_tables(guild_id)
    return fetchone(guild_id, "SELECT * FROM hollow_nodes WHERE LOWER(name)=?", (name.lower(),))

def _list_nodes(guild_id):
    _ensure_tables(guild_id)
    return fetchall(guild_id, "SELECT * FROM hollow_nodes ORDER BY name")

def _add_node(guild_id, name, zone, node_type):
    _ensure_tables(guild_id)
    if _get_node(guild_id, name):
        return f"⚠️ Node `{name}` sudah ada."
    execute(guild_id,
            "INSERT INTO hollow_nodes (name, zone, type) VALUES (?, ?, ?)",
            (name, zone, node_type))
    return f"✅ Node `{name}` ditambahkan di zona `{zone}` (type `{node_type}`)."

def _edit_node(guild_id, name, entry):
    row = _get_node(guild_id, name)
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
    params = list(updates.values()) + [name.lower()]
    execute(guild_id, f"UPDATE hollow_nodes SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE LOWER(name)=?", params)
    return f"📝 Node `{name}` diperbarui: {updates}"

def _remove_node(guild_id, node_name):
    if not _get_node(guild_id, node_name):
        return f"❌ Node `{node_name}` tidak ditemukan."
    execute(guild_id, "DELETE FROM hollow_nodes WHERE LOWER(name)=?", (node_name.lower(),))
    return f"🗑️ Node `{node_name}` dihapus."

def _clone_node(guild_id, source, target):
    node = _get_node(guild_id, source)
    if not node:
        return f"❌ Node sumber `{source}` tidak ditemukan."
    if _get_node(guild_id, target):
        return f"⚠️ Node target `{target}` sudah ada."
    execute(
        guild_id,
        """INSERT INTO hollow_nodes
           (name, zone, type, traits, types, npcs, visitors, events, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            target,
            node.get("zone"),
            node.get("type"),
            node.get("traits") or "[]",
            node.get("types") or "[]",
            node.get("npcs") or "[]",
            node.get("visitors") or "[]",
            node.get("events") or "[]",
            node.get("tags") or "[]",
        )
    )
    return f"✅ Node `{target}` berhasil diklon dari `{source}`."

def _reset_node(guild_id, node_name):
    if not _get_node(guild_id, node_name):
        return f"❌ Node `{node_name}` tidak ditemukan."
    execute(
        guild_id,
        "UPDATE hollow_nodes SET vendors_today='[]', visitors_today='[]', event_today='{}', updated_at=CURRENT_TIMESTAMP WHERE LOWER(name)=?",
        (node_name.lower(),)
    )
    return f"♻️ Node `{node_name}` di-reset."

def _get_logs(guild_id, node_name, n=5):
    return fetchall(guild_id, "SELECT * FROM hollow_log WHERE node=? ORDER BY id DESC LIMIT ?", (node_name, n))

def _export_log(guild_id, node_name, n=20):
    return json.dumps(_get_logs(guild_id, node_name, n), indent=2, ensure_ascii=False)

def _clean_orphans(guild_id):
    execute(guild_id, "DELETE FROM hollow_log WHERE node NOT IN (SELECT name FROM hollow_nodes)")
    return "🧹 Orphan log dibersihkan."

# ---------- Vendors (NPC di node) ----------
def _list_npc(guild_id, node_name):
    node = _get_node(guild_id, node_name)
    if not node:
        return []
    npcs = _json_load(node.get("npcs"), [])
    if npcs and isinstance(npcs[0], str):
        npcs = [{"name": n, "chance": 50, "rarity": "common"} for n in npcs]
    return npcs

def _add_npc(guild_id, node_name, npc_name, chance=50, rarity="common"):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    npcs = _json_load(node.get("npcs"), [])
    # kompatibilitas format lama
    if npcs and isinstance(npcs[0], str):
        npcs = [{"name": n, "chance": 50, "rarity": "common"} for n in npcs]
    if any(n.get("name", "").lower() == npc_name.lower() for n in npcs):
        return f"⚠️ Vendor `{npc_name}` sudah ada di `{node_name}`."
    npcs.append({"name": npc_name, "chance": int(chance), "rarity": str(rarity).lower()})
    execute(guild_id, "UPDATE hollow_nodes SET npcs=? WHERE name=?", (_json_dump(npcs), node_name))
    return f"✅ Vendor `{npc_name}` ditambahkan ke `{node_name}` (Chance {chance}%, Rarity {rarity})."

def _remove_npc(guild_id, node_name, npc_name):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    npcs = _json_load(node.get("npcs"), [])
    # normalisasi
    norm = []
    for n in npcs:
        if isinstance(n, str):
            if n.lower() != npc_name.lower():
                norm.append(n)
        else:
            if n.get("name", "").lower() != npc_name.lower():
                norm.append(n)
    execute(guild_id, "UPDATE hollow_nodes SET npcs=? WHERE name=?", (_json_dump(norm), node_name))
    return f"🗑️ Vendor `{npc_name}` dihapus dari `{node_name}`."

# ---------- Visitors (global) ----------
def _add_visitor(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_visitors (name) VALUES (?)", (name,))
    return f"✅ Visitor `{name}` ditambahkan."

def _remove_visitor(guild_id, name):
    execute(guild_id, "DELETE FROM hollow_visitors WHERE LOWER(name)=?", (name.lower(),))
    return f"🗑️ Visitor `{name}` dihapus."

def _edit_visitor(guild_id, name, entry):
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

def _list_visitors(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_visitors ORDER BY rarity DESC, chance DESC, name ASC")

# ---------- Events (global) ----------
def _add_event(guild_id, name):
    execute(guild_id, "INSERT OR IGNORE INTO hollow_events (name) VALUES (?)", (name,))
    return f"✅ Event `{name}` ditambahkan."

def _remove_event(guild_id, name):
    execute(guild_id, "DELETE FROM hollow_events WHERE LOWER(name)=?", (name.lower(),))
    return f"🗑️ Event `{name}` dihapus."

def _edit_event(guild_id, name, entry):
    clean_name = name.strip().strip('"').strip("'").lower()
    row = fetchone(guild_id, "SELECT * FROM hollow_events WHERE LOWER(name)=?", (clean_name,))
    if not row:
        return f"❌ Event `{name}` tidak ditemukan."
    # parse key="multi word" atau key=word
    pattern = re.findall(r'(\w+)=("[^"]+"|\'[^\']+\'|[^\s]+)', entry)
    updates = {k: v.strip('"').strip("'") for k, v in pattern}
    if not updates:
        return "⚠️ Tidak ada field valid untuk diupdate. Format: key=value."
    set_clause = ", ".join([f"{k}=?" for k in updates])
    params = list(updates.values()) + [clean_name]
    execute(guild_id, f"UPDATE hollow_events SET {set_clause} WHERE LOWER(name)=?", params)
    fields = ", ".join([f"`{k}` → `{v}`" for k, v in updates.items()])
    return f"📝 Event `{row['name']}` diperbarui: {fields}"

def _list_events(guild_id):
    return fetchall(guild_id, "SELECT * FROM hollow_events ORDER BY rarity DESC, chance DESC, name ASC")

def _assign_event(guild_id, event_name, node_name):
    ev = fetchone(guild_id, "SELECT * FROM hollow_events WHERE LOWER(name)=?", (event_name.lower(),))
    if not ev:
        return f"❌ Event `{event_name}` tidak ditemukan."
    execute(guild_id, "UPDATE hollow_nodes SET event_today=? WHERE LOWER(name)=?",
            (json.dumps(ev, ensure_ascii=False), node_name.lower()))
    return f"🎯 Event `{event_name}` kini aktif di `{node_name}`."

def _clear_event(guild_id, node_name):
    execute(guild_id, "UPDATE hollow_nodes SET event_today='{}' WHERE LOWER(name)=?", (node_name.lower(),))
    return f"🧹 Event pada node `{node_name}` telah dihapus."

def _trigger_event_text(guild_id, node_name, event_name):
    ev = fetchone(guild_id, "SELECT * FROM hollow_events WHERE LOWER(name)=?", (event_name.lower(),))
    if not ev:
        return f"❌ Event `{event_name}` tidak ditemukan."
    desc = ev.get("desc", "-")
    effect = ev.get("effect", "-")
    formula = ev.get("effect_formula", "")
    return f"🎯 Event `{event_name}` aktif di `{node_name}`!\n🧠 {desc}\n⚙️ Efek: {effect or formula or '-'}"

# ---------- Traits & Types ----------
def _add_trait(guild_id, node_name, trait):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    traits = _json_load(node.get("traits"), [])
    if trait not in traits:
        traits.append(trait)
    execute(guild_id, "UPDATE hollow_nodes SET traits=? WHERE name=?", (_json_dump(traits), node_name))
    return f"💠 Trait `{trait}` ditambahkan ke `{node_name}`."

def _remove_trait(guild_id, node_name, trait):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    traits = _json_load(node.get("traits"), [])
    if trait in traits:
        traits.remove(trait)
    execute(guild_id, "UPDATE hollow_nodes SET traits=? WHERE name=?", (_json_dump(traits), node_name))
    return f"🗑️ Trait `{trait}` dihapus dari `{node_name}`."

def _list_traits(guild_id, node_name):
    node = _get_node(guild_id, node_name)
    if not node:
        return []
    return _json_load(node.get("traits"), [])

def _add_type(guild_id, node_name, t):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    types = _json_load(node.get("types"), [])
    if t not in types:
        types.append(t)
    execute(guild_id, "UPDATE hollow_nodes SET types=? WHERE name=?", (_json_dump(types), node_name))
    return f"💠 Type `{t}` ditambahkan ke `{node_name}`."

def _remove_type(guild_id, node_name, t):
    node = _get_node(guild_id, node_name)
    if not node:
        return "❌ Node tidak ditemukan."
    types = _json_load(node.get("types"), [])
    if t in types:
        types.remove(t)
    execute(guild_id, "UPDATE hollow_nodes SET types=? WHERE name=?", (_json_dump(types), node_name))
    return f"🗑️ Type `{t}` dihapus dari `{node_name}`."

def _list_types(guild_id, node_name):
    node = _get_node(guild_id, node_name)
    if not node:
        return []
    return _json_load(node.get("types"), [])

# ======================================================
# 🎲 ROLL SYSTEM & ANNOUNCE
# ======================================================
def _roll_daily(guild_id, node_name, time_label="day"):
    node = _get_node(guild_id, node_name)
    if not node:
        embed = discord.Embed(title="❌ Node tidak ditemukan.", color=0xe74c3c)
        return embed

    traits = _json_load(node.get("traits"), [])
    # Vendors
    all_npcs = _list_npc(guild_id, node_name)
    vendors_today = [
        n["name"] for n in all_npcs
        if random.randint(1, 100) <= int(n.get("chance", 50))
    ]

    # Visitors
    all_visitors = _list_visitors(guild_id)
    visitors_today = [
        v["name"] for v in all_visitors
        if random.randint(1, 100) <= int(n.get("chance", 50))
    ]

    # Events
    all_events = _list_events(guild_id)
    event_today = {}
    if all_events:
        pool = [
            e for e in all_events
            if random.randint(1, 100) <= int(n.get("chance", 50))
        ]
        if pool:
            ev = random.choice(pool)
            event_today = {
                "name": ev.get("name"),
                "desc": ev.get("desc"),
                "rarity": ev.get("rarity", "common"),
                "effect": ev.get("effect")
            }

    # Simpan hasil ke node + log
    execute(
        guild_id,
        "UPDATE hollow_nodes SET vendors_today=?, visitors_today=?, event_today=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (_json_dump(vendors_today), _json_dump(visitors_today), json.dumps(event_today, ensure_ascii=False), node_name)
    )
    execute(
        guild_id,
        "INSERT INTO hollow_log (node, vendors, visitors, event, time) VALUES (?, ?, ?, ?, ?)",
        (node_name, _json_dump(vendors_today), _json_dump(visitors_today), event_today.get("name", "-"), time_label)
    )

    rarity = event_today.get("rarity", "common")
    icon = RARITY_ICON.get((rarity or "").lower(), "⚪")
    color = _color_from_rarity(rarity)

    embed = discord.Embed(
        title=f"{icon} Hollow Roll — {node_name}",
        color=color,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="💰 Vendors", value=", ".join(vendors_today) or "-", inline=False)
    embed.add_field(name="👁 Visitors", value=", ".join(visitors_today) or "-", inline=False)
    embed.add_field(
        name="🎯 Event",
        value=(f"**{event_today.get('name','-')}** — {event_today.get('desc','-')}" if event_today else "-"),
        inline=False
    )
    embed.add_field(name="🕐 Time", value=time_label, inline=False)
    embed.set_footer(text="Technonesia Hollow System — Daily Roll")
    return embed

def _roll_slot(guild_id, node_name, slot):
    slot = (slot or "day").lower()
    if slot not in {"morning", "evening", "night", "day"}:
        slot = "day"
    return _roll_daily(guild_id, node_name, time_label=slot)

def _sync_all(guild_id):
    embeds = []
    for n in _list_nodes(guild_id):
        embeds.append(_roll_daily(guild_id, n["name"], time_label="day"))
    return embeds

def _make_announcement(guild_id, node_name):
    node = _get_node(guild_id, node_name)
    if not node:
        return None
    vendors = _json_load(node.get("vendors_today"), [])
    visitors = _json_load(node.get("visitors_today"), [])
    event = _json_load(node.get("event_today"), {})
    color = _color_from_rarity(event.get("rarity", "common"))
    icon = RARITY_ICON.get((event.get("rarity", "common") or "common").lower(), "⚪")

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

# ---------- EMBED LIST BUILDERS ----------
def _make_node_embed(node):
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

def _make_visitor_list_embed(visitors):
    embed = discord.Embed(title="👁 Global Visitors", color=discord.Color.green())
    for v in visitors:
        embed.add_field(
            name=f"{v['name']} ({str(v.get('rarity','common')).capitalize()})",
            value=f"Chance: {v.get('chance',50)}% | {v.get('desc','-')}\n🌍 {v.get('origin','-')} | 🪤 Hook: {v.get('hook','-')}",
            inline=False,
        )
    embed.set_footer(text="Technonesia Hollow Visitors")
    return embed

def _make_event_list_embed(events):
    embed = discord.Embed(title="🎯 Global Hollow Events", color=discord.Color.orange())
    for e in events:
        embed.add_field(
            name=f"{e['name']} ({str(e.get('rarity','common')).capitalize()})",
            value=f"Chance: {e.get('chance',10)}% | {e.get('desc','-')}\nEffect: {e.get('effect','-')} | Formula: {e.get('effect_formula','-')}",
            inline=False,
        )
    embed.set_footer(text="Technonesia Hollow Events")
    return embed

# ======================================================
# 🧭 COG
# ======================================================
class Hollow(commands.Cog):
    """🌀 Technonesia Hollow System — Node, Vendor, Visitor, Event & Daily Cycle (All-in-One)"""

    def __init__(self, bot):
        self.bot = bot
        # 🔧 Auto-ensure Hollow tables for every guild on load
        for guild in bot.guilds:
            try:
                _ensure_tables(guild.id)
                print(f"[HOLLOW INIT] ✅ Tables ensured for guild {guild.id}")
            except Exception as e:
                print(f"[HOLLOW INIT] ⚠️ Failed ensure for {guild.id}: {e}")

    # ---------------- Base Help ----------------
    @commands.group(name="hollow", invoke_without_command=True)
    async def hollow(self, ctx):
        """Daftar perintah Hollow (GM Only)"""
        embed = discord.Embed(
            title="🌀 Technonesia Hollow System (GM)",
            color=discord.Color.teal(),
            description=(
                "⚙️ **Node Control**\n"
                "`!hollow addnode <nama> <zona> [type]`\n"
                "`!hollow list`, `!hollow info <node>`, `!hollow edit <node> field=value`,\n"
                "`!hollow clone <src> <target>`, `!hollow remove <node>`, `!hollow reset <node>`\n\n"
                "🎲 **Daily Cycle**\n"
                "`!hollow roll <node>` | `!hollow daily_roll <node>` | `!hollow announce <node>` | `!hollow sync`\n"
                "`!hollow slot_roll <node> <morning/evening/night>`\n\n"
                "🧍‍♂️ **Vendor Control**\n"
                "`!hollow addnpc <nama> <node> [chance] [rarity]`\n"
                "`!hollow removenpc <nama> <node>` | `!hollow listnpc <node>`\n\n"
                "👁 **Visitors**\n"
                "`!hollow addvisitor <nama>` | `!hollow removevisitor <nama>` | `!hollow editvisitor <nama> field=value`\n"
                "`!hollow listvisitor`\n\n"
                "🎯 **Events**\n"
                "`!hollow addevent <nama>` | `!hollow removeevent <nama>` | `!hollow editevent <nama> field=value`\n"
                "`!hollow listevent` | `!hollow assign <event> <node>` | `!hollow clearevent <node>`\n\n"
                "🧩 **Traits & Types**\n"
                "`!hollow trait add/remove <node> <trait>` | `!hollow type add/remove <node> <type>`"
            )
        )
        embed.set_footer(text="Technonesia 2145 • Hollow Command Index")
        await ctx.send(embed=embed)

    # ---------------- Node Control ----------------
    @hollow.command(name="addnode")
    @commands.has_permissions(administrator=True)
    async def addnode(self, ctx, name: str, zone: str, node_type: str = "market"):
        msg = _add_node(ctx.guild.id, name, zone, node_type)
        await ctx.send(msg)

    @hollow.command(name="list")
    async def list_nodes(self, ctx):
        rows = _list_nodes(ctx.guild.id)
        if not rows:
            return await ctx.send("📭 Belum ada node Hollow terdaftar.")
        embed = discord.Embed(title="📍 Hollow Network Map", color=discord.Color.blue())
        for r in rows:
            npcs = len(_json_load(r.get("npcs"), []))
            visitors = len(_json_load(r.get("visitors"), []))
            events = len(_json_load(r.get("events"), []))
            embed.add_field(
                name=f"{r['name']} ({r.get('zone','-')})",
                value=(f"🏷 Type: `{r.get('type','-')}`\n"
                       f"💰 NPC: {npcs} | 👁 Visitors: {visitors} | 🎯 Events: {events}"),
                inline=False
            )
        embed.set_footer(text="Technonesia Hollow Nodes Overview")
        await ctx.send(embed=embed)

    @hollow.command(name="info")
    async def node_info(self, ctx, node_name: str):
        node = _get_node(ctx.guild.id, node_name)
        if not node:
            return await ctx.send("❌ Node tidak ditemukan.")
        embed = _make_node_embed(node)
        await ctx.send(embed=embed)

    @hollow.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def edit_node(self, ctx, node_name: str, *, entry: str):
        msg = _edit_node(ctx.guild.id, node_name, entry)
        await ctx.send(msg)

    @hollow.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_node(self, ctx, *, node_name: str):
        msg = _remove_node(ctx.guild.id, node_name)
        await ctx.send(msg)

    @hollow.command(name="clone")
    @commands.has_permissions(administrator=True)
    async def clone_node(self, ctx, source: str, target: str):
        msg = _clone_node(ctx.guild.id, source, target)
        await ctx.send(msg)

    @hollow.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_node(self, ctx, *, node_name: str):
        msg = _reset_node(ctx.guild.id, node_name)
        await ctx.send(msg)

    @hollow.command(name="log")
    async def show_log(self, ctx, node_name: str, n: int = 5):
        logs = _get_logs(ctx.guild.id, node_name, n)
        if not logs:
            return await ctx.send("📭 Belum ada histori untuk node itu.")
        embed = discord.Embed(title=f"🧾 Hollow Log — {node_name}", color=discord.Color.dark_teal())
        for l in logs:
            date = l.get("created_at", "-")
            ev = l.get("event") or "-"
            vendors = ", ".join(_json_load(l.get("vendors"), [])) or "-"
            visitors = ", ".join(_json_load(l.get("visitors"), [])) or "-"
            embed.add_field(
                name=f"{date}",
                value=f"🎯 {ev}\n💰 {vendors}\n👁 {visitors}",
                inline=False
            )
        await ctx.send(embed=embed)

    # ---------------- Daily & Slot Roll ----------------
    @hollow.command(name="roll")
    @commands.has_permissions(administrator=True)
    async def roll_node(self, ctx, node_name: str):
        embed = _roll_daily(ctx.guild.id, node_name)
        await ctx.send(embed=embed)

    @hollow.command(name="daily_roll")
    @commands.has_permissions(administrator=True)
    async def daily_roll(self, ctx, node_name: str):
        embed = _roll_daily(ctx.guild.id, node_name, time_label="day")
        await ctx.send(embed=embed)

    @hollow.command(name="slot_roll")
    @commands.has_permissions(administrator=True)
    async def slot_roll(self, ctx, node_name: str, slot: str):
        embed = _roll_slot(ctx.guild.id, node_name, slot)
        await ctx.send(embed=embed)

    @hollow.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce_node(self, ctx, node_name: str):
        embed = _make_announcement(ctx.guild.id, node_name)
        if not embed:
            return await ctx.send("📭 Tidak ada hasil roll terakhir untuk node itu.")
        await ctx.send(embed=embed)

    @hollow.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_all(self, ctx):
        embeds = _sync_all(ctx.guild.id)
        for e in embeds:
            await ctx.send(embed=e)
        await ctx.send("✅ Semua node Hollow telah di-roll ulang.")

    # ---------------- Vendor Management ----------------
    @hollow.command(name="addnpc")
    @commands.has_permissions(administrator=True)
    async def addnpc(self, ctx, npc_name: str, node_name: str, chance: int = 50, rarity: str = "common"):
        """
        Tambah vendor/NPC ke node, sekaligus set chance & rarity.
        Contoh: !hollow addnpc "Kall Ryn" Outskritz 20 uncommon
        """
        msg = _add_npc(ctx.guild.id, node_name, npc_name, chance, rarity)
        await ctx.send(msg)

    @hollow.command(name="removenpc")
    @commands.has_permissions(administrator=True)
    async def removenpc(self, ctx, npc_name: str, node_name: str):
        msg = _remove_npc(ctx.guild.id, node_name, npc_name)
        await ctx.send(msg)

    @hollow.command(name="listnpc")
    async def listnpc(self, ctx, node_name: str):
        npcs = _list_npc(ctx.guild.id, node_name)
        if not npcs:
            return await ctx.send("📭 Tidak ada NPC di node itu.")
        embed = discord.Embed(title=f"💰 Vendor & NPC — {node_name}", color=discord.Color.gold())
        for npc in npcs:
            if isinstance(npc, str):
                name = npc
                chance = 50
                rarity = "common"
            else:
                name = npc.get("name", "-")
                chance = npc.get("chance", 50)
                rarity = npc.get("rarity", "common")
            embed.add_field(
                name=name,
                value=f"🎯 Chance: {chance}% | 🏷 Rarity: {str(rarity).capitalize()}",
                inline=False
            )
        embed.set_footer(text="Technonesia Hollow Vendors")
        await ctx.send(embed=embed)

    # ---------------- Visitor Management ----------------
    @hollow.command(name="addvisitor")
    @commands.has_permissions(administrator=True)
    async def addvisitor(self, ctx, *, visitor_name: str):
        msg = _add_visitor(ctx.guild.id, visitor_name)
        await ctx.send(msg)

    @hollow.command(name="removevisitor")
    @commands.has_permissions(administrator=True)
    async def removevisitor(self, ctx, *, visitor_name: str):
        msg = _remove_visitor(ctx.guild.id, visitor_name)
        await ctx.send(msg)

    @hollow.command(name="editvisitor")
    @commands.has_permissions(administrator=True)
    async def editvisitor(self, ctx, visitor_name: str, *, entry: str):
        msg = _edit_visitor(ctx.guild.id, visitor_name, entry)
        await ctx.send(msg)

    @hollow.command(name="listvisitor")
    async def listvisitor(self, ctx):
        visitors = _list_visitors(ctx.guild.id)
        if not visitors:
            return await ctx.send("📭 Belum ada visitor global.")
        embed = _make_visitor_list_embed(visitors)
        await ctx.send(embed=embed)

    # ---------------- Event Management ----------------
    @hollow.command(name="addevent")
    @commands.has_permissions(administrator=True)
    async def addevent(self, ctx, *, event_name: str):
        msg = _add_event(ctx.guild.id, event_name)
        await ctx.send(msg)

    @hollow.command(name="removeevent")
    @commands.has_permissions(administrator=True)
    async def removeevent(self, ctx, *, event_name: str):
        msg = _remove_event(ctx.guild.id, event_name)
        await ctx.send(msg)

    @hollow.command(name="editevent")
    @commands.has_permissions(administrator=True)
    async def editevent(self, ctx, event_name: str, *, entry: str):
        msg = _edit_event(ctx.guild.id, event_name, entry)
        await ctx.send(msg)

    @hollow.command(name="listevent")
    async def listevent(self, ctx):
        events = _list_events(ctx.guild.id)
        if not events:
            return await ctx.send("📭 Tidak ada event global.")
        embed = _make_event_list_embed(events)
        await ctx.send(embed=embed)

    @hollow.command(name="assign")
    @commands.has_permissions(administrator=True)
    async def assign_event(self, ctx, event_name: str, node_name: str):
        msg = _assign_event(ctx.guild.id, event_name, node_name)
        await ctx.send(msg)

    @hollow.command(name="clearevent")
    @commands.has_permissions(administrator=True)
    async def clear_event(self, ctx, node_name: str):
        msg = _clear_event(ctx.guild.id, node_name)
        await ctx.send(msg)

    # ---------------- Traits & Types ----------------
    @hollow.group(name="trait")
    @commands.has_permissions(administrator=True)
    async def trait_group(self, ctx):
        pass

    @trait_group.command(name="add")
    async def add_trait(self, ctx, node_name: str, *, trait: str):
        msg = _add_trait(ctx.guild.id, node_name, trait)
        await ctx.send(msg)

    @trait_group.command(name="remove")
    async def remove_trait(self, ctx, node_name: str, *, trait: str):
        msg = _remove_trait(ctx.guild.id, node_name, trait)
        await ctx.send(msg)

    @trait_group.command(name="list")
    async def list_trait(self, ctx, node_name: str):
        traits = _list_traits(ctx.guild.id, node_name)
        embed = discord.Embed(
            title=f"🧩 Traits — {node_name}",
            description="\n".join(traits) if traits else "Tidak ada trait aktif.",
            color=discord.Color.teal()
        )
        await ctx.send(embed=embed)

    @hollow.group(name="type")
    @commands.has_permissions(administrator=True)
    async def type_group(self, ctx):
        pass

    @type_group.command(name="add")
    async def add_type(self, ctx, node_name: str, *, t: str):
        msg = _add_type(ctx.guild.id, node_name, t)
        await ctx.send(msg)

    @type_group.command(name="remove")
    async def remove_type(self, ctx, node_name: str, *, t: str):
        msg = _remove_type(ctx.guild.id, node_name, t)
        await ctx.send(msg)

    @type_group.command(name="list")
    async def list_type(self, ctx, node_name: str):
        types = _list_types(ctx.guild.id, node_name)
        embed = discord.Embed(
            title=f"💠 Types — {node_name}",
            description="\n".join(types) if types else "Tidak ada type aktif.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

# ======================================================
# ✅ SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Hollow(bot))
