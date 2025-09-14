import discord
from discord.ext import commands
from cogs.world.encyclopedia import CLASSES
from memory import get_recent, save_memory
import json

# ===== Helper =====
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

def save_char(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "character", json.dumps(data), {"name": name})

# ===== Cog =====
class ClassManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setclass")
    async def setclass(self, ctx, char_name: str, class_name: str):
        """Set karakter menjadi class tertentu sesuai encyclopedia."""
        cls = CLASSES.get(class_name)
        if not cls:
            return await ctx.send("❌ Class tidak ditemukan di encyclopedia.")

        c = load_char(str(ctx.guild.id), str(ctx.channel.id), char_name)
        if not c:
            return await ctx.send("❌ Karakter tidak ditemukan.")

        # Apply class
        c["class"] = class_name
        # Update stats
        for stat, bonus in cls.get("stat_bonus", {}).items():
            base = c.get("stats", {}).get(stat, 10)
            c.setdefault("stats", {})[stat] = base + bonus
        # Tambah skills & passives
        c["skills"] = list(set(c.get("skills", []) + cls.get("actives", [])))
        c["passives"] = list(set(c.get("passives", []) + cls.get("passives", [])))
        # Proficiency
        c["proficiency"] = cls.get("proficiency", {})

        save_char(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, char_name, c)
        await ctx.send(f"✅ {char_name} sekarang adalah {class_name}. Bonus & skills diterapkan.")

async def setup(bot):
    await bot.add_cog(ClassManager(bot))
