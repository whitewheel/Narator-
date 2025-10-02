import discord
from discord.ext import commands
from utils import db

class DbAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="db", invoke_without_command=True)
    async def db_group(self, ctx):
        await ctx.send("Gunakan: `!db checkschema` atau `!db resettable <nama>`")

    @db_group.command(name="checkschema")
    async def checkschema(self, ctx):
        """Cek semua tabel + kolom di DB guild ini"""
        guild_id = ctx.guild.id
        schema = db.check_schema(guild_id)
        msg = "📖 Schema DB untuk guild ini:\n"
        for t, cols in schema.items():
            msg += f"**{t}**: {', '.join(cols)}\n"
        await ctx.send(msg[:1990])  # biar aman tidak melebihi limit

    @db_group.command(name="resettable")
    @commands.has_permissions(administrator=True)
    async def resettable(self, ctx, *, table: str):
        """Hapus satu tabel lalu kosongin"""
        guild_id = ctx.guild.id
        try:
            db.execute(guild_id, f"DROP TABLE IF EXISTS {table}")
            await ctx.send(f"✅ Tabel `{table}` sudah dihapus.")
        except Exception as e:
            await ctx.send(f"❌ Gagal drop tabel `{table}`: {e}")

async def setup(bot):
    await bot.add_cog(DbAdmin(bot))
