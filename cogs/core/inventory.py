import discord
from discord.ext import commands
from services import inventory_service

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="inv", invoke_without_command=True)
    async def inv_group(self, ctx):
        await ctx.send("Gunakan: `!inv add`, `!inv remove`, `!inv show`, `!inv transfer`, `!inv meta`")

    # === Tambah item ===
    @inv_group.command(name="add")
    async def inv_add(self, ctx, owner: str, item: str, qty: int = 1):
        await inventory_service.add_item(owner, item, qty)
        await ctx.send(f"📦 {qty}x **{item}** ditambahkan ke inventory {owner}.")

    # === Hapus item ===
    @inv_group.command(name="remove")
    async def inv_remove(self, ctx, owner: str, item: str, qty: int = 1):
        ok = await inventory_service.remove_item(owner, item, qty)
        if ok:
            await ctx.send(f"🗑️ {qty}x **{item}** dihapus dari inventory {owner}.")
        else:
            await ctx.send(f"❌ {owner} tidak punya cukup {item}.")

    # === Lihat inventory ===
    @inv_group.command(name="show")
    async def inv_show(self, ctx, owner: str = "party"):
        items = await inventory_service.get_inventory(owner)
        if not items:
            return await ctx.send(f"ℹ️ Inventory {owner} kosong.")

        embed = discord.Embed(
            title=f"🎒 Inventory: {owner}",
            color=discord.Color.gold()
        )
        for it in items:
            meta = it["meta"]
            meta_line = ", ".join([f"{k}: {v}" for k, v in meta.items()]) if meta else "-"
            embed.add_field(
                name=f"{it['item']} x{it['qty']}",
                value=meta_line,
                inline=False
            )
        await ctx.send(embed=embed)

    # === Transfer item ===
    @inv_group.command(name="transfer")
    async def inv_transfer(self, ctx, from_owner: str, to_owner: str, item: str, qty: int = 1):
        ok = await inventory_service.transfer_item(from_owner, to_owner, item, qty)
        if ok:
            await ctx.send(f"🔄 {qty}x **{item}** dipindahkan dari {from_owner} → {to_owner}.")
        else:
            await ctx.send(f"❌ Gagal transfer, cek item/qty.")

    # === Update metadata ===
    @inv_group.command(name="meta")
    async def inv_meta(self, ctx, owner: str, item: str, *pairs):
        """Update metadata item. Contoh: !inv meta Alice Sword rarity=epic note='cursed blade'"""
        metadata = {}
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                metadata[k.strip()] = v.strip()

        ok = await inventory_service.update_metadata(owner, item, metadata)
        if ok:
            await ctx.send(f"📝 Metadata {item} diupdate: {metadata}")
        else:
            await ctx.send(f"❌ Item {item} milik {owner} tidak ditemukan.")


async def setup(bot):
    await bot.add_cog(Inventory(bot))
