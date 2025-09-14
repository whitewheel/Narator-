import discord
from discord.ext import commands
from cogs.world.encyclopedia import RACES
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
class RaceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setrace")
    async def setrace(self, ctx, char_name: str, race_name: str):
        """Set karakter menjadi ras tertentu sesuai encyclopedia."""
        race = RACES.get(race_name)
        if not race:
            return await ctx.send("❌ Race tidak ditemukan di encyclopedia.")

        c = load_char(str(ctx.guild.id), str(ctx.channel.id), char_name)
        if not c:
            return await ctx.send("❌ Karakter tidak ditemukan.")

        # Apply race
        c["race"] = race_name
        # Update stats
        for stat, bonus in race.get("stat_bonus", {}).items():
            base = c.get("stats", {}).get(stat, 10)
            c.setdefault("stats", {})[stat] = base + bonus
        # Traits & resist
        c["traits"] = list(set(c.get("traits", []) + race.get("traits", [])))
        c["resist"] = list(set(c.get("resist", []) + race.get("resist", [])))

        save_char(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, char_name, c)
        await ctx.send(f"✅ {char_name} sekarang adalah {race_name}. Bonus & traits diterapkan.")

async def setup(bot):
    await bot.add_cog(RaceManager(bot))
