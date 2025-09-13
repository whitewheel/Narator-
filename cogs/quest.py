import discord
from discord.ext import commands
from memory import save_memory, get_recent, template_for
import json
import re

def _key(ctx):
    return (str(ctx.guild.id), str(ctx.channel.id))

# --------------------
# Storage helpers
# --------------------
def save_quest(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "quest", json.dumps(data), {"name": name})

def load_quest(guild_id, channel_id, name):
    rows = get_recent(guild_id, channel_id, "quest", 200)
    for (_id, cat, content, meta, ts) in rows:
        try:
            q = json.loads(content)
            if meta.get("name","").lower() == name.lower() or q.get("name","").lower() == name.lower():
                return q
        except:
            continue
    return None

def load_all_quests(guild_id, channel_id):
    rows = get_recent(guild_id, channel_id, "quest", 200)
    out = {}
    for (_id, cat, content, meta, ts) in rows:
        try:
            q = json.loads(content)
            nm = meta.get("name", q.get("name"))
            out[nm] = q
        except:
            continue
    return out

def save_char(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "character", json.dumps(data), {"name": name})

def load_char(guild_id, channel_id, name):
    rows = get_recent(guild_id, channel_id, "character", 200)
    for (_id, cat, content, meta, ts) in rows:
        try:
            c = json.loads(content)
            if meta.get("name","").lower() == name.lower() or c.get("name","").lower() == name.lower():
                return c
        except:
            continue
    return None

def get_item(guild_id, channel_id, name):
    rows = get_recent(guild_id, channel_id, "item", 200)
    for (_id, cat, content, meta, ts) in rows:
        try:
            i = json.loads(content)
            if i.get("name","").lower() == name.lower():
                return i
        except:
            continue
    return None

