import discord
from discord.ext import commands
from services import status_service

ICONS = {
    "buff": "✨",
    "debuff": "☠️",
    "expired": "⌛",
    "char": "🧍",
    "enemy": "👹"
}

class Tick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tick")
    async def tick(self, ctx):
        """Kurangi durasi buff/debuff semua karakter & musuh di channel ini."""
        results = await status_service.tick_all_effects(str(ctx.guild.id), str(ctx.channel.id))

        embed = discord.Embed(
            title="⏳ Tick Round Effects",
            description=f"Channel: **{ctx.channel.name}**",
            color=discord.Color.orange()
        )

        for ttype, chars in results.items():
            if not chars:
                continue
            section = []
            for name, data in chars.items():
                expired_str = ", ".join([f"{ICONS['expired']} {e['text']}" for e in data["expired"]]) or "-"
                remain_str = ", ".join([
                    f"{ICONS['buff']} {e['text']} ({e.get('duration','∞')})" if 'buff' in e['text'].lower()
                    else f"{ICONS['debuff']} {e['text']} ({e.get('duration','∞')})"
                    for e in data["remaining"]
                ]) or "-"
                section.append(f"**{name}**\n{ICONS['expired']} Expired: {expired_str}\nActive: {remain_str}")
            embed.add_field(
                name=f"{ICONS[ttype]} {'Characters' if ttype=='char' else 'Enemies'}",
                value="\n\n".join(section),
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tick(bot))
