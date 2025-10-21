import discord
from discord.ext import commands
from services import inventory_service, item_service
from utils.db import fetchone, fetchall
import math

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="inv", invoke_without_command=True)
    async def inv_group(self, ctx):
        await ctx.send(
            "Gunakan: `!inv add`, `!inv remove`, `!inv drop`, `!inv clear`, "
            "`!inv show`, `!inv transfer`, `!inv meta`, `!inv use`, `!inv recalc_all`"
        )

    # === Tambah item ===
    @inv_group.command(name="add")
    async def inv_add(self, ctx, owner: str, item: str, qty: int = 1, *meta_pairs):
        guild_id = ctx.guild.id
        metadata = {}
        for p in meta_pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                metadata[k.strip()] = v.strip()

        ok = inventory_service.add_item(
            guild_id, owner, item, qty,
            metadata=metadata, user_id=str(ctx.author.id)
        )
        if not ok:
            return await ctx.send(
                f"❌ {owner} tidak sanggup membawa {qty}x **{item}** "
                f"(melebihi kapasitas)."
            )

        await ctx.send(f"📦 {qty}x **{item}** ditambahkan ke inventory {owner}.")

    # === Hapus item ===
    @inv_group.command(name="remove")
    async def inv_remove(self, ctx, owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        ok = inventory_service.remove_item(guild_id, owner, item, qty, user_id=str(ctx.author.id))
        if ok:
            await ctx.send(f"🗑️ {qty}x **{item}** dihapus dari inventory {owner}.")
        else:
            await ctx.send(f"❌ {owner} tidak punya cukup {item}.")

    # === Drop item ===
    @inv_group.command(name="drop")
    async def inv_drop(self, ctx, owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        ok = inventory_service.remove_item(guild_id, owner, item, qty, user_id=str(ctx.author.id))
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

        for it in items:
            inventory_service.remove_item(guild_id, owner, it["item"], it["qty"], user_id=str(ctx.author.id))

        await ctx.send(f"🧹 Semua item di inventory **{owner}** telah dibersihkan.")

    # === Lihat inventory dengan pagination ===
    @inv_group.command(name="show")
    async def inv_show(self, ctx, owner: str = "party"):
        guild_id = ctx.guild.id
        items = inventory_service.get_inventory(guild_id, owner)
        if not items:
            return await ctx.send(f"ℹ️ Inventory {owner} kosong.")

        # cek carry
        char = fetchone(guild_id, "SELECT carry_capacity, carry_used FROM characters WHERE name=?", (owner,))
        carry_desc = None
        if char:
            cap = char.get("carry_capacity", 0) or 0
            used = char.get("carry_used", 0) or 0
            carry_desc = f"⚖️ Carry: **{used:.1f} / {cap:.1f}**\n-----------------------"

        # fungsi buat bikin embed per page
        def make_page(page_idx: int):
            start = page_idx * 3
            end = start + 3
            subset = items[start:end]

            embed = discord.Embed(
                title=f"🎒 Inventory: {owner} (Page {page_idx+1}/{math.ceil(len(items)/5)})",
                color=discord.Color.gold()
            )
            if carry_desc:
                embed.description = carry_desc

            item_lines = []
            for it in subset:
                item = item_service.get_item(guild_id, it["item"])
                icon = item.get("icon", "📦") if item else "📦"
                effect = item.get("effect", "-") if item else "-"
                drawback = item.get("drawback", "") if item else ""
                cost = item.get("cost", "") if item else ""
                rules = item.get("rules", "") if item else ""

                desc = f"{icon} {it['item']} x{it['qty']}\n✨ {effect}"
                if drawback:
                    desc += f"\n☠️ {drawback}"
                if cost:
                    desc += f"\n⚡ {cost}"
                if rules:
                    desc += f"\n📘 {rules}"

                item_lines.append(desc)

            embed.add_field(name="Items", value="\n\n".join(item_lines), inline=False)
            return embed

        # buat view pagination
        class InvView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)  # auto-expire 2 menit
                self.page = 0
                self.msg = None

            async def update_page(self, interaction: discord.Interaction):
                await interaction.response.edit_message(embed=make_page(self.page), view=self)

            @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
            async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page > 0:
                    self.page -= 1
                    await self.update_page(interaction)
                else:
                    await interaction.response.defer()

            @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
            async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if (self.page + 1) * 5 < len(items):
                    self.page += 1
                    await self.update_page(interaction)
                else:
                    await interaction.response.defer()

            @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger)
            async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()

        view = InvView()
        await ctx.send(embed=make_page(0), view=view)

    # === Transfer item ===
    @inv_group.command(name="transfer")
    async def inv_transfer(self, ctx, from_owner: str, to_owner: str, item: str, qty: int = 1):
        guild_id = ctx.guild.id
        ok = inventory_service.transfer_item(guild_id, from_owner, to_owner, item, qty, user_id=str(ctx.author.id))
        if ok:
            await ctx.send(f"🔄 {qty}x **{item}** dipindahkan dari {from_owner} → {to_owner}.")
        else:
            await ctx.send(f"❌ Transfer gagal. {to_owner} mungkin kelebihan beban atau item tidak cukup.")

    # === Update metadata ===
    @inv_group.command(name="meta")
    async def inv_meta(self, ctx, owner: str, item: str, *pairs):
        guild_id = ctx.guild.id
        metadata = {}
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                metadata[k.strip()] = v.strip()

        ok = inventory_service.update_metadata(guild_id, owner, item, metadata, user_id=str(ctx.author.id))
        if ok:
            await ctx.send(f"📝 Metadata {item} diupdate: {metadata}")
        else:
            await ctx.send(f"❌ Item {item} milik {owner} tidak ditemukan.")

    # === Gunakan item (consumable) ===
    @inv_group.command(name="use")
    async def inv_use(self, ctx, owner: str, *, item_name: str):
        guild_id = ctx.guild.id

        i = item_service.get_item(guild_id, item_name)
        if not i:
            return await ctx.send(f"❌ Item **{item_name}** tidak ditemukan di katalog.")

        inv = inventory_service.get_inventory(guild_id, owner)
        entry = next((it for it in inv if it["item"].lower() == item_name.lower()), None)
        if not entry or entry["qty"] <= 0:
            return await ctx.send(f"❌ {owner} tidak punya item {item_name}.")

        ok = inventory_service.remove_item(guild_id, owner, item_name, 1, user_id=str(ctx.author.id))
        if not ok:
            return await ctx.send(f"❌ Gagal mengurangi {item_name} dari {owner}.")

        effect = i.get("effect", "-")
        drawback = i.get("drawback", "")
        cost = i.get("cost", "")
        rules = i.get("rules", "")
        result_lines = []

        if rules:
            for rule in rules.split(";"):
                r = rule.strip()
                if not r:
                    continue
                if r.startswith("+") or r.startswith("-"):
                    if "HP" in r.upper():
                        import re
                        amount = int(re.findall(r"[+-]?[0-9]+", r)[0])
                        if "+" in r:
                            result_lines.append(f"❤️ {owner} dipulihkan {amount} HP.")
                        else:
                            result_lines.append(f"💥 {owner} menerima {abs(amount)} damage.")
                elif r.lower().startswith("gold:"):
                    val = int(r.split(":")[1])
                    result_lines.append(f"💰 {owner} gold berubah {val:+d}.")
                elif r.lower().startswith("xp:"):
                    val = int(r.split(":")[1])
                    result_lines.append(f"⭐ {owner} XP bertambah {val}.")
                elif r.lower().startswith("quest:"):
                    result_lines.append(f"📜 Quest event: {r.split(':',1)[1]}")
                elif r.lower().startswith("favor:"):
                    result_lines.append(f"🤝 Favor event: {r.split(':',1)[1]}")
                elif r.lower().startswith("scene:"):
                    result_lines.append(f"🌍 Scene event: {r.split(':',1)[1]}")
                elif r.lower().startswith("npc:"):
                    result_lines.append(f"👤 NPC event: {r.split(':',1)[1]}")
                elif r.lower().startswith("gm:"):
                    result_lines.append(f"🎙️ GM event: {r.split(':',1)[1]}")

        narasi = f"✨ **{owner}** menggunakan **{i['name']}**. {effect}"
        embed = discord.Embed(
            title=f"🎒 {owner} menggunakan item!",
            description=narasi,
            color=discord.Color.green()
        )

        detail_lines = []
        if drawback:
            detail_lines.append(f"☠️ {drawback}")
        if cost:
            detail_lines.append(f"⚡ {cost}")
        if rules:
            detail_lines.append(f"📘 {rules}")

        if detail_lines:
            embed.add_field(name="📖 Detail Item", value="\n".join(detail_lines), inline=False)

        if result_lines:
            embed.add_field(name="⚙️ Efek Mekanik", value="\n".join(result_lines), inline=False)

        await ctx.send(embed=embed)

    # === Recalculate carry semua karakter ===
    @inv_group.command(name="recalc_all")
    async def inv_recalc_all(self, ctx):
        guild_id = ctx.guild.id
        chars = fetchall(guild_id, "SELECT name, carry_capacity FROM characters")
        if not chars:
            return await ctx.send("ℹ️ Belum ada karakter.")

        lines = []
        for c in chars:
            if c["name"].lower() == "party":
                continue
            total = inventory_service.calc_carry(guild_id, c["name"])
            cap = c.get("carry_capacity", 0)
            lines.append(f"⚖️ {c['name']}: {total:.1f} / {cap:.1f}")

        await ctx.send("\n".join(lines))


async def setup(bot):
    await bot.add_cog(Inventory(bot))
