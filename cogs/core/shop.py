import discord
from discord.ext import commands
from services import shop_service, item_service, npc_service, inventory_service, status_service, favor_service, quest_service
from utils.db import fetchone, fetchall

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==== Base ====
    @commands.group(name="shop", invoke_without_command=True)
    async def shop_group(self, ctx):
        await ctx.send(
            "Gunakan: `!shop list <NPC>`, `!shop gmlist`, `!shop add <NPC> <Item> <Harga> [Stock]`, "
            "`!shop edit <NPC> <Item> | price=.. stock=..`, `!shop restock <NPC> <Item> <Jumlah>`, "
            "`!shop remove <NPC> <Item>`, `!shop clear <NPC>`, "
            "`!shop lock <NPC>`, `!shop unlock <NPC>`, "
            "`!shop buy <NPC> <Karakter> <Item> [Qty]`"
        )

    # ==== Lihat dagangan (player) ====
    @shop_group.command(name="list")
    async def shop_list(self, ctx, npc_name: str, char_name: str = None):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        rows = await shop_service.list_items(guild_id, npc_name, char_name)
        embed = discord.Embed(
            title=f"🛒 Dagangan {npc_name}",
            color=discord.Color.green()
        )
        for line in rows:
            embed.add_field(name="─", value=line, inline=False)
        await ctx.send(embed=embed)

    # ==== GM lihat semua shop ====
    @shop_group.command(name="gmlist")
    @commands.has_permissions(administrator=True)
    async def shop_gmlist(self, ctx):
        guild_id = ctx.guild.id
        rows = fetchall(guild_id, "SELECT * FROM npc_shop ORDER BY npc_name, item")
        if not rows:
            return await ctx.send("📭 Tidak ada shop terdaftar.")
        embed = discord.Embed(title="🛒 [GM] Semua NPC Shop", color=discord.Color.purple())
        for r in rows:
            embed.add_field(
                name=f"{r['npc_name']} — {r['item']}",
                value=f"💰 {r['price']} | Stock {r['stock']} | FavorReq {r['favor_req']} | QuestReq {r['quest_req']}",
                inline=False
            )
        await ctx.send(embed=embed)

    # ==== Tambah item ke dagangan ====
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
        await ctx.send(f"✅ {npc_name} sekarang menjual {item} seharga {price} gold (stock {stock if stock>=0 else '∞'}).")

    # ==== Edit item (harga/stock) ====
    @shop_group.command(name="edit")
    async def shop_edit(self, ctx, npc_name: str, item: str, *, spec: str):
        guild_id = ctx.guild.id
        kv = {}
        for part in spec.split():
            if "=" in part:
                k, v = part.split("=", 1)
                kv[k.lower()] = v
        price = int(kv["price"]) if "price" in kv else None
        stock = int(kv["stock"]) if "stock" in kv else None
        msg = shop_service.edit_item(guild_id, npc_name, item, price, stock)
        await ctx.send(msg)

    # ==== Restock ====
    @shop_group.command(name="restock")
    async def shop_restock(self, ctx, npc_name: str, item: str, amount: int):
        guild_id = ctx.guild.id
        msg = shop_service.restock_item(guild_id, npc_name, item, amount)
        await ctx.send(msg)

    # ==== Hapus item dari dagangan ====
    @shop_group.command(name="remove")
    async def shop_remove(self, ctx, npc_name: str, item: str):
        guild_id = ctx.guild.id
        shop_service.remove_item(guild_id, npc_name, item)
        await ctx.send(f"🗑️ {item} dihapus dari dagangan {npc_name}.")

    # ==== Clear semua dagangan ====
    @shop_group.command(name="clear")
    async def shop_clear(self, ctx, npc_name: str):
        guild_id = ctx.guild.id
        shop_service.clear_shop(guild_id, npc_name)
        await ctx.send(f"🧹 Semua dagangan {npc_name} dihapus.")

    # ==== Lock / Unlock Shop ====
    @shop_group.command(name="lock")
    async def shop_lock(self, ctx, npc_name: str):
        guild_id = ctx.guild.id
        shop_service.lock_shop(guild_id, npc_name, True)
        await ctx.send(f"🔒 Shop {npc_name} dikunci.")

    @shop_group.command(name="unlock")
    async def shop_unlock(self, ctx, npc_name: str):
        guild_id = ctx.guild.id
        shop_service.lock_shop(guild_id, npc_name, False)
        await ctx.send(f"🔓 Shop {npc_name} dibuka.")

    # ==== Beli item ====
    @shop_group.command(name="buy")
    async def shop_buy(self, ctx, npc_name: str, char_name: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id

        npc = npc_service.get_npc(guild_id, npc_name)
        if not npc:
            return await ctx.send(f"❌ NPC {npc_name} tidak ditemukan.")

        ok, msg = await shop_service.buy_item(guild_id, npc_name, char_name, item, qty, ctx.author.id)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Shop(bot))
