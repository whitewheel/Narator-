# cogs/world/faction.py
import discord
from discord.ext import commands
from services import faction_service

class Faction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="faction", invoke_without_command=True)
    async def faction(self, ctx):
        await ctx.send(
            "Gunakan: \n"
            "`!faction add <Nama> [Deskripsi]`\n"
            "`!faction list [all]`\n"
            "`!faction detail <Nama>`\n"
            "`!faction hide <Nama> [on/off]`\n"
            "`!faction remove <Nama>`"
        )

    @faction.command(name="add")
    async def faction_add(self, ctx, name: str, *, desc: str = ""):
        guild_id = ctx.guild.id
        msg = faction_service.add_faction(guild_id, name, desc)
        await ctx.send(msg)

    @faction.command(name="list")
    async def faction_list(self, ctx, show_hidden: str = "no"):
        guild_id = ctx.guild.id
        include_hidden = show_hidden.lower() in ("yes", "true", "1", "all")
        rows = faction_service.list_factions(guild_id, include_hidden)
        if not rows:
            return await ctx.send("❌ Belum ada faction terdaftar.")
        embed = discord.Embed(
            title="📜 Daftar Factions",
            color=discord.Color.gold()
        )
        for r in rows:
            hidden_mark = " 🙈" if r.get("hidden", 0) else ""
            embed.add_field(
                name=f"{r['name']}{hidden_mark}",
                value=r.get("desc", "-") or "-",
                inline=False
            )
        await ctx.send(embed=embed)

    @faction.command(name="detail")
    async def faction_detail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        f = faction_service.get_faction(guild_id, name)
        if not f:
            return await ctx.send("❌ Faction tidak ditemukan.")
        embed = discord.Embed(
            title=f"🏷️ {f['name']}",
            description=f.get("desc", "-"),
            color=discord.Color.gold()
        )
        if f.get("hidden", 0):
            embed.set_footer(text="🙈 Hidden Faction")
        await ctx.send(embed=embed)

    @faction.command(name="remove")
    async def faction_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.remove_faction(guild_id, name)
        await ctx.send(msg)

    @faction.command(name="hide")
    async def faction_hide(self, ctx, name: str, mode: str = "on"):
        guild_id = ctx.guild.id
        hidden = 1 if mode.lower() in ("on", "yes", "true", "1") else 0
        msg = faction_service.hide_faction(guild_id, name, hidden)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Faction(bot))
