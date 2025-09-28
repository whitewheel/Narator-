# cogs/equipment.py
import discord
from discord.ext import commands
from services import equipment_service

class Equipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="equip", invoke_without_command=True)
    async def equip_group(self, ctx):
        await ctx.send(
            "Gunakan: `!equip set <char> <slot> <item>`, "
            "`!equip remove <char> <slot>`, "
            "`!equip show <char>`"
        )

    # === Pasang item ===
    @equip_group.command(name="set")
    async def equip_set(self, ctx, char: str, slot: str, *, item: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.equip_item(
            guild_id, char, slot, item, user_id=str(ctx.author.id)
        )
        await ctx.send(msg)

    # === Lepas item ===
    @equip_group.command(name="remove")
    async def equip_remove(self, ctx, char: str, slot: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.unequip_item(
            guild_id, char, slot, user_id=str(ctx.author.id)
        )
        await ctx.send(msg)

    # === Lihat semua slot ===
    @equip_group.command(name="show")
    async def equip_show(self, ctx, char: str):
        guild_id = ctx.guild.id
        eq_list = equipment_service.show_equipment(guild_id, char)
        if not eq_list:
            return await ctx.send(f"❌ Karakter {char} tidak ditemukan.")

        embed = discord.Embed(
            title=f"🧰 Equipment {char}",
            color=discord.Color.blue()
        )
        embed.description = "\n".join(eq_list)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Equipment(bot))
