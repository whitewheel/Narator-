import discord
from discord.ext import commands
from services import favor_service

class Favor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="favor", invoke_without_command=True)
    async def favor(self, ctx):
        await ctx.send(
            "Gunakan: `!favor add <char> <faction> <value> [notes]`, "
            "`!favor set <char> <faction> <value> [notes]`, "
            "`!favor mod <char> <faction> <delta> [notes]`, "
            "`!favor show <char>`, "
            "`!favor detail <char> <faction>`, "
            "`!favor remove <char> <faction>`, "
            "`!favor factions <char>`, "
            "`!favor gmshow`"
        )

    # ---------- Basic CRUD ----------
    @favor.command(name="add")
    async def favor_add(self, ctx, char_name: str, faction: str, value: int, *, notes: str = ""):
        msg = await favor_service.add_or_set_favor(ctx.guild.id, char_name, faction, value, notes)
        await ctx.send(msg)

    @favor.command(name="set")
    async def favor_set(self, ctx, char_name: str, faction: str, value: int, *, notes: str = ""):
        """Set nilai favor ke angka tertentu"""
        guild_id = ctx.guild.id
        msg = await favor_service.add_or_set_favor(guild_id, char_name, faction, value, notes)
        await ctx.send(msg)

    @favor.command(name="mod")
    async def favor_mod(self, ctx, char_name: str, faction: str, delta: int, *, notes: str = ""):
        msg = await favor_service.mod_favor(ctx.guild.id, char_name, faction, delta, notes)
        await ctx.send(msg)

    @favor.command(name="remove")
    async def favor_remove(self, ctx, char_name: str, faction: str):
        msg = await favor_service.remove_favor(ctx.guild.id, char_name, faction)
        await ctx.send(msg)

    # ---------- Player View ----------
    @favor.command(name="show")
    async def favor_show(self, ctx, *, char_name: str):
        rows = await favor_service.list_favors(ctx.guild.id, char_name=char_name)
        if not rows:
            return await ctx.send(f"❌ Tidak ada data favor untuk {char_name}.")
        embed = discord.Embed(
            title=f"💠 Favor {char_name}",
            color=discord.Color.orange()
        )
        for r in rows:
            status = favor_service.favor_status(r["favor"])
            embed.add_field(
                name=f"{r['faction']}",
                value=f"Nilai: {r['favor']} → {status}\nCatatan: {r.get('notes','-')}",
                inline=False
            )
        await ctx.send(embed=embed)

    @favor.command(name="detail")
    async def favor_detail(self, ctx, char_name: str, faction: str):
        f = await favor_service.get_detail(ctx.guild.id, faction, char_name=char_name)
        if not f:
            return await ctx.send("❌ Favor tidak ditemukan.")
        status = favor_service.favor_status(f["favor"])
        embed = discord.Embed(
            title=f"💠 Favor {char_name}:{f['faction']}",
            description=f"Nilai: `{f['favor']}` → {status}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Catatan", value=f.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    @favor.command(name="factions")
    async def favor_factions(self, ctx, *, char_name: str):
        factions = [
            "ArthaDyne", "PetraCore", "BlueWave", "Aether Mining",
            "Mutarians", "FreeRunners", "Dustborn", "Black Lotus Syndicate", "Khaj"
        ]
        rows = await favor_service.list_factions_status(ctx.guild.id, char_name, factions)
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
        rows = await favor_service.list_all_favors(ctx.guild.id)
        if not rows:
            return await ctx.send("📭 Tidak ada data favor sama sekali.")
        embed = discord.Embed(
            title="💠 Semua Favor Karakter",
            color=discord.Color.dark_gold()
        )
        for r in rows:
            status = favor_service.favor_status(r["favor"])
            embed.add_field(
                name=f"{r['faction']} ({r['char_name']})",
                value=f"Nilai: {r['favor']} → {status}\nCatatan: {r.get('notes','-')}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Favor(bot))

