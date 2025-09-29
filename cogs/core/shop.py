# cogs/core/shop.py
import discord
from discord.ext import commands
from services import shop_service, item_service, npc_service, inventory_service, status_service
from utils.db import fetchone

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==== Base ====
    @commands.group(name="shop", invoke_without_command=True)
    async def shop_group(self, ctx):
        await ctx.send("Gunakan: `!shop list <NPC>`, `!shop add <NPC> <Item> <Harga> [Stock]`, "
                       "`!shop remove <NPC> <Item>`, `!shop buy <NPC> <Karakter> <Item> [Qty]`")

    # ==== Lihat dagangan ====
    @shop_group.command(name="list")
    async def shop_list(self, ctx, npc_name: str):
        guild_id = ctx.guild.id

        # cek NPC
        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        rows = shop_service.list_items(guild_id, npc_name)
        embed = discord.Embed(
            title=f"🛒 Dagangan {npc_name}",
            color=discord.Color.green()
        )
        for line in rows:
            embed.add_field(name="─", value=line, inline=False)

        await ctx.send(embed=embed)

    # ==== Tambah item ke dagangan ====
    @shop_group.command(name="add")
    async def shop_add(self, ctx, npc_name: str, item: str, price: int, stock: int = -1):
        guild_id = ctx.guild.id

        # cek NPC
        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan. Tambahkan dulu dengan `!npc add`.")

        # cek item
        it = item_service.get_item(guild_id, item)
        if not it:
            return await ctx.send(f"❌ Item {item} tidak ada di katalog. Tambahkan dulu dengan `!item add`.")

        shop_service.add_item(guild_id, npc_name, item, price, stock)
        await ctx.send(f"✅ {npc_name} sekarang menjual {item} seharga {price} gold (stock {stock if stock>=0 else '∞'}).")

    # ==== Hapus item dari dagangan ====
    @shop_group.command(name="remove")
    async def shop_remove(self, ctx, npc_name: str, item: str):
        guild_id = ctx.guild.id
        shop_service.remove_item(guild_id, npc_name, item)
        await ctx.send(f"🗑️ {item} dihapus dari dagangan {npc_name}.")

    # ==== Beli item ====
    @shop_group.command(name="buy")
    async def shop_buy(self, ctx, npc_name: str, char_name: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id

        # cek NPC
        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        ok, msg = shop_service.buy_item(guild_id, npc_name, char_name, item, qty)
        await ctx.send(msg)

    # ==== [Opsional] Integrasi quest/favor lock ====
    @shop_group.command(name="unlock")
    async def shop_unlock(self, ctx, npc_name: str, item: str, favor: str = None, quest: str = None):
        """Set syarat favor/quest untuk beli item (next step integrasi penuh)."""
        guild_id = ctx.guild.id
        req_favor = {favor: 1} if favor else {}
        req_quest = [quest] if quest else []
        shop_service.add_item(guild_id, npc_name, item, price=0, stock=0,
                              favor_req=req_favor, quest_req=req_quest)
        await ctx.send(f"🔒 {item} di {npc_name} terkunci, butuh favor/quest untuk akses.")

async def setup(bot):
    await bot.add_cog(Shop(bot))
