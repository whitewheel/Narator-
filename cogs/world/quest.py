import discord
from discord.ext import commands
from utils.db import fetchone, fetchall, execute
import json
import re
from cogs.world.timeline import log_event  # hook timeline
from services import quest_service

# --------------------
# Storage helpers (per server)
# --------------------
def save_quest(guild_id: int, data: dict):
    execute(guild_id, """
        INSERT INTO quests (name, desc, status, assigned_to, rewards, favor, tags, archived, rewards_visible)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            desc=excluded.desc,
            status=excluded.status,
            assigned_to=excluded.assigned_to,
            rewards=excluded.rewards,
            favor=excluded.favor,
            tags=excluded.tags,
            archived=excluded.archived,
            rewards_visible=excluded.rewards_visible,
            updated_at=CURRENT_TIMESTAMP
    """, (
        data["name"],
        data.get("desc", ""),
        data.get("status", "open"),
        json.dumps(data.get("assigned_to", [])),
        json.dumps(data.get("rewards", {})),
        json.dumps(data.get("favor", {})),
        json.dumps(data.get("tags", {})),
        data.get("archived", 0),
        data.get("rewards_visible", 1)
    ))

def load_quest(guild_id: int, name: str):
    row = fetchone(guild_id, "SELECT * FROM quests WHERE name=?", (name,))
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
        "archived": row.get("archived", 0),
        "rewards_visible": row.get("rewards_visible", 1),
    }

def load_all_quests(guild_id: int):
    rows = fetchall(guild_id, "SELECT * FROM quests")
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
            "archived": r.get("archived", 0),
            "rewards_visible": r.get("rewards_visible", 1),
        }
    return out

