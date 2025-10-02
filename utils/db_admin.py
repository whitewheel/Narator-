import discord
from discord.ext import commands
from utils import db

class DBAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="db", invoke_without_command=True)
    async def db_group(self, ctx):
        await ctx.send("Gunakan: `!db checkschema` atau `!db resettable <nama>`")

    @db_group.command(name="checkschema")
    @commands.has_permissions(administrator=True)
    async def db_checkschema(self, ctx):
        guild_id = ctx.guild.id
        schema = db.check_schema(guild_id)
        msg = "\n".join([f"**{t}**: {', '.join(cols)}" for t, cols in schema.items()])
        await ctx.send(f"📊 Schema DB untuk guild ini:\n{msg}")

async def setup(bot):
    await bot.add_cog(DBAdmin(bot))