# --------------------
# Parsing helpers
# --------------------
def parse_kv_pairs(s: str):
    \"\"\"Parse simple pairs like 'xp=100 gold=50 favor=ArthaDyne:10' (favor optional).
    Items can be specified with items=\"Potion x2; Dagger\".
    \"\"\"
    # Extract items=\"...\"
    items_spec = None
    m = re.search(r'items\\s*=\\s*\"(.*?)\"', s)
    if m:
        items_spec = m.group(1)
        s = s[:m.start()] + s[m.end():]

    kv = {}
    for part in s.strip().split():
        if \"=\" in part:
            k, v = part.split(\"=\", 1)
            kv[k.lower()] = v
    if items_spec is not None:
        kv[\"items\"] = items_spec
    return kv

def parse_items_list(spec: str):
    \"\"\"'Potion x2; Rusty Dagger; Gold Coin x10' -> [{\"name\":\"Potion\",\"qty\":2}, ...]\"\"\"
    items = []
    for chunk in [c.strip() for c in spec.split(\";\")]:
        if not chunk:
            continue
        qty = 1
        m = re.search(r\"\\s+x(\\d+)$\", chunk, flags=re.IGNORECASE)
        if m:
            qty = int(m.group(1))
            name = chunk[:m.start()].strip()
        else:
            name = chunk.strip()
        items.append({\"name\": name, \"qty\": qty})
    return items

# --------------------
# Cog
# --------------------
class Quest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _quest_template(self, name: str, desc: str, hidden: bool = False):
        data = template_for(\"quest\")
        # Ensure baseline fields
        data.update({
            \"name\": name,
            \"desc\": desc,
            \"status\": \"hidden\" if hidden else \"active\",
            \"objectives\": [],
            \"assigned_to\": [],            # list of character names
            \"rewards\": {                  # xp per char, gold per char, items per char
                \"xp\": 0,
                \"gold\": 0,
                \"items\": []               # [{\"name\":\"Potion\",\"qty\":1}, ...]
            },
            \"favor\": {},                  # {\"Faction\": +10}
            \"tags\": {},
        })
        return data

    # ---------- Commands ----------
    @commands.group(name=\"quest\", invoke_without_command=True)
    async def quest(self, ctx):
        await ctx.send(\"Gunakan: `!quest add`, `!quest show`, `!quest detail`, `!quest assign`, `!quest reward`, `!quest reveal`, `!quest complete`, `!quest fail`\")

    @quest.command(name=\"add\")
    async def quest_add(self, ctx, *, entry: str):
        \"\"\"Format: !quest add Nama | Deskripsi | [--hidden]\"\"\"
        parts = [p.strip() for p in entry.split(\"|\")]
        if len(parts) < 2:
            return await ctx.send(\"⚠️ Format: `!quest add Nama | Deskripsi | [--hidden]`\")
        name, desc = parts[0], parts[1]
        hidden = any(\"--hidden\" in p.lower() for p in parts[2:])
        q = self._quest_template(name, desc, hidden)
        k = _key(ctx)
        save_quest(k[0], k[1], ctx.author.id, name, q)
        await ctx.send(f\"📜 Quest **{name}** dibuat. Status: {'hidden' if hidden else 'active'}.\")

    @quest.command(name=\"show\")
    async def quest_show(self, ctx, status: str = \"active\"):
        \"\"\"!quest show [active|hidden|all|complete|failed]\"\"\"
        k = _key(ctx)
        allq = load_all_quests(k[0], k[1])
        filt = status.lower()
        out = []
        for nm, q in allq.items():
            st = q.get(\"status\",\"active\")
            if filt == \"all\" or st == filt:
                out.append(f\"• **{nm}** — _{st}_\")
        if not out:
            return await ctx.send(\"Tidak ada quest yang cocok.\")
        await ctx.send(\"\\n\".join(out[:25]))

    @quest.command(name=\"detail\")
    async def quest_detail(self, ctx, *, name: str):
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        r = q.get(\"rewards\", {})
        items = r.get(\"items\", [])
        items_str = \"\\n\".join([f\"- {it['name']} x{it.get('qty',1)}\" for it in items]) or \"-\"
        assigned = \", \".join(q.get(\"assigned_to\", [])) or \"-\"
        embed = discord.Embed(title=f\"📜 {q['name']}\", description=q.get(\"desc\",\"-\"), color=discord.Color.gold())
        embed.add_field(name=\"Status\", value=q.get(\"status\",\"active\"), inline=True)
        embed.add_field(name=\"Assigned To\", value=assigned, inline=True)
        embed.add_field(name=\"XP/Gold\", value=f\"{r.get('xp',0)} XP / {r.get('gold',0)} Gold (per karakter)\", inline=False)
        embed.add_field(name=\"Items\", value=items_str, inline=False)
        if q.get(\"favor\"):
            fav_str = \"\\n\".join([f\"{f}: {v:+d}\" for f, v in q[\"favor\"].items()])
            embed.add_field(name=\"Favor\", value=fav_str, inline=False)
        await ctx.send(embed=embed)

    @quest.command(name=\"assign\")
    async def quest_assign(self, ctx, name: str, *, chars_csv: str):
        \"\"\"!quest assign <QuestName> <Char1,Char2,...>\"\"\"
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        chars = [c.strip() for c in chars_csv.split(\",\") if c.strip()]
        q[\"assigned_to\"] = list(dict.fromkeys(chars))  # unique, keep order
        save_quest(k[0], k[1], ctx.author.id, name, q)
        await ctx.send(f\"✅ Quest **{name}** di-assign ke: {', '.join(q['assigned_to'])}\")

    @quest.command(name=\"reward\")
    async def quest_reward(self, ctx, name: str, *, spec: str):
        \"\"\"!quest reward <QuestName> xp=100 gold=50 items=\"Potion x2; Rusty Dagger\" favor=ArthaDyne:+10\"\"\"
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        kv = parse_kv_pairs(spec)
        r = q.get(\"rewards\", {\"xp\":0,\"gold\":0,\"items\":[]})
        if \"xp\" in kv:
            try: r[\"xp\"] = int(kv[\"xp\"])
            except: pass
        if \"gold\" in kv:
            try: r[\"gold\"] = int(kv[\"gold\"])
            except: pass
        if \"items\" in kv:
            r[\"items\"] = parse_items_list(kv[\"items\"])
        # favor optional
        if \"favor\" in kv:
            fav = {}
            for part in kv[\"favor\"].split(\",\"):
                part = part.strip()
                if not part: continue
                if \":\" in part:
                    fac, val = part.split(\":\",1)
                    try:
                        fav[fac.strip()] = int(val.strip())
                    except:
                        continue
            q[\"favor\"] = fav
        q[\"rewards\"] = r
        save_quest(k[0], k[1], ctx.author.id, name, q)
        await ctx.send(f\"🎁 Reward quest **{name}** diset. XP {r.get('xp',0)}, Gold {r.get('gold',0)}, Items {len(r.get('items',[]))}.\")

    @quest.command(name=\"reveal\")
    async def quest_reveal(self, ctx, *, name: str):
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        q[\"status\"] = \"active\"
        save_quest(k[0], k[1], ctx.author.id, name, q)
        await ctx.send(f\"🔔 Quest **{name}** sekarang **ACTIVE**.\")

    @quest.command(name=\"complete\")
    async def quest_complete(self, ctx, name: str, *, targets: str = None):
        \"\"\"!quest complete <QuestName> [to=Aima,Zarek]
        - Jika 'to' tidak diberikan, gunakan assigned_to.
        - Jika assigned_to kosong, hanya tandai complete tanpa auto-reward.\"\"\"
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        # resolve targets
        to_chars = []
        if targets and \"to=\" in targets:
            to_chars = [c.strip() for c in targets.split(\"to=\",1)[1].split(\",\") if c.strip()]
        elif q.get(\"assigned_to\"):
            to_chars = q[\"assigned_to\"]

        # mark complete
        q[\"status\"] = \"complete\"
        save_quest(k[0], k[1], ctx.author.id, name, q)

        r = q.get(\"rewards\", {})
        xp = int(r.get(\"xp\", 0) or 0)
        gold = int(r.get(\"gold\", 0) or 0)
        items = r.get(\"items\", [])
        favor = q.get(\"favor\", {})

        applied = []
        for ch in to_chars:
            c = load_char(k[0], k[1], ch)
            if not c:
                continue
            # apply xp/gold
            c[\"xp\"] = int(c.get(\"xp\",0)) + xp
            c[\"gold\"] = int(c.get(\"gold\",0)) + gold
            # apply items
            inv = c.get(\"inventory\", [])
            for it in items:
                name_i = it.get(\"name\")
                qty_i = int(it.get(\"qty\",1))
                # get from library to add details
                lib = get_item(k[0], k[1], name_i) or {\"name\": name_i}
                exists = next((x for x in inv if x[\"name\"].lower() == name_i.lower()), None)
                if exists:
                    exists[\"qty\"] = exists.get(\"qty\",1) + qty_i
                else:
                    add = lib.copy()
                    add[\"qty\"] = qty_i
                    inv.append(add)
            c[\"inventory\"] = inv
            save_char(k[0], k[1], ctx.author.id, ch, c)
            applied.append(ch)

        # favor integration (stub: announce only)
        fav_text = \"\"
        if favor:
            fav_text = \"\\n\".join([f\"{f}: {v:+d}\" for f, v in favor.items()])

        embed = discord.Embed(title=f\"✅ Quest Complete: {q['name']}\", description=q.get(\"desc\",\"-\"), color=discord.Color.green())
        if applied:
            embed.add_field(name=\"Reward Applied To\", value=\", \".join(applied), inline=False)
            embed.add_field(name=\"XP/Gold\", value=f\"{xp} XP / {gold} Gold per karakter\", inline=False)
            if items:
                items_str = \"\\n\".join([f\"- {it['name']} x{it.get('qty',1)}\" for it in items])
                embed.add_field(name=\"Items\", value=items_str, inline=False)
        else:
            embed.add_field(name=\"Info\", value=\"Tidak ada target karakter. Gunakan `to=<Char1,Char2>` atau assign dulu.\", inline=False)
        if fav_text:
            embed.add_field(name=\"Favor\", value=fav_text, inline=False)
        await ctx.send(embed=embed)

    @quest.command(name=\"fail\")
    async def quest_fail(self, ctx, *, name: str):
        k = _key(ctx)
        q = load_quest(k[0], k[1], name)
        if not q:
            return await ctx.send(\"❌ Quest tidak ditemukan.\")
        q[\"status\"] = \"failed\"
        save_quest(k[0], k[1], ctx.author.id, name, q)
        await ctx.send(f\"❌ Quest **{name}** ditandai **FAILED**.\")

async def setup(bot):
    await bot.add_cog(Quest(bot))
