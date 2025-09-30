import discord
from discord.ext import commands
from utils.db import execute

class GMTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === Wipe Inventory Karakter ===
    @commands.command(name="inv_wipe")
    @commands.has_permissions(administrator=True)  # biar cuma admin/GM bisa pakai
    async def inv_wipe(self, ctx, char: str):
        guild_id = ctx.guild.id
        execute(guild_id, "DELETE FROM inventory WHERE LOWER(owner)=LOWER(?)", (char,))
        await ctx.send(f"🧹 Semua inventory milik **{char}** sudah dihapus total (wipe).")

    # === Clear Equipment Karakter (kosongin semua slot) ===
    @commands.command(name="equip_clear")
    @commands.has_permissions(administrator=True)
    async def equip_clear(self, ctx, char: str):
        import json
        from services.equipment_service import SLOTS
        eq = {s: "" for s in SLOTS}
        guild_id = ctx.guild.id
        execute(
            guild_id,
            "UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE LOWER(name)=LOWER(?)",
            (json.dumps(eq), char)
        )
        await ctx.send(f"🛑 Semua slot equipment **{char}** sudah dikosongkan.")

async def setup(bot):
    await bot.add_cog(GMTools(bot))
