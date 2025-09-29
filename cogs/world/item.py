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

# ===========================
# Pagination View
# ===========================
class ItemPaginator(View):
    def __init__(self, pages):
        super().__init__(timeout=120)  # auto stop setelah 2 menit
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

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 6:
            return None
        try:
            weight = float(parts[5])
        except ValueError:
            return None

        return {
            "name": parts[0],
            "type": parts[1],
            "effect": parts[2],
            "rarity": parts[3] if len(parts) > 3 else "Common",
            "value": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
            "weight": weight,
            "slot": parts[6] if len(parts) > 6 else None,
            "notes": parts[7] if len(parts) > 7 else "",
            "rules": parts[8] if len(parts) > 8 else "",
            "requirement": parts[9] if len(parts) > 9 else "",  # baru
        }

    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send(
            "📦 **Item Commands**\n"
            "• `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules] | [Requirement]`\n"
            "• `!item show [all|weapon|armor|consumable|accessory|gadget|misc]`\n"
            "• `!item remove <Nama>`\n"
            "• `!item detail <Nama>`\n"
            "• `!item edit <Nama> | key=value [key=value...]`\n"
            "• `!item info <Nama>`\n"
            "• `!use <Char> <Item>`\n"
            "• `!item clearall gmacc`\n\n"
            "⚠️ Kolom **Weight** wajib diisi (angka). Contoh:\n"
            "`!item add Rust Shiv | Weapon | Damage 1d4 + DEX | Common | 20 | 0.5 | main_hand | Pisau kecil dari scrap logam | Crit 20 (×2) | STR 5+`"
        )

    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format salah! Gunakan `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules] | [Requirement]`")

        # Cek duplikat
        existing = item_service.get_item(guild_id, data["name"])
        if existing:
            item_service.remove_item(guild_id, data["name"])
            item_service.add_item(guild_id, data)
            await ctx.send(f"♻️ Item **{data['name']}** diperbarui (replace item lama).")
        else:
            item_service.add_item(guild_id, data)
            await ctx.send(f"🧰 Item **{data['name']}** ditambahkan ke katalog.")

    @item.command(name="show")
    async def item_show(self, ctx, *, type_name: str = None):
        guild_id = ctx.guild.id
        items = item_service.list_items(guild_id, limit=9999)
        if not items:
            return await ctx.send("Tidak ada item.")

        # Default = all
        if not type_name:
            type_name = "all"

        type_name = type_name.lower()

        # === Filter kategori spesifik ===
        if type_name != "all":
            filtered = []
            collect = False
            for line in items:
                if line.startswith("__**"):  # kategori baru
                    collect = (type_name in line.lower())
                elif collect and line.strip():
                    filtered.append(line)
            items = filtered
            if not items:
                return await ctx.send(f"❌ Tidak ada item dengan kategori **{type_name}**.")

        # === Buat embed pagination ===
        per_page = 10
        pages = []
        for i in range(0, len(items), per_page):
            chunk = items[i:i+per_page]
            embed = discord.Embed(
                title=f"📦 Item Catalog",
                description=f"Kategori: {type_name.title()}",
                color=discord.Color.teal()
            )
            for line in chunk:
                if "|" in line:
                    name, val = line.split("|", 1)
                    embed.add_field(
                        name=name.strip(),
                        value=safe_field_value(val.strip()),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=line[:50],
                        value=safe_field_value(line),
                        inline=False
                    )
            embed.set_footer(text=f"Page {i//per_page+1}/{(len(items)-1)//per_page+1}")
            pages.append(embed)

        view = ItemPaginator(pages)
        await ctx.send(embed=pages[0], view=view)

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
            return await ctx.send("⚠️ Konfirmasi salah. Gunakan: `!item clearall gmacc` untuk hapus semua item.")

        count = item_service.clear_items(guild_id)
        await ctx.send(f"🗑️ Semua item dihapus dari katalog. (Total: {count})")

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
        embed.add_field(name="Efek", value=i.get("effect","-"), inline=False)
        embed.add_field(name="Rules", value=i.get("rules","-"), inline=False)
        embed.add_field(name="Requirement", value=i.get("requirement","-"), inline=False)  # baru
        embed.add_field(name="Rarity", value=i.get("rarity","Common"), inline=True)
        embed.add_field(name="Value", value=str(i.get("value",0)), inline=True)
        embed.add_field(name="Berat", value=str(i.get("weight",0)), inline=True)
        embed.add_field(name="Slot", value=str(i.get("slot","-")), inline=True)
        embed.add_field(name="Notes", value=i.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    # === Edit item global ===
    @item.command(name="edit")
    async def item_edit(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        try:
            name, rest = entry.split("|", 1)
        except ValueError:
            return await ctx.send("⚠️ Format salah! Gunakan: `!item edit Nama | key=value [key=value...]`")

        name = name.strip()
        updates = {}
        for p in rest.split():
            if "=" in p:
                k, v = p.split("=", 1)
                updates[k.strip()] = v.strip()

        found = item_service.get_item(guild_id, name)
        if not found:
            return await ctx.send(f"❌ Item {name} tidak ditemukan.")

        found.update(updates)
        if "weight" in updates:
            try:
                found["weight"] = float(updates["weight"])
            except:
                return await ctx.send("⚠️ Weight harus angka.")

        item_service.add_item(guild_id, found)
        await ctx.send(f"📝 Item **{name}** diperbarui: {updates}")

    # === Info singkat item ===
    @item.command(name="info")
    async def item_info(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        i = item_service.get_item(guild_id, name)
        if not i:
            return await ctx.send("❌ Item tidak ditemukan.")
        req = f" | Req: {i['requirement']}" if i.get("requirement") else ""
        await ctx.send(f"{i.get('icon','📦')} **{i['name']}** | {i['rarity']} | ⚖️ {i['weight']} | ✨ {i.get('effect','-')}{req}")

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

        narasi = f"✨ {char} menggunakan {i['name']}. {effect}"
        embed = discord.Embed(title=f"🎒 {char} menggunakan item!", color=discord.Color.green())
        embed.add_field(name="Item", value=i["name"], inline=False)
        if result_lines:
            embed.add_field(name="Efek Mekanik", value="\n".join(result_lines), inline=False)
        if effect:
            embed.add_field(name="Narasi", value=effect, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Item(bot))
