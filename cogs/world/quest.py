import discord
from discord.ext import commands
from utils.db import save_memory, get_recent, template_for
import json
import re

from cogs.world.timeline import log_event  # hook timeline

# --------------------
# Storage helpers (global)
# --------------------
def save_quest(user_id, name, data):
    save_memory(user_id, "quest", json.dumps(data), {"name": name})

def load_quest(name):
    rows = get_recent("quest", 200)
    for r in rows:
        try:
            q = json.loads(r["value"])
            meta = json.loads(r.get("meta") or "{}")
            if meta.get("name", "").lower() == name.lower() or q.get("name", "").lower() == name.lower():
                return q
        except Exception:
            continue
    return None

def load_all_quests():
    rows = get_recent("quest", 200)
    out = {}
    for r in rows:
        try:
            q = json.loads(r["value"])
            meta = json.loads(r.get("meta") or "{}")
            nm = meta.get("name", q.get("name"))
            out[nm] = q
        except Exception:
            continue
    return out

def save_char(user_id, name, data):
    save_memory(user_id, "character", json.dumps(data), {"name": name})

def load_char(name):
    rows = get_recent("character", 200)
    for r in rows:
        try:
            c = json.loads(r["value"])
            meta = json.loads(r.get("meta") or "{}")
            if meta.get("name", "").lower() == name.lower() or c.get("name", "").lower() == name.lower():
                return c
        except Exception:
            continue
    return None

def get_item(name):
    rows = get_recent("item", 200)
    for r in rows:
        try:
            i = json.loads(r["value"])
            if i.get("name", "").lower() == name.lower():
                return i
        except Exception:
            continue
    return None

# --------------------
# Parsing helpers
# --------------------
def parse_kv_pairs(s: str):
    items_spec = None
    m = re.search(r'items\s*=\s*"(.*?)"', s)
    if m:
        items_spec = m.group(1)
        s = s[:m.start()] + s[m.end():]

    kv = {}
    for part in s.strip().split():
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.lower()] = v
    if items_spec is not None:
        kv["items"] = items_spec
    return kv

def parse_items_list(spec: str):
    items = []
    for chunk in [c.strip() for c in spec.split(";")]:
        if not chunk:
            continue
        qty = 1
        m = re.search(r"\s+x(\d+)$", chunk, flags=re.IGNORECASE)
        if m:
            qty = int(m.group(1))
            name = chunk[:m.start()].strip()
        else:
            name = chunk.strip()
        items.append({"name": name, "qty": qty})
    return items

