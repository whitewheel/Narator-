# cogs/world/faction.py
import discord
from discord.ext import commands
from services import faction_service

FACTION_ICONS = {
    "city": "🏙️",
    "region": "🏞️",
    "corp": "🏢",
    "gang": "🏴‍☠️",
    "military": "⚔️",
    "science": "🧪",
    "frontier": "🌌",
    "general": "🏷️",
}

class Faction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="faction", invoke_without_command=True)
    async def faction(self, ctx):
        await ctx.send("Gunakan: `!faction add|list|detail|remove|hide|show|gmshow`")

    @faction.command(name="add")
    async def faction_add(self, ctx, *, entry: str):
        """Tambah faction baru. Format: Nama | Deskripsi | [Type]"""
        guild_id = ctx.guild.id
        parts = [p.strip() for p in entry.split("|")]
        if len(parts) < 1:
            return await ctx.send("⚠️ Format: `!faction add Nama | Deskripsi | [Type]`")
        name = parts[0]
        desc = parts[1] if len(parts) > 1 else ""
        ftype = parts[2].lower() if len(parts) > 2 else "general"
        msg = faction_service.add_faction(guild_id, name, desc, ftype, hidden=0)
        await ctx.send(msg)

    @faction.command(name="list")
    async def faction_list(self, ctx):
        """List semua faction visible"""
        guild_id = ctx.guild.id
        rows = faction_service.list_factions(guild_id, include_hidden=False)
        if not rows:
            return await ctx.send("❌ Tidak ada faction.")
        embed = discord.Embed(
            title="🏷️ Daftar Factions",
            description="Faction yang diketahui publik.",
            color=discord.Color.blue()
        )
        for r in rows:
            icon = FACTION_ICONS.get(r.get("type","general"), "🏷️")
            embed.add_field(
                name=f"{icon} **{r['name']}**",
                value=r.get("desc","-"),
                inline=False
            )
        await ctx.send(embed=embed)

    @faction.command(name="gmshow")
    async def faction_gmshow(self, ctx):
        """List semua faction termasuk hidden"""
        guild_id = ctx.guild.id
        rows = faction_service.list_factions(guild_id, include_hidden=True)
        if not rows:
            return await ctx.send("❌ Tidak ada faction.")
        embed = discord.Embed(
            title="🏷️ [GM] Daftar Semua Factions",
            description="Termasuk faction yang disembunyikan.",
            color=discord.Color.purple()
        )
        for r in rows:
            status = "🙈 Hidden" if r.get("hidden",0) == 1 else "👁️ Visible"
            icon = FACTION_ICONS.get(r.get("type","general"), "🏷️")
            embed.add_field(
                name=f"{icon} **{r['name']}** ({status})",
                value=r.get("desc","-"),
                inline=False
            )
        await ctx.send(embed=embed)

    @faction.command(name="detail")
    async def faction_detail(self, ctx, *, name: str):
        """Detail 1 faction"""
        guild_id = ctx.guild.id
        f = faction_service.get_faction(guild_id, name)
        if not f:
            return await ctx.send("❌ Faction tidak ditemukan.")
        status = "🙈 Hidden" if f.get("hidden",0) == 1 else "👁️ Visible"
        icon = FACTION_ICONS.get(f.get("type","general"), "🏷️")
        embed = discord.Embed(
            title=f"{icon} Faction: {f['name']}",
            description=f.get("desc","-"),
            color=discord.Color.gold()
        )
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Type", value=f.get("type","general"), inline=True)
        await ctx.send(embed=embed)

    @faction.command(name="remove")
    async def faction_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.remove_faction(guild_id, name)
        await ctx.send(msg)

    @faction.command(name="hide")
    async def faction_hide(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.hide_faction(guild_id, name, hidden=1)
        await ctx.send(msg)

    @faction.command(name="show")
    async def faction_show(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.hide_faction(guild_id, name, hidden=0)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Faction(bot))
