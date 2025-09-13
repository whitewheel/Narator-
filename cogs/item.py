import discord
from discord.ext import commands
from memory import save_memory, get_recent, category_icon, template_for

import json

class Item(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _key(self, ctx):
        return (str(ctx.guild.id), str(ctx.channel.id))

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 3:
            return None
        data = template_for("item")
        data["name"] = parts[0]
        data["type"] = parts[1]
        data["effect"] = parts[2]
        if len(parts) > 3:
            data["rarity"] = parts[3]
        return data

    @commands.group(name="item", invoke_without_command=True)
    async def item(self, ctx):
        await ctx.send("Gunakan: `!item add`, `!item show`, `!item remove`, `!item detail`")

    @item.command(name="add")
    async def item_add(self, ctx, *, entry: str):
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format: `!item add Nama | Tipe | Efek | [Rarity]`")
        key = self._key(ctx)
        save_memory(key[0], key[1], ctx.author.id, "item", json.dumps(data), {"name": data["name"]})
        await ctx.send(f"🧰 Item **{data['name']}** ditambahkan.")

    @item.command(name="show")
    async def item_show(self, ctx):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "item", 50)
        out = []
        for (_id, cat, content, meta, ts) in rows:
            try:
                i = json.loads(content)
                line = f"🧰 **{i['name']}** ({i['type']})"
                out.append(line)
            except:
                continue
        if not out:
            return await ctx.send("Tidak ada item.")
        await ctx.send("\n".join(out[:10]))

    @item.command(name="remove")
    async def item_remove(self, ctx, *, name: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "item", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                i = json.loads(content)
                if i["name"].lower() == name.lower():
                    i["effect"] = "(deleted)"
                    save_memory(key[0], key[1], ctx.author.id, "item", json.dumps(i), {"name": i["name"]})
                    return await ctx.send(f"🗑️ Item **{i['name']}** dihapus.")
            except:
                continue
        await ctx.send("❌ Item tidak ditemukan.")

    @item.command(name="detail")
    async def item_detail(self, ctx, *, name: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "item", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                i = json.loads(content)
                if i["name"].lower() == name.lower():
                    embed = discord.Embed(
                        title=f"🧰 {i['name']}",
                        description=f"Tipe: **{i['type']}**",
                        color=discord.Color.teal()
                    )
                    embed.add_field(name="🎯 Efek", value=i["effect"], inline=False)
                    embed.add_field(name="⭐ Rarity", value=i.get("rarity", "-"), inline=True)
                    await ctx.send(embed=embed)
                    return
            except:
                continue
        await ctx.send("❌ Item tidak ditemukan.")

async def setup(bot):
    await bot.add_cog(Item(bot))