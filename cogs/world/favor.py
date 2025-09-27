import discord
from discord.ext import commands
from services import favor_service

class Favor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="favor", invoke_without_command=True)
    async def favor(self, ctx):
        await ctx.send("Gunakan: `!favor add`, `!favor set`, `!favor mod`, `!favor show`, `!favor detail`, `!favor remove`, `!favor player <nama>`, `!favor factions [nama]`, `!favor gmshow`")

    # ---------- Basic CRUD ----------
    @favor.command(name="add")
    async def favor_add(self, ctx, faction: str, value: int, *, notes: str = ""):
        guild_id = ctx.guild.id
        msg = await favor_service.add_or_set_favor(guild_id, ctx.author.id, faction, value, notes)
        await ctx.send(msg)

    @favor.command(name="set")
    async def favor_set(self, ctx, faction: str, value: int, *, notes: str = ""):
        await self.favor_add(ctx, faction, value, notes=notes)

    @favor.command(name="mod")
    async def favor_mod(self, ctx, faction: str, delta: int, *, notes: str = ""):
        guild_id = ctx.guild.id
        msg = await favor_service.mod_favor(guild_id, ctx.author.id, faction, delta, notes)
        await ctx.send(msg)

    @favor.command(name="show")
    async def favor_show(self, ctx):
        guild_id = ctx.guild.id
        msg = await favor_service.list_favors(guild_id)
        await ctx.send(msg)

    @favor.command(name="detail")
    async def favor_detail(self, ctx, *, faction: str):
        guild_id = ctx.guild.id
        f = await favor_service.get_detail(guild_id, faction)
        if not f:
            return await ctx.send("❌ Favor tidak ditemukan.")
        status = favor_service.favor_status(f["favor"])
        embed = discord.Embed(
            title=f"💠 Favor: {f['faction']}",
            description=f"Nilai: `{f['favor']}` → {status}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Catatan", value=f.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    @favor.command(name="remove")
    async def favor_remove(self, ctx, *, faction: str):
        guild_id = ctx.guild.id
        msg = await favor_service.remove_favor(guild_id, ctx.author.id, faction)
        await ctx.send(msg)

    # ---------- Player View ----------
    @favor.command(name="player")
    async def favor_player(self, ctx, *, char_name: str):
        guild_id = ctx.guild.id
        rows = await favor_service.list_favors(guild_id, char_name=char_name)
        if not rows:
            return await ctx.send(f"❌ Tidak ada data favor untuk {char_name}.")
        embed = discord.Embed(
            title=f"💠 Favor Player: {char_name}",
            color=discord.Color.blue()
        )
        for r in rows:
            status = favor_service.favor_status(r["favor"])
            embed.add_field(
                name=r["faction"],
                value=f"Nilai: {r['favor']} → {status}\nCatatan: {r.get('notes','-')}",
                inline=False
            )
        await ctx.send(embed=embed)

    @favor.command(name="factions")
    async def favor_factions(self, ctx, *, char_name: str = None):
        guild_id = ctx.guild.id
        if not char_name:
            char_name = ctx.author.display_name
        factions = [
            "ArthaDyne", "PetraCore", "BlueWave", "Aether Mining",
            "Mutarians", "FreeRunners", "Dustborn", "Black Lotus Syndicate"
        ]
        rows = await favor_service.list_factions_status(guild_id, char_name, factions)
        embed = discord.Embed(
            title=f"💠 Favor Factions untuk {char_name}",
            color=discord.Color.purple()
        )
        for fac, val, status in rows:
            embed.add_field(name=fac, value=f"{val} → {status}", inline=False)
        await ctx.send(embed=embed)

    # ---------- GM ----------
    @favor.command(name="gmshow")
    @commands.has_permissions(administrator=True)
    async def favor_gmshow(self, ctx):
        guild_id = ctx.guild.id
        rows = await favor_service.list_all_favors(guild_id)
        if not rows:
            return await ctx.send("📭 Tidak ada data favor sama sekali.")
        embed = discord.Embed(
            title="💠 Semua Favor Player",
            color=discord.Color.dark_gold()
        )
        for r in rows:
            status = favor_service.favor_status(r["favor"])
            embed.add_field(
                name=f"{r['faction']} ({r['user_id']})",
                value=f"Nilai: {r['favor']} → {status}\nCatatan: {r.get('notes','-')}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Favor(bot))
