import discord
from discord.ext import commands
from utils.db import save_memory, get_recent, template_for
import json
import re

class Item(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 3:
            return None
        data = template_for("item")
        data["name"]   = parts[0]
        data["type"]   = parts[1]
        data["effect"] = parts[2]
        data["rarity"] = parts[3] if len(parts) > 3 else "Common"
        data["value"]  = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
        try:
            data["weight"] = float(parts[5]) if len(parts) > 5 else 0.0
        except:
            data["weight"] = 0.0
        data["slot"]   = parts[6] if len(parts) > 6 else None
        data["notes"]  = parts[7] if len(parts) > 7 else ""
        data["rules"]  = parts[8] if len(parts) > 8 else ""
        return data

    def _get_item_by_name(self, guild_id: int, name: str):
        rows = get_recent(guild_id, "item", 100)
        for r in rows:
            try:
                i = json.loads(r["value"])
                if i["name"].lower() == name.lower():
                    return i
            except:
                continue
        return None

    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send("Gunakan: `!item add`, `!item show`, `!item remove`, `!item detail`, `!use`")

    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        guild_id = ctx.guild.id
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format: `!item add Nama | Type | Effect | [Rarity] | [Value] | [Weight] | [Slot] | [Notes] | [Rules]`")
        save_memory(guild_id, ctx.author.id, "item", json.dumps(data), {"name": data["name"]})
        await ctx.send(f"🧰 Item **{data['name']}** ditambahkan.")

    @item.command(name="show")
    async def item_show(self, ctx):
        guild_id = ctx.guild.id
        rows = get_recent(guild_id, "item", 50)
        out = []
        for r in rows:
            try:
                i = json.loads(r["value"])
                line = f"🧰 **{i['name']}** ({i['type']})"
                out.append(line)
            except:
                continue
        if not out:
            return await ctx.send("Tidak ada item.")
        await ctx.send("\n".join(out[:15]))

    @item.command(name="remove")
    async def item_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        rows = get_recent(guild_id, "item", 50)
        for r in rows:
            try:
                i = json.loads(r["value"])
                if i["name"].lower() == name.lower():
                    i["effect"] = "(deleted)"
                    save_memory(guild_id, ctx.author.id, "item", json.dumps(i), {"name": i["name"]})
                    return await ctx.send(f"🗑️ Item **{i['name']}** dihapus.")
            except:
                continue
        await ctx.send("❌ Item tidak ditemukan.")

    @item.command(name="detail")
    async def item_detail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        i = self._get_item_by_name(guild_id, name)
        if not i:
            return await ctx.send("❌ Item tidak ditemukan.")
        embed = discord.Embed(
            title=f"🧰 {i['name']}",
            description=f"Tipe: **{i['type']}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="Efek", value=i.get("effect","-"), inline=False)
        embed.add_field(name="Rules", value=i.get("rules","-"), inline=False)
        embed.add_field(name="Rarity", value=i.get("rarity","Common"), inline=True)
        embed.add_field(name="Value", value=str(i.get("value",0)), inline=True)
        embed.add_field(name="Weight", value=str(i.get("weight",0)), inline=True)
        embed.add_field(name="Slot", value=str(i.get("slot","-")), inline=True)
        embed.add_field(name="Notes", value=i.get("notes","-"), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="use")
    async def use_item(self, ctx, char: str, *, item_name: str):
        guild_id = ctx.guild.id
        i = self._get_item_by_name(guild_id, item_name)
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
