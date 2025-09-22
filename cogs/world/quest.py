import discord
from discord.ext import commands
from utils.db import fetchone, fetchall
import json
import re
from cogs.world.timeline import log_event  # hook timeline
from services import quest_service

# --------------------
# Storage helpers (global, pakai tabel quests)
# --------------------
def save_quest(data: dict):
    from utils.db import execute
    execute("""
        INSERT INTO quests (name, desc, status, assigned_to, rewards, favor, tags)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            desc=excluded.desc,
            status=excluded.status,
            assigned_to=excluded.assigned_to,
            rewards=excluded.rewards,
            favor=excluded.favor,
            tags=excluded.tags,
            updated_at=CURRENT_TIMESTAMP
    """, (
        data["name"],
        data.get("desc", ""),
        data.get("status", "open"),
        json.dumps(data.get("assigned_to", [])),
        json.dumps(data.get("rewards", {})),
        json.dumps(data.get("favor", {})),
        json.dumps(data.get("tags", {}))
    ))

def load_quest(name: str):
    row = fetchone("SELECT * FROM quests WHERE name=?", (name,))
    if not row:
        return None
    return {
        "name": row["name"],
        "desc": row["desc"],
        "status": row["status"],
        "assigned_to": json.loads(row.get("assigned_to") or "[]"),
        "rewards": json.loads(row.get("rewards") or "{}"),
        "favor": json.loads(row.get("favor") or "{}"),
        "tags": json.loads(row.get("tags") or "{}"),
    }

def load_all_quests():
    rows = fetchall("SELECT * FROM quests")
    out = {}
    for r in rows:
        out[r["name"]] = {
            "name": r["name"],
            "desc": r["desc"],
            "status": r["status"],
            "assigned_to": json.loads(r.get("assigned_to") or "[]"),
            "rewards": json.loads(r.get("rewards") or "{}"),
            "favor": json.loads(r.get("favor") or "{}"),
            "tags": json.loads(r.get("tags") or "{}"),
        }
    return out

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
        return {
            "name": name,
            "desc": desc,
            "status": "hidden" if hidden else "open",
            "assigned_to": [],
            "rewards": {"xp": 0, "gold": 0, "items": []},
            "favor": {},
            "tags": {},
        }

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
        save_quest(q)
        await ctx.send(f"📜 Quest **{name}** dibuat. Status: {'hidden' if hidden else 'open'}.")

    @quest.command(name="show")
    async def quest_show(self, ctx, status: str = "all"):
        allq = load_all_quests()
        filt = status.lower()
        out = []
        for nm, q in allq.items():
            st = q.get("status", "open")
            if filt == "all" or st.lower() == filt:
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
        embed.add_field(name="Status", value=q.get("status", "open"), inline=True)
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
        save_quest(q)
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
        save_quest(q)
        await ctx.send(f"🎁 Reward quest **{name}** diset. XP {r.get('xp',0)}, Gold {r.get('gold',0)}, Items {len(r.get('items',[]))}.")

    @quest.command(name="reveal")
    async def quest_reveal(self, ctx, *, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "open"
        save_quest(q)
        await ctx.send(f"🔔 Quest **{name}** sekarang **OPEN**.")

    @quest.command(name="complete")
    async def quest_complete(self, ctx, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")

        # tandai completed
        q["status"] = "completed"
        save_quest(q)

        # eksekusi reward lewat quest_service
        msg = quest_service.complete_quest(name, q.get("assigned_to", []), ctx.author.id)

        # log timeline
        log_event(ctx.author.id,
                  code=f"Q_COMPLETE_{name.upper()}",
                  title=f"Quest selesai: {name}",
                  details=json.dumps(q.get("rewards", {})),
                  etype="quest_complete",
                  quest=name,
                  actors=q.get("assigned_to", []),
                  tags=["quest","complete"])

        await ctx.send(f"✅ Quest **{name}** diselesaikan.\n{msg}")

    @quest.command(name="fail")
    async def quest_fail(self, ctx, *, name: str):
        q = load_quest(name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "failed"
        save_quest(q)
        log_event(ctx.author.id,
                  code=f"Q_FAIL_{name.upper()}",
                  title=f"Quest gagal: {name}",
                  etype="quest_fail",
                  quest=name,
                  actors=q.get("assigned_to", []),
                  tags=["quest","fail"])
        await ctx.send(f"❌ Quest **{name}** ditandai **FAILED**.")

async def setup(bot):
    await bot.add_cog(Quest(bot))
