import discord
from discord.ext import commands
from utils.db import save_memory, get_recent
import json
from cogs.world.timeline import log_event  # ✅ supaya favor masuk ke timeline

class Favor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 2:
            return None
        return {
            "faction": parts[0],
            "favor": int(parts[1]),
            "notes": parts[2] if len(parts) > 2 else ""
        }

    @commands.group(name="favor", invoke_without_command=True)
    async def favor(self, ctx):
        await ctx.send("Gunakan: `!favor add`, `!favor set`, `!favor show`, `!favor detail`, `!favor remove`")

    @favor.command(name="add")
    async def favor_add(self, ctx, *, entry: str):
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format: `!favor add Fraksi | Nilai | [Catatan]`")
        save_memory("0", "0", ctx.author.id, "favor", json.dumps(data), {"faction": data["faction"]})
        log_event("0", "0", ctx.author.id,
                  code=f"FAVOR_ADD_{data['faction'].upper()}",
                  title=f"🪙 Favor ditambahkan: {data['faction']}",
                  details=f"Set ke {data['favor']} ({data.get('notes','-')})",
                  etype="favor_set",
                  actors=[data['faction']],
                  tags=["favor"])
        await ctx.send(f"🪙 Favor untuk **{data['faction']}** diset ke `{data['favor']}`.")

    @favor.command(name="set")
    async def favor_set(self, ctx, *, entry: str):
        await self.favor_add(ctx, entry=entry)

    @favor.command(name="show")
    async def favor_show(self, ctx):
        rows = get_recent("0", "0", "favor", 50)
        out = []
        for r in rows:
            try:
                f = json.loads(r["value"])
                line = f"🪙 **{f['faction']}** → {f['favor']}"
                out.append(line)
            except:
                continue
        if not out:
            return await ctx.send("Tidak ada data favor.")
        await ctx.send("\n".join(out[:15]))

    @favor.command(name="detail")
    async def favor_detail(self, ctx, *, faction: str):
        rows = get_recent("0", "0", "favor", 50)
        for r in rows:
            try:
                f = json.loads(r["value"])
                if f["faction"].lower() == faction.lower():
                    embed = discord.Embed(
                        title=f"🪙 Favor: {f['faction']}",
                        description=f"Nilai: `{f['favor']}`",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="Catatan", value=f.get("notes", "-"), inline=False)
                    await ctx.send(embed=embed)
                    return
            except:
                continue
        await ctx.send("❌ Favor tidak ditemukan.")

    @favor.command(name="remove")
    async def favor_remove(self, ctx, *, faction: str):
        rows = get_recent("0", "0", "favor", 50)
        for r in rows:
            try:
                f = json.loads(r["value"])
                if f["faction"].lower() == faction.lower():
                    f["notes"] = "(deleted)"
                    save_memory("0", "0", ctx.author.id, "favor", json.dumps(f), {"faction": f["faction"]})
                    log_event("0", "0", ctx.author.id,
                              code=f"FAVOR_REMOVE_{f['faction'].upper()}",
                              title=f"🗑️ Favor dihapus: {f['faction']}",
                              details="Favor entry dihapus",
                              etype="favor_remove",
                              actors=[f["faction"]],
                              tags=["favor","remove"])
                    return await ctx.send(f"🗑️ Favor untuk **{f['faction']}** dihapus.")
            except:
                continue
        await ctx.send("❌ Favor tidak ditemukan.")

async def setup(bot):
    await bot.add_cog(Favor(bot))