# --------------------
# Parsing helpers
# --------------------
def parse_kv_pairs(s: str):
    # ambil items="..." agar spasi di dalamnya tidak pecah
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
    # "Item A x1; Item B x2" -> [{"name":"Item A","qty":1}, {"name":"Item B","qty":2}]
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
            "rewards": {"xp": 0, "gold": 0, "loot": {}, "favor": {}},
            "favor": {},
            "tags": {},
            "archived": 0,
            "rewards_visible": 1,  # 1=player bisa lihat reward; 0=disembunyikan
        }

    # ---------- Root ----------
    @commands.group(name="quest", invoke_without_command=True)
    async def quest(self, ctx):
        await ctx.send("Gunakan: `!quest add`, `!quest show`, `!quest gmshow`, `!quest showarchived`, `!quest detail`, `!quest assign`, `!quest reward`, `!quest rewardvisible`, `!quest reveal`, `!quest complete`, `!quest fail`, `!quest archive`")

    # ---------- Add ----------
    @quest.command(name="add")
    async def quest_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        parts = [p.strip() for p in entry.split("|")]
        if len(parts) < 2:
            return await ctx.send("⚠️ Format: `!quest add Nama | Deskripsi | [--hidden]`")
        name, desc = parts[0], parts[1]
        hidden = any("--hidden" in p.lower() for p in parts[2:])
        q = self._quest_template(name, desc, hidden)
        save_quest(guild_id, q)
        await ctx.send(f"📜 Quest **{name}** dibuat. Status: {'hidden' if hidden else 'open'}.")

    # ---------- Player Show ----------
    @quest.command(name="show")
    async def quest_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id

        # tanpa nama: list semua quest OPEN yang di-assign ke player ini
        if not name:
            allq = load_all_quests(guild_id)
            out = []
            for nm, q in allq.items():
                if q.get("archived", 0) == 1:
                    continue
                if q.get("status") != "open":
                    continue
                if ctx.author.display_name in q.get("assigned_to", []):
                    out.append(f"• **{nm}** — _{q['status']}_")
            if not out:
                return await ctx.send("📭 Kamu belum punya quest yang aktif.")
            return await ctx.send("\n".join(out[:25]))

        # dengan nama: cek apakah player ini assigned ke quest tsb
        q = load_quest(guild_id, name)
        if not q or q.get("status") != "open":
            return await ctx.send("❌ Quest tidak ditemukan atau belum terbuka.")
        if ctx.author.display_name not in q.get("assigned_to", []):
            return await ctx.send("📭 Kamu tidak sedang assigned ke quest ini.")
        await ctx.send(f"✅ Kamu terdaftar di quest **{name}** (status: {q['status']}).")

    # ---------- GM Show ----------
    @quest.command(name="gmshow")
    @commands.has_permissions(administrator=True)
    async def quest_gmshow(self, ctx):
        guild_id = ctx.guild.id
        allq = load_all_quests(guild_id)
        out = []
        for nm, q in allq.items():
            if q.get("archived", 0) == 1:
                continue
            assigned = ", ".join(q.get("assigned_to", [])) or "-"
            st = q.get("status", "open")
            out.append(f"• **{nm}** — _{st}_ → Assigned: {assigned}")
        if not out:
            return await ctx.send("Tidak ada quest aktif.")
        await ctx.send("\n".join(out[:25]))

    # ---------- Archived ----------
    @quest.command(name="showarchived")
    async def quest_show_archived(self, ctx):
        guild_id = ctx.guild.id
        allq = load_all_quests(guild_id)
        out = []
        for nm, q in allq.items():
            if q.get("archived", 0) == 1:
                st = q.get("status", "open")
                out.append(f"• **{nm}** — _{st}_ 📦")
        if not out:
            return await ctx.send("Tidak ada quest yang diarsipkan.")
        await ctx.send("\n".join(out[:25]))

    # ---------- Detail ----------
    @quest.command(name="detail")
    async def quest_detail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        await self._send_quest_detail(ctx, q)

    # ---------- Assign ----------
    @quest.command(name="assign")
    async def quest_assign(self, ctx, name: str, *, chars_csv: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        chars = [c.strip() for c in chars_csv.split(",") if c.strip()]
        q["assigned_to"] = list(dict.fromkeys(chars))
        save_quest(guild_id, q)
        await ctx.send(f"✅ Quest **{name}** di-assign ke: {', '.join(q['assigned_to'])}")

    # ---------- Reward (xp/gold/items->loot/favor) ----------
    @quest.command(name="reward")
    async def quest_reward(self, ctx, name: str, *, spec: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        kv = parse_kv_pairs(spec)
        r = q.get("rewards", {"xp": 0, "gold": 0, "loot": {}, "favor": {}})

        # XP
        if "xp" in kv:
            try: r["xp"] = int(kv["xp"])
            except: pass
        # Gold
        if "gold" in kv:
            try: r["gold"] = int(kv["gold"])
            except: pass
        # Items -> Loot map
        if "items" in kv:
            items = parse_items_list(kv["items"])
            loot_map = {}
            for it in items:
                loot_map[it["name"]] = it["qty"]
            r["loot"] = loot_map
        # Favor
        if "favor" in kv:
            fav = {}
            for part in kv["favor"].split(","):
                if ":" in part:
                    fac, val = part.split(":", 1)
                    try:
                        fav[fac.strip()] = int(val.strip())
                    except:
                        continue
            r["favor"] = fav

        q["rewards"] = r
        save_quest(guild_id, q)
        await ctx.send(f"🎁 Reward quest **{name}** diset. XP {r.get('xp',0)}, Gold {r.get('gold',0)}, Loot {len(r.get('loot',{}))}.")

    # ---------- Toggle reward visible ----------
    @quest.command(name="rewardvisible")
    @commands.has_permissions(administrator=True)
    async def quest_reward_visible(self, ctx, name: str, mode: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")

        if mode.lower() in ["on", "yes", "true", "1"]:
            q["rewards_visible"] = 1
            save_quest(guild_id, q)
            await ctx.send(f"👁️ Reward quest **{name}** sekarang **terlihat** oleh player.")
        elif mode.lower() in ["off", "no", "false", "0"]:
            q["rewards_visible"] = 0
            save_quest(guild_id, q)
            await ctx.send(f"🙈 Reward quest **{name}** sekarang **disembunyikan** dari player.")
        else:
            await ctx.send("⚠️ Gunakan: `!quest rewardvisible <nama> on/off`")

    # ---------- Reveal (embed ringkas) ----------
    @quest.command(name="reveal")
    async def quest_reveal(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "open"
        save_quest(guild_id, q)

        embed = discord.Embed(
            title=f"🔔 Quest Baru: {q['name']}",
            description=(q.get("desc", "-")[:200] + "...") if len(q.get("desc", "")) > 200 else q.get("desc", "-"),
            color=discord.Color.green()
        )
        embed.set_footer(text="Gunakan !quest detail <nama> untuk lihat informasi lengkap.")
        await ctx.send(embed=embed)

    # ---------- Complete (embed breakdown) ----------
    @quest.command(name="complete")
    async def quest_complete(self, ctx, name: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")

        # Mark selesai + arsip
        q["status"] = "completed"
        q["archived"] = 1
        save_quest(guild_id, q)

        rewards = q.get("rewards", {})
        embed = discord.Embed(
            title=f"✅ Quest Selesai: {q['name']}",
            description="Quest telah diselesaikan! Berikut hadiahnya:",
            color=discord.Color.gold()
        )

        if rewards.get("xp", 0) > 0 or rewards.get("gold", 0) > 0:
            embed.add_field(
                name="XP / Gold",
                value=f"⭐ {rewards.get('xp',0)} XP\n💰 {rewards.get('gold',0)} Gold",
                inline=False
            )

        loot = rewards.get("loot", {})
        if loot:
            loot_str = "\n".join([f"🎁 {qty}x {item}" for item, qty in loot.items()])
            embed.add_field(name="Loot", value=loot_str, inline=False)

        favor = rewards.get("favor", {})
        if favor:
            favor_str = "\n".join([f"💠 {fac}: {val:+d}" for fac, val in favor.items()])
            embed.add_field(name="Favor", value=favor_str, inline=False)

        await ctx.send(embed=embed)

        # jalankan servis penyelesaian (auto add xp/gold/loot)
        msg = await quest_service.complete_quest(guild_id, name, q.get("assigned_to", []), ctx.author.id)
        if msg:
            await ctx.send(msg)

        # timeline log
        log_event(
            guild_id,
            ctx.author.id,
            code=f"Q_COMPLETE_{name.upper()}",
            title=f"Quest selesai: {name}",
            details=json.dumps(q.get("rewards", {})),
            etype="quest_complete",
            quest=name,
            actors=q.get("assigned_to", []),
            tags=["quest","complete"]
        )

    # ---------- Fail ----------
    @quest.command(name="fail")
    async def quest_fail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["status"] = "failed"
        q["archived"] = 1
        save_quest(guild_id, q)
        log_event(guild_id,
                  ctx.author.id,
                  code=f"Q_FAIL_{name.upper()}",
                  title=f"Quest gagal: {name}",
                  etype="quest_fail",
                  quest=name,
                  actors=q.get("assigned_to", []),
                  tags=["quest","fail"])
        await ctx.send(f"❌ Quest **{name}** ditandai **FAILED** dan diarsipkan.")

    # ---------- Archive ----------
    @quest.command(name="archive")
    async def quest_archive(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        q = load_quest(guild_id, name)
        if not q:
            return await ctx.send("❌ Quest tidak ditemukan.")
        q["archived"] = 1
        save_quest(guild_id, q)
        await ctx.send(f"📦 Quest **{name}** berhasil diarsipkan.")

    # ---------- Helper (Embed Detail) ----------
    async def _send_quest_detail(self, ctx, q, gm_view: bool = False):
        r = q.get("rewards", {})
        loot = r.get("loot", {})
        loot_str = "\n".join([f"- {item} x{qty}" for item, qty in loot.items()]) or "-"
        assigned = ", ".join(q.get("assigned_to", [])) or "-"

        title_icon = "📜"
        if q.get("status") == "hidden":
            title_icon += " 🔒"
        if q.get("archived", 0) == 1:
            title_icon += " 📦"

        embed = discord.Embed(
            title=f"{title_icon} {q['name']}",
            description=q.get("desc", "-"),
            color=discord.Color.gold()
        )
        embed.add_field(name="Status", value=q.get("status", "open"), inline=True)
        embed.add_field(name="Assigned To", value=assigned, inline=True)

        # tampilkan reward sesuai visibility
        if gm_view or q.get("rewards_visible", 1) == 1:
            embed.add_field(name="XP/Gold", value=f"{r.get('xp',0)} XP / {r.get('gold',0)} Gold", inline=False)
            embed.add_field(name="Loot", value=loot_str, inline=False)
        else:
            embed.add_field(name="Reward", value="❓ Tidak diketahui", inline=False)

        if q.get("favor"):
            fav_str = "\n".join([f"{f}: {v:+d}" for f, v in q["favor"].items()])
            embed.add_field(name="Favor", value=fav_str, inline=False)

        if q.get("archived", 0) == 1:
            embed.set_footer(text="📦 Arsip Quest")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Quest(bot))
