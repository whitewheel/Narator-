import discord
from discord.ext import commands
from services import item_service
import re
from discord.ui import View, button
from discord import ButtonStyle

# ===========================
# Helper
# ===========================
def safe_field_value(text: str, limit: int = 1024) -> str:
    """Potong string biar nggak lebih dari 1024 char"""
    if not text:
        return "-"
    return text if len(text) <= limit else text[:limit-3] + "..."

def split_long_field(name: str, text: str, limit: int = 1024):
    """Pisahkan field panjang menjadi beberapa bagian (auto-split)"""
    if not text:
        return [(name, "-")]
    chunks = [text[i:i+limit] for i in range(0, len(text), limit)]
    if len(chunks) == 1:
        return [(name, chunks[0])]
    return [(f"{name} (bagian {i+1})", chunk) for i, chunk in enumerate(chunks)]

# ===========================
# Pagination View
# ===========================
class ItemPaginator(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0

    async def update(self, interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="◀", style=ButtonStyle.secondary)
    async def prev_page(self, interaction, button):
        if self.index > 0:
            self.index -= 1
            await self.update(interaction)
        else:
            await interaction.response.defer()

    @button(label="▶", style=ButtonStyle.secondary)
    async def next_page(self, interaction, button):
        if self.index < len(self.pages) - 1:
            self.index += 1
            await self.update(interaction)
        else:
            await interaction.response.defer()


class Item(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===========================
    # Parsing multiline entry
    # ===========================
    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        while len(parts) < 10:
            parts.append("")

        try:
            weight = float(parts[5]) if parts[5] else 0.1
        except ValueError:
            weight = 0.1

        return {
            "name": parts[0],
            "type": parts[1],
            "effect": parts[2],
            "rarity": parts[3] if parts[3] else "Common",
            "value": int(parts[4]) if parts[4].isdigit() else 0,
            "weight": weight,
            "slot": parts[6] if len(parts) > 6 else "",
            "notes": parts[7] if len(parts) > 7 else "",
            "rules": parts[8] if len(parts) > 8 else "",
            "requirement": parts[9] if len(parts) > 9 else "",
        }

    # ===========================
    # Commands
    # ===========================
    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send(
            "📦 **Item Commands**\n"
            "• `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules] | [Requirement]`\n"
            "• `!item show [kategori]`\n"
            "• `!item detail <Nama>`\n"
            "• `!item remove <Nama>`\n"
            "• `!item edit <Nama> | key=value ...`\n"
            "• `!use <Char> <Item>`"
        )

    # === ADD ITEM (multiline) ===
    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        data = self._parse_entry(entry)
        if not data["name"] or not data["type"]:
            return await ctx.send("⚠️ Format salah! Gunakan: `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules] | [Requirement]`")

        existing = item_service.get_item(guild_id, data["name"])
        if existing:
            item_service.remove_item(guild_id, data["name"])
            item_service.add_item(guild_id, data)
            await ctx.send(f"♻️ Item **{data['name']}** diperbarui (replace item lama).")
        else:
            item_service.add_item(guild_id, data)
            await ctx.send(f"🧰 Item **{data['name']}** ditambahkan ke katalog.")

    # === SHOW ITEMS ===
    @item.command(name="show")
    async def item_show(self, ctx, *, type_name: str = None):
        guild_id = ctx.guild.id
        items = item_service.list_items(guild_id, limit=9999)
        if not items:
            return await ctx.send("❌ Tidak ada item di katalog.")

        if not type_name:
            type_name = "all"
        type_name = type_name.lower()

        # filter kategori
        if type_name != "all":
            filtered = []
            collect = False
            for line in items:
                if line.startswith("__**"):
                    collect = (type_name in line.lower())
                elif collect and line.strip():
                    filtered.append(line)
            items = filtered
            if not items:
                return await ctx.send(f"❌ Tidak ada item dengan kategori **{type_name}**.")

        # pagination
        per_page = 10
        pages, buffer = [], []
        for line in items:
            if line.startswith("__**"):
                if buffer:
                    pages.append(buffer)
                    buffer = []
                buffer.append(line)
            else:
                buffer.append(line)
                if len(buffer) >= per_page:
                    pages.append(buffer)
                    buffer = []
        if buffer:
            pages.append(buffer)

        embeds = []
        for idx, chunk in enumerate(pages):
            embed = discord.Embed(
                title="📦 Item Catalog",
                description=f"Kategori: {type_name.title()}",
                color=discord.Color.teal()
            )
            value_text = "\n".join(chunk)
            embed.add_field(name="Items", value=safe_field_value(value_text), inline=False)
            embed.set_footer(text=f"Page {idx+1}/{len(pages)}")
            embeds.append(embed)

        view = ItemPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    # === DETAIL (auto split long effect) ===
    @item.command(name="detail")
    async def item_detail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        i = item_service.get_item(guild_id, name)
        if not i:
            return await ctx.send("❌ Item tidak ditemukan.")

        embed = discord.Embed(
            title=f"{i.get('icon','🧰')} {i['name']}",
            description=f"Tipe: **{i['type']}**",
            color=discord.Color.gold()
        )

        # Efek panjang auto split
        for fn, fv in split_long_field("Efek", i.get("effect", "-")):
            embed.add_field(name=fn, value=fv, inline=False)

        # Lain-lain
        embed.add_field(name="Rules", value=safe_field_value(i.get("rules","-")), inline=False)
        embed.add_field(name="Requirement", value=i.get("requirement") or "-", inline=False)
        embed.add_field(name="Rarity", value=i.get("rarity","Common"), inline=True)
        embed.add_field(name="Value", value=str(i.get("value",0)), inline=True)
        embed.add_field(name="Berat", value=str(i.get("weight",0)), inline=True)
        embed.add_field(name="Slot", value=str(i.get("slot","-")), inline=True)
        embed.add_field(name="Notes", value=safe_field_value(i.get("notes","-")), inline=False)

        await ctx.send(embed=embed)

    # === REMOVE / CLEAR ===
    @item.command(name="remove")
    async def item_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        found = item_service.get_item(guild_id, name)
        if not found:
            return await ctx.send("❌ Item tidak ditemukan.")
        item_service.remove_item(guild_id, name)
        await ctx.send(f"🗑️ Item **{name}** dihapus dari katalog.")

    @item.command(name="clearall")
    async def item_clearall(self, ctx, confirm: str = None):
        guild_id = ctx.guild.id
        if confirm != "gmacc":
            return await ctx.send("⚠️ Konfirmasi salah. Gunakan: `!item clearall gmacc`.")
        count = item_service.clear_items(guild_id)
        await ctx.send(f"🗑️ Semua item dihapus dari katalog. (Total: {count})")

    # === USE ITEM (tetap sama) ===
    @commands.command(name="use")
    async def use_item(self, ctx, char: str, *, item_name: str):
        guild_id = ctx.guild.id
        i = item_service.get_item(guild_id, item_name)
        if not i:
            return await ctx.send("❌ Item tidak ditemukan.")

        rules = i.get("rules","")
        effect = i.get("effect","")
        result_lines = []

        if rules:
            for rule in rules.split(";"):
                r = rule.strip()
                if not r:
                    continue
                if r.startswith("+") or r.startswith("-"):
                    if "HP" in r.upper():
                        amount = int(re.findall(r"[+-]?[0-9]+", r)[0])
                        if "+" in r:
                            result_lines.append(f"❤️ {char} dipulihkan {amount} HP.")
                        else:
                            result_lines.append(f"💥 {char} menerima {abs(amount)} damage.")
                elif r.lower().startswith("gold:"):
                    val = int(r.split(":")[1])
                    result_lines.append(f"💰 {char} gold berubah {val:+d}.")
                elif r.lower().startswith("xp:"):
                    val = int(r.split(":")[1])
                    result_lines.append(f"⭐ {char} XP bertambah {val}.")
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

        embed = discord.Embed(title=f"🎒 {char} menggunakan {i['name']}!", color=discord.Color.green())
        embed.add_field(name="Item", value=i["name"], inline=False)
        if result_lines:
            embed.add_field(name="Efek Mekanik", value="\n".join(result_lines), inline=False)
        for fn, fv in split_long_field("Narasi", effect):
            embed.add_field(name=fn, value=fv, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Item(bot))