# --------------------
# Cog
# --------------------
class Quest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _quest_template(self, name: str, desc: str, hidden: bool = False):
        data = template_for("quest")
        data.update({
            "name": name,
            "desc": desc,
            "status": "hidden" if hidden else "active",
            "objectives": [],
            "assigned_to": [],
            "rewards": {
                "xp": 0,
                "gold": 0,
                "items": []
            },
            "favor": {},
            "tags": {},
        })
        return data

    # ---------- Commands ----------
    @commands.group(name="quest", invoke_without_command=True)
    async def quest(self, ctx):
        await ctx.send("Gunakan: `!quest add`, `!quest show`, `!quest detail`, `!quest assign`, `!quest reward`, `!quest reveal`, `!quest complete`, `!quest fail`")

    @quest.command(name="add")
    async def quest_add(self, ctx, *, entry: str):
        parts = [p.strip() for p in entry.split("|")]
        if len(parts) < 2:
            return await ctx.send("⚠️ Format: `!quest add Nama | Deskripsi | [--hidden]`")
        name, desc = parts[0], parts[1]
        hidden = any("--hidden" in p.lower() for p in parts[2:])
        q = self._quest_template(name, desc, hidden)
        save_quest(ctx.author.id, name, q)
        await ctx.send(f"📜 Quest **{name}** dibuat. Status: {'hidden' if hidden else 'active'}.")

    @quest.command(name="show")
    async def quest_show(self, ctx, status: str = "active"):
        allq = load_all_quests()
        filt = status.lower()
        out = []
        for nm, q in allq.items():
            st = q.get("status", "active")
            if filt == "all" or st == filt:
                out.append(f"• **{nm}** — _{st}_")
        if not out:
            return await ctx.send("Tidak ada quest yang cocok.")
        await ctx.send("\n".join(out[:25]))

    @quest.command(name="detail")
    async def quest_detail(self, ctx, *, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        r = q.get("rewards", {})
        items = r.get("items", [])
        items_str = "\n".join([f"- {it['name']} x{it.get('qty',1)}" for it in items]) or "-"
        assigned = ", ".join(q.get("assigned_to", [])) or "-"
        embed = discord.Embed(title=f"📜 {q['name']}", description=q.get("desc", "-"), color=discord.Color.gold())
        embed.add_field(name="Status", value=q.get("status", "active"), inline=True)
        embed.add_field(name="Assigned To", value=assigned, inline=True)
        embed.add_field(name="XP/Gold", value=f"{r.get('xp',0)} XP / {r.get('gold',0)} Gold (per karakter)", inline=False)
        embed.add_field(name="Items", value=items_str, inline=False)
        if q.get("favor"):
            fav_str = "\n".join([f"{f}: {v:+d}" for f, v in q["favor"].items()])
            embed.add_field(name="Favor", value=fav_str, inline=False)
        await ctx.send(embed=embed)

    @quest.command(name="assign")
    async def quest_assign(self, ctx, name: str, *, chars_csv: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        chars = [c.strip() for c in chars_csv.split(",") if c.strip()]
        q["assigned_to"] = list(dict.fromkeys(chars))
        save_quest(ctx.author.id, name, q)
        await ctx.send(f"✅ Quest **{name}** di-assign ke: {', '.join(q['assigned_to'])}")

    @quest.command(name="reward")
    async def quest_reward(self, ctx, name: str, *, spec: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        kv = parse_kv_pairs(spec)
        r = q.get("rewards", {"xp": 0, "gold": 0, "items": []})
        if "xp" in kv:
            try: r["xp"] = int(kv["xp"])
            except: pass
        if "gold" in kv:
            try: r["gold"] = int(kv["gold"])
            except: pass
        if "items" in kv:
            r["items"] = parse_items_list(kv["items"])
        if "favor" in kv:
            fav = {}
            for part in kv["favor"].split(","):
                if ":" in part:
                    fac, val = part.split(":", 1)
                    try:
                        fav[fac.strip()] = int(val.strip())
                    except: continue
            q["favor"] = fav
        q["rewards"] = r
        save_quest(ctx.author.id, name, q)
        await ctx.send(f"🎁 Reward quest **{name}** diset. XP {r.get('xp',0)}, Gold {r.get('gold',0)}, Items {len(r.get('items',[]))}.")

    @quest.command(name="reveal")
    async def quest_reveal(self, ctx, *, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "active"
        save_quest(ctx.author.id, name, q)
        await ctx.send(f"🔔 Quest **{name}** sekarang **ACTIVE**.")

    @quest.command(name="complete")
    async def quest_complete(self, ctx, name: str, *, targets: str = None):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        to_chars = []
        if targets and "to=" in targets:
            to_chars = [c.strip() for c in targets.split("to=", 1)[1].split(",") if c.strip()]
        elif q.get("assigned_to"):
            to_chars = q["assigned_to"]

        q["status"] = "complete"
        save_quest(ctx.author.id, name, q)

        r = q.get("rewards", {})
        xp = int(r.get("xp", 0) or 0)
        gold = int(r.get("gold", 0) or 0)
        items = r.get("items", [])
        favor = q.get("favor", {})

        applied = []
        for ch in to_chars:
            c = load_char(ch)
            if not c:
                continue
            c["xp"] = int(c.get("xp", 0)) + xp
            c["gold"] = int(c.get("gold", 0)) + gold
            inv = c.get("inventory", [])
            for it in items:
                name_i = it.get("name")
                qty_i = int(it.get("qty", 1))
                lib = get_item(name_i) or {"name": name_i}
                exists = next((x for x in inv if x["name"].lower() == name_i.lower()), None)
                if exists:
                    exists["qty"] = exists.get("qty", 1) + qty_i
                else:
                    add = lib.copy()
                    add["qty"] = qty_i
                    inv.append(add)
            c["inventory"] = inv
            save_char(ctx.author.id, ch, c)
            applied.append(ch)

        log_event(ctx.author.id,
                  code=f"Q_COMPLETE_{name.upper()}",
                  title=f"Quest selesai: {name}",
                  details=f"Reward: {xp} XP, {gold} gold, items {len(items)}, favor {favor}",
                  etype="quest_complete",
                  quest=name,
                  actors=to_chars,
                  tags=["quest","complete"])
        fav_text = ""
        if favor:
            fav_text = "\n".join([f"{f}: {v:+d}" for f, v in favor.items()])

        embed = discord.Embed(title=f"✅ Quest Complete: {q['name']}", description=q.get("desc", "-"), color=discord.Color.green())
        if applied:
            embed.add_field(name="Reward Applied To", value=", ".join(applied), inline=False)
            embed.add_field(name="XP/Gold", value=f"{xp} XP / {gold} Gold per karakter", inline=False)
            if items:
                items_str = "\n".join([f"- {it['name']} x{it.get('qty',1)}" for it in items])
                embed.add_field(name="Items", value=items_str, inline=False)
        else:
            embed.add_field(name="Info", value="Tidak ada target karakter. Gunakan `to=<Char1,Char2>` atau assign dulu.", inline=False)
        if fav_text:
            embed.add_field(name="Favor", value=fav_text, inline=False)
        await ctx.send(embed=embed)

    @quest.command(name="fail")
    async def quest_fail(self, ctx, *, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "failed"
        save_quest(ctx.author.id, name, q)
        await ctx.send(f"❌ Quest **{name}** ditandai **FAILED**.")

async def setup(bot):
    await bot.add_cog(Quest(bot))
