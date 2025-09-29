# cogs/core/shop.py
import discord
from discord.ext import commands
from services import shop_service, item_service, npc_service
from utils.db import fetchone

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==== Base ====
    @commands.group(name="shop", invoke_without_command=True)
    async def shop_group(self, ctx):
        await ctx.send(
            "Gunakan: `!shop gmlist <NPC>`, `!shop add <NPC> <Item> <Harga> [Stock]`, "
            "`!shop remove <NPC> <Item>`, `!shop clear <NPC>`, "
            "`!shop buy <NPC> <Karakter> <Item> [Qty]`, "
            "`!shop unlock <NPC> <Item> [favor=<Faction>:<Val>] [quest=<Quest>]`"
        )

    # ==== GM List (full detail) ====
    @shop_group.command(name="gmlist")
    @commands.has_permissions(administrator=True)
    async def shop_gmlist(self, ctx, npc_name: str):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        rows = shop_service.list_items(guild_id, npc_name, gm_view=True)
        embed = discord.Embed(
            title=f"🛒 [GM] Dagangan {npc_name}",
            color=discord.Color.dark_gold()
        )
        for line in rows:
            embed.add_field(name="─", value=line, inline=False)

        await ctx.send(embed=embed)

    # ==== Lihat dagangan (player) ====
    @shop_group.command(name="list")
    async def shop_list(self, ctx, npc_name: str, char_name: str = None):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        rows = shop_service.list_items(guild_id, npc_name, char_name=char_name)
        embed = discord.Embed(
            title=f"🛒 Dagangan {npc_name}",
            color=discord.Color.green()
        )
        for line in rows:
            embed.add_field(name="─", value=line, inline=False)

        await ctx.send(embed=embed)

    # ==== Tambah item ====
    @shop_group.command(name="add")
    async def shop_add(self, ctx, npc_name: str, item: str, price: int, stock: int = -1):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan. Tambahkan dulu dengan `!npc add`.")

        it = item_service.get_item(guild_id, item)
        if not it:
            return await ctx.send(f"❌ Item {item} tidak ada di katalog. Tambahkan dulu dengan `!item add`.")

        shop_service.add_item(guild_id, npc_name, item, price, stock)
        await ctx.send(
            f"✅ {npc_name} sekarang menjual {item} seharga {price} gold "
            f"(stock {stock if stock>=0 else '∞'})."
        )

    # ==== Hapus item ====
    @shop_group.command(name="remove")
    async def shop_remove(self, ctx, npc_name: str, item: str):
        guild_id = ctx.guild.id
        shop_service.remove_item(guild_id, npc_name, item)
        await ctx.send(f"🗑️ {item} dihapus dari dagangan {npc_name}.")

    # ==== Clear dagangan ====
    @shop_group.command(name="clear")
    async def shop_clear(self, ctx, npc_name: str):
        guild_id = ctx.guild.id
        shop_service.clear_items(guild_id, npc_name)
        await ctx.send(f"🗑️ Semua dagangan {npc_name} dihapus.")

    # ==== Beli item ====
    @shop_group.command(name="buy")
    async def shop_buy(self, ctx, npc_name: str, char_name: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        ok, msg = shop_service.buy_item(guild_id, npc_name, char_name, item, qty)
        await ctx.send(msg)

    # ==== Lock/unlock item (favor / quest req) ====
    @shop_group.command(name="unlock")
    async def shop_unlock(self, ctx, npc_name: str, item: str, *, reqs: str = ""):
        guild_id = ctx.guild.id
        favor_req, quest_req = {}, []

        for part in reqs.split():
            if part.lower().startswith("favor="):
                try:
                    fac, val = part.split("=", 1)[1].split(":")
                    favor_req[fac.strip()] = int(val.strip())
                except:
                    pass
            elif part.lower().startswith("quest="):
                quest_req.append(part.split("=", 1)[1].strip())

        shop_service.add_item(
            guild_id, npc_name, item,
            price=0, stock=0,
            favor_req=favor_req, quest_req=quest_req
        )
        await ctx.send(
            f"🔒 {item} di {npc_name} sekarang terkunci. "
            f"Syarat: {favor_req if favor_req else ''} {quest_req if quest_req else ''}"
        )

async def setup(bot):
    await bot.add_cog(Shop(bot))
