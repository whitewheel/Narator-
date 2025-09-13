import discord
from discord.ext import commands
from memory import save_memory, get_recent
import json

def _key(ctx):
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)

def save_enemy(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "enemy", json.dumps(data), {"name": name})

def load_enemy(guild_id, channel_id, name):
    rows = get_recent(guild_id, channel_id, "enemy", 100)
    for (_id, cat, content, meta, ts) in rows:
        try:
            e = json.loads(content)
            if meta.get("name","").lower() == name.lower() or e.get("name","").lower() == name.lower():
                return e
        except:
            continue
    return None

def save_char(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "character", json.dumps(data), {"name": name})

def load_char(guild_id, channel_id, name):
    rows = get_recent(guild_id, channel_id, "character", 100)
    for (_id, cat, content, meta, ts) in rows:
        try:
            c = json.loads(content)
            if meta.get("name","").lower() == name.lower() or c.get("name","").lower() == name.lower():
                return c
        except:
            continue
    return None

class Loot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="loot", invoke_without_command=True)
    async def loot(self, ctx):
        await ctx.send("Gunakan: `!loot list <Enemy>`, `!loot take <Enemy> <Item> <Char>`, `!loot takeall <Enemy> <Char>`, `!loot drop <Enemy>`")

    @loot.command(name="list")
    async def loot_list(self, ctx, enemy_name: str):
        e = load_enemy(str(ctx.guild.id), str(ctx.channel.id), enemy_name)
        if not e:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        loots = e.get("loot", [])
        if not loots:
            return await ctx.send("❌ Enemy ini tidak punya loot.")
        out = [f"- {it['name']} ({it.get('rarity','')})" for it in loots]
        await ctx.send(f"🎁 Loot dari {enemy_name}:\n" + "\n".join(out))

    @loot.command(name="take")
    async def loot_take(self, ctx, enemy_name: str, item_name: str, char_name: str):
        e = load_enemy(str(ctx.guild.id), str(ctx.channel.id), enemy_name)
        if not e:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        loots = e.get("loot", [])
        found = None
        for it in loots:
            if it["name"].lower() == item_name.lower():
                found = it
                break
        if not found:
            return await ctx.send("❌ Item tidak ditemukan di loot.")

        c = load_char(str(ctx.guild.id), str(ctx.channel.id), char_name)
        if not c:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        inv = c.get("inventory", [])
        exists = next((x for x in inv if x["name"].lower() == found["name"].lower()), None)
        if exists:
            exists["qty"] = exists.get("qty",1) + 1
        else:
            found_copy = found.copy()
            found_copy["qty"] = 1
            inv.append(found_copy)
        c["inventory"] = inv
        save_char(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, char_name, c)

        # Remove from enemy loot
        e["loot"] = [it for it in loots if it["name"].lower() != found["name"].lower()]
        save_enemy(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, enemy_name, e)

        await ctx.send(f"✅ {char_name} mengambil {found['name']} dari {enemy_name}.")

    @loot.command(name="takeall")
    async def loot_takeall(self, ctx, enemy_name: str, char_name: str):
        e = load_enemy(str(ctx.guild.id), str(ctx.channel.id), enemy_name)
        if not e:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        loots = e.get("loot", [])
        if not loots:
            return await ctx.send("❌ Tidak ada loot tersisa.")
        c = load_char(str(ctx.guild.id), str(ctx.channel.id), char_name)
        if not c:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        inv = c.get("inventory", [])
        for it in loots:
            exists = next((x for x in inv if x["name"].lower() == it["name"].lower()), None)
            if exists:
                exists["qty"] = exists.get("qty",1) + 1
            else:
                it_copy = it.copy()
                it_copy["qty"] = 1
                inv.append(it_copy)
        c["inventory"] = inv
        save_char(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, char_name, c)

        e["loot"] = []
        save_enemy(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, enemy_name, e)
        await ctx.send(f"✅ Semua loot dari {enemy_name} diambil oleh {char_name}.")

    @loot.command(name="drop")
    async def loot_drop(self, ctx, enemy_name: str):
        e = load_enemy(str(ctx.guild.id), str(ctx.channel.id), enemy_name)
        if not e:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        e["loot"] = []
        save_enemy(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, enemy_name, e)
        await ctx.send(f"🗑️ Semua loot dari {enemy_name} dibuang.")

async def setup(bot):
    await bot.add_cog(Loot(bot))
