import discord
from discord.ext import commands
from services import favor_service

class Favor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="favor", invoke_without_command=True)
    async def favor(self, ctx):
        await ctx.send("Gunakan: `!favor add <Fraksi> <Nilai> [Catatan]`, `!favor set`, `!favor mod`, `!favor show`, `!favor detail`, `!favor remove`")

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
        embed = discord.Embed(
            title=f"🪙 Favor: {f['faction']}",
            description=f"Nilai: `{f['favor']}`",
            color=discord.Color.gold()
        )
        embed.add_field(name="Catatan", value=f.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    @favor.command(name="remove")
    async def favor_remove(self, ctx, *, faction: str):
        guild_id = ctx.guild.id
        msg = await favor_service.remove_favor(guild_id, ctx.author.id, faction)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Favor(bot))
