import discord
from discord.ext import commands
from services import inventory_service

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="inv", invoke_without_command=True)
    async def inv_group(self, ctx):
        await ctx.send("Gunakan: `!inv add`, `!inv remove`, `!inv drop`, `!inv clear`, `!inv show`, `!inv transfer`, `!inv meta`")

    # === Tambah item ===
    @inv_group.command(name="add")
    async def inv_add(self, ctx, owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        inventory_service.add_item(guild_id, owner, item, qty)
        await ctx.send(f"📦 {qty}x **{item}** ditambahkan ke inventory {owner}.")

    # === Hapus item ===
    @inv_group.command(name="remove")
    async def inv_remove(self, ctx, owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        ok = inventory_service.remove_item(guild_id, owner, item, qty)
        if ok:
            await ctx.send(f"🗑️ {qty}x **{item}** dihapus dari inventory {owner}.")
        else:
            await ctx.send(f"❌ {owner} tidak punya cukup {item}.")

    # === Drop item (narasi berbeda) ===
    @inv_group.command(name="drop")
    async def inv_drop(self, ctx, owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        ok = inventory_service.remove_item(guild_id, owner, item, qty)
        if ok:
            await ctx.send(f"📤 {owner} menjatuhkan {qty}x **{item}** ke tanah.")
        else:
            await ctx.send(f"❌ {owner} tidak punya cukup {item} untuk dijatuhkan.")

    # === Clear inventory ===
    @inv_group.command(name="clear")
    async def inv_clear(self, ctx, owner: str):
        guild_id = ctx.guild.id
        items = inventory_service.get_inventory(guild_id, owner)
        if not items:
            return await ctx.send(f"ℹ️ Inventory {owner} sudah kosong.")

        # hapus semua
        for it in items:
            inventory_service.remove_item(guild_id, owner, it["item"], it["qty"])

        await ctx.send(f"🧹 Semua item di inventory **{owner}** telah dibersihkan.")

    # === Lihat inventory ===
    @inv_group.command(name="show")
    async def inv_show(self, ctx, owner: str = "party"):
        guild_id = ctx.guild.id
        items = inventory_service.get_inventory(guild_id, owner)
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
        guild_id = ctx.guild.id
        ok = inventory_service.transfer_item(guild_id, from_owner, to_owner, item, qty)
        if ok:
            await ctx.send(f"🔄 {qty}x **{item}** dipindahkan dari {from_owner} → {to_owner}.")
        else:
            await ctx.send(f"❌ Gagal transfer, cek item/qty.")

    # === Update metadata ===
    @inv_group.command(name="meta")
    async def inv_meta(self, ctx, owner: str, item: str, *pairs):
        guild_id = ctx.guild.id
        metadata = {}
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                metadata[k.strip()] = v.strip()

        ok = inventory_service.update_metadata(guild_id, owner, item, metadata)
        if ok:
            await ctx.send(f"📝 Metadata {item} diupdate: {metadata}")
        else:
            await ctx.send(f"❌ Item {item} milik {owner} tidak ditemukan.")


async def setup(bot):
    await bot.add_cog(Inventory(bot))
