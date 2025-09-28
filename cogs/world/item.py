import discord
from discord.ext import commands
from services import item_service
import re

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
        }

    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send(
            "📦 **Item Commands**\n"
            "• `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules]`\n"
            "• `!item show [all|weapon|armor|consumable|accessory|gadget|misc]`\n"
            "• `!item remove <Nama>`\n"
            "• `!item detail <Nama>`\n"
            "• `!item edit <Nama> | key=value [key=value...]`\n"
            "• `!item info <Nama>`\n"
            "• `!use <Char> <Item>`\n\n"
            "⚠️ Kolom **Weight** wajib diisi (angka). Contoh:\n"
            "`!item add Neural Pistol Mk.I | Weapon | Pistol energi standar | Rare | 420 | 1.4 | main_hand | Senjata awal | +10 HP`"
        )

    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format salah! Gunakan `!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules]`")
        item_service.add_item(guild_id, data)
        await ctx.send(f"🧰 Item **{data['name']}** ditambahkan ke katalog.")

    @item.command(name="show")
    async def item_show(self, ctx, *, type_name: str = None):
        guild_id = ctx.guild.id
        if type_name and type_name.lower() == "all":
            items = item_service.list_items(guild_id, limit=9999)
        else:
            items = item_service.list_items(guild_id, limit=20)

        if not items:
            return await ctx.send("Tidak ada item.")

        if type_name and type_name.lower() not in ("all",):
            block = []
            collect = False
            for line in items:
                if line.startswith("__**"):
                    collect = (type_name.lower() in line.lower())
                elif collect and line.strip():
                    block.append(line)

            if not block:
                return await ctx.send(f"Tidak ada item dengan kategori **{type_name}**.")
            return await ctx.send("\n".join(block))

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
        await ctx.send(f"{i.get('icon','📦')} **{i['name']}** | {i['rarity']} | ⚖️ {i['weight']} | ✨ {i.get('effect','-')}")

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
