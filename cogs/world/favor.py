import discord
from discord.ext import commands
from services import favor_service

class Favor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="favor", invoke_without_command=True)
    async def favor(self, ctx):
        await ctx.send("Gunakan: `!favor add`, `!favor set`, `!favor show`, `!favor detail`, `!favor remove`")

    @favor.command(name="add")
    async def favor_add(self, ctx, faction: str, value: int, *, notes: str = ""):
        guild_id = ctx.guild.id
        favor_service.add_or_set_favor(guild_id, faction, value, notes)
        await ctx.send(f"🪙 Favor **{faction}** diset ke `{value}`. {notes}")

    @favor.command(name="set")
    async def favor_set(self, ctx, faction: str, value: int, *, notes: str = ""):
        await self.favor_add(ctx, faction, value, notes=notes)

    @favor.command(name="show")
    async def favor_show(self, ctx):
        guild_id = ctx.guild.id
        rows = favor_service.list_favor(guild_id)
        if not rows:
            return await ctx.send("Tidak ada data favor.")
        out = [f"🪙 **{r['faction']}** → {r['value']}" for r in rows]
        await ctx.send("\n".join(out))

    @favor.command(name="detail")
    async def favor_detail(self, ctx, *, faction: str):
        guild_id = ctx.guild.id
        f = favor_service.get_favor(guild_id, faction)
        if not f:
            return await ctx.send("❌ Favor tidak ditemukan.")
        embed = discord.Embed(
            title=f"🪙 Favor: {f['faction']}",
            description=f"Nilai: `{f['value']}`",
            color=discord.Color.gold()
        )
        embed.add_field(name="Catatan", value=f.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    @favor.command(name="remove")
    async def favor_remove(self, ctx, *, faction: str):
        guild_id = ctx.guild.id
        ok = favor_service.remove_favor(guild_id, faction)
        if ok:
            await ctx.send(f"🗑️ Favor **{faction}** dihapus.")
        else:
            await ctx.send("❌ Favor tidak ditemukan.")

async def setup(bot):
    await bot.add_cog(Favor(bot))
