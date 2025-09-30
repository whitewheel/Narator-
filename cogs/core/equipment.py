import discord
from discord.ext import commands
from services import equipment_service

# List slot valid, biar gampang ditampilkan ke user
VALID_SLOTS = [
    "main_hand", "off_hand",
    "armor_inner", "armor_outer",
    "accessory1", "accessory2", "accessory3",
    "augment1", "augment2", "augment3",
]

class Equipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="equip", invoke_without_command=True)
    async def equip_group(self, ctx):
        await ctx.send(
            "🧰 **Equipment Commands**\n"
            "• `!equip set <char> <slot> <item>` → pasang item\n"
            "• `!equip remove <char> <slot>` → lepas item\n"
            "• `!equip show <char>` → lihat semua slot\n\n"
            f"Slot valid: `{', '.join(VALID_SLOTS)}`"
        )

    # === Pasang item ===
    @equip_group.command(name="set")
    async def equip_set(self, ctx, char: str, slot: str, *, item: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.equip_item(
            guild_id, char, slot, item, user_id=str(ctx.author.id)
        )

        embed = discord.Embed(
            title="⚔️ Equip Item" if ok else "❌ Equip Gagal",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red()
        )
        await ctx.send(embed=embed)

    # === Lepas item ===
    @equip_group.command(name="remove")
    async def equip_remove(self, ctx, char: str, slot: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.unequip_item(
            guild_id, char, slot, user_id=str(ctx.author.id)
        )

        embed = discord.Embed(
            title="🛑 Unequip Item" if ok else "❌ Unequip Gagal",
            description=msg,
            color=discord.Color.orange() if ok else discord.Color.red()
        )
        await ctx.send(embed=embed)

    # === Lihat semua slot ===
    @equip_group.command(name="show")
    async def equip_show(self, ctx, char: str):
        guild_id = ctx.guild.id
        eq_list = equipment_service.show_equipment(guild_id, char)
        if not eq_list:
            return await ctx.send(f"❌ Karakter **{char}** tidak ditemukan.")

        embed = discord.Embed(
            title=f"🧰 Equipment {char}",
            description="\n".join(eq_list),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Equipment(bot))
