import discord
from discord.ext import commands
from services import item_service
import re

class Item(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        # minimal: Nama | Type | Effect | Rarity | Value | Weight
        if len(parts) < 6:
            return None
        # validasi weight harus angka
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
        }

    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send(
            "📦 **Item Commands**\n"
            "• `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules]`\n"
            "• `!item show`\n"
            "• `!item remove <Nama>`\n"
            "• `!item detail <Nama>`\n"
            "• `!use <Char> <Item>`\n\n"
            "⚠️ Kolom **Weight** wajib diisi (angka). Contoh:\n"
            "`!item add Neural Pistol Mk.I | Weapon | Pistol energi standar | Rare | 420 | 1.4 | main_hand | Senjata awal | +10 HP`"
        )

    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send(
                "⚠️ Format salah!\n"
                "Gunakan: `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules]`\n"
                "Contoh: `!item add Neural Pistol Mk.I | Weapon | Pistol energi standar | Rare | 420 | 1.4 | main_hand | Senjata awal | +10 HP`"
            )
        item_service.add_item(guild_id, data)
        await ctx.send(f"🧰 Item **{data['name']}** ditambahkan ke katalog.")

    @item.command(name="show")
    async def item_show(self, ctx):
        guild_id = ctx.guild.id
        items = item_service.list_items(guild_id, limit=20)
        if not items:
            return await ctx.send("Tidak ada item.")
        await ctx.send("\n".join(items))

    @item.command(name="remove")
    async def item_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        found = item_service.get_item(guild_id, name)
        if not found:
            return await ctx.send("❌ Item tidak ditemukan.")
        item_service.remove_item(guild_id, name)
        await ctx.send(f"🗑️ Item **{name}** dihapus dari katalog.")

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
        embed.add_field(name="Rarity", value=i.get("rarity","Common"), inline=True)
        embed.add_field(name="Value", value=str(i.get("value",0)), inline=True)
        embed.add_field(name="⚖️ Berat", value=str(i.get("weight",0)), inline=True)
        embed.add_field(name="Slot", value=str(i.get("slot","-")), inline=True)
        embed.add_field(name="Notes", value=i.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

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
