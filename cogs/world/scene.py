import discord
from discord.ext import commands
from utils.db import execute, fetchall, fetchone
import json
from cogs.world.timeline import log_event  # ✅ untuk catat ke timeline

class Scene(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scene_pin = {}  # pinned scene per guild

    # ---------- DB Helpers ----------
    def _ensure_table(self, guild_id: int):
        execute(
            guild_id,
            """
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                desc TEXT,
                factions TEXT DEFAULT '[]',
                danger TEXT DEFAULT '-',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def _get_latest_scene(self, guild_id: int):
        row = fetchone(guild_id, "SELECT * FROM scenes ORDER BY updated_at DESC LIMIT 1")
        return row

    # ---------- Command Group ----------
    @commands.group(name="scene", invoke_without_command=True)
    async def scene(self, ctx):
        await ctx.send(
            "Gunakan: `!scene create <nama> | <desc>`\n"
            "`!scene edit <nama> | <desc baru> [--faction ... --danger ...]`\n"
            "`!scene list`, `!scene recall <nama>`\n"
            "`!scene pin`, `!scene unpin`, `!scene show`, `!scene now`"
        )

    # ---------- Create ----------
    @scene.command(name="create")
    async def scene_create(self, ctx, *, entry: str):
        """Buat scene baru: !scene create <nama> | <desc>"""
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        if "|" not in entry:
            return await ctx.send("⚠️ Format: `!scene create <nama> | <desc>`")

        name, desc = [p.strip() for p in entry.split("|", 1)]
        execute(
            guild_id,
            "INSERT OR REPLACE INTO scenes (name, desc) VALUES (?, ?)",
            (name, desc),
        )

        log_event(
            guild_id,
            ctx.author.id,
            code=f"SCENE_CREATE_{name.upper()}",
            title=f"🌍 Scene dibuat: {name}",
            details=desc,
            etype="scene_create",
            actors=[],
            tags=["scene", "create"]
        )

        await ctx.send(f"🌍 Scene **{name}** dibuat.")

    # ---------- Edit ----------
    @scene.command(name="edit")
    async def scene_edit(self, ctx, *, entry: str):
        """
        Edit scene lama: !scene edit <nama> | <desc baru> [--faction ... --danger ...]
        """
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        if "|" not in entry:
            return await ctx.send("⚠️ Format: `!scene edit <nama> | <desc>`")

        name, desc = [p.strip() for p in entry.split("|", 1)]

        factions = []
        danger = None
        if "--faction" in desc:
            parts = desc.split("--faction")
            desc, fact_str = parts[0].strip(), parts[1].strip()
            factions = [f.strip() for f in fact_str.split(",")]
        if "--danger" in desc:
            parts = desc.split("--danger")
            desc, danger = parts[0].strip(), parts[1].strip()

        row = fetchone(guild_id, "SELECT * FROM scenes WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Scene **{name}** tidak ditemukan.")

        execute(
            guild_id,
            "UPDATE scenes SET desc=?, factions=?, danger=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
            (desc, json.dumps(factions), (danger or row.get("danger") or "-"), name)
        )

        log_event(
            guild_id,
            ctx.author.id,
            code=f"SCENE_EDIT_{name.upper()}",
            title=f"✏️ Scene diedit: {name}",
            details=desc,
            etype="scene_edit",
            actors=[],
            tags=["scene", "edit"]
        )

        # auto pin versi baru
        self.scene_pin[guild_id] = {
            "name": name,
            "desc": desc,
            "factions": factions,
            "danger": danger or "-"
        }

        await ctx.send(f"✏️ Scene **{name}** diperbarui & dipin.")

    # ---------- List ----------
    @scene.command(name="list")
    async def scene_list(self, ctx):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        rows = fetchall(guild_id, "SELECT * FROM scenes ORDER BY updated_at DESC LIMIT 10")
        if not rows:
            return await ctx.send("⚠️ Belum ada scene.")

        out = []
        for r in rows:
            out.append(f"📍 **{r['name']}** — {r['desc'][:50]}...")
        await ctx.send("\n".join(out))

    # ---------- Recall ----------
    @scene.command(name="recall")
    async def scene_recall(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        row = fetchone(guild_id, "SELECT * FROM scenes WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Scene **{name}** tidak ditemukan.")

        data = {
            "name": row["name"],
            "desc": row.get("desc", "-"),
            "factions": json.loads(row.get("factions") or "[]"),
            "danger": row.get("danger", "-"),
        }
        self.scene_pin[guild_id] = data
        await ctx.send(f"📌 Scene **{name}** dipin (recall).")

    # ---------- Pin / Unpin / Show / Now ----------
    @scene.command(name="pin")
    async def scene_pin_cmd(self, ctx):
        guild_id = ctx.guild.id
        row = self._get_latest_scene(guild_id)
        if not row:
            return await ctx.send("⚠️ Tidak ada scene/zone terakhir.")
        self.scene_pin[guild_id] = {
            "name": row["name"],
            "desc": row.get("desc", "-"),
            "factions": json.loads(row.get("factions") or "[]"),
            "danger": row.get("danger", "-"),
        }
        await ctx.send(f"📌 Scene **{row['name']}** dipin.")

    @scene.command(name="unpin")
    async def scene_unpin_cmd(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.scene_pin:
            old = self.scene_pin[guild_id]
            del self.scene_pin[guild_id]
            await ctx.send(f"❎ Scene {old.get('name')} unpinned.")
        else:
            await ctx.send("⚠️ Tidak ada scene yang sedang dipin.")

    @scene.command(name="show")
    async def scene_show_cmd(self, ctx):
        guild_id = ctx.guild.id
        data = self.scene_pin.get(guild_id)
        if not data:
            return await ctx.send("⚠️ Tidak ada scene yang sedang dipin.")
        embed = discord.Embed(
            title=f"📍 {data.get('name','(tanpa nama)')}",
            description=data.get("desc", "-"),
            color=discord.Color.green()
        )
        embed.add_field(name="🔺 Faksi", value=", ".join(data.get("factions", []) or ["-"]), inline=False)
        embed.add_field(name="⚠️ Bahaya", value=data.get("danger", "-"), inline=True)
        await ctx.send(embed=embed)

    @scene.command(name="now")
    async def scene_now_cmd(self, ctx):
        """Alias cepat untuk tampilkan scene terpin saat ini"""
        await self.scene_show_cmd(ctx)

async def setup(bot):
    await bot.add_cog(Scene(bot))
