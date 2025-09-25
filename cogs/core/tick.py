# cogs/core/tick.py
import discord
from discord.ext import commands
from services import status_service

ICONS = {
    "buff": "✨",
    "debuff": "☠️",
    "expired": "⌛",
    "char": "🧍",
    "enemy": "👹",
    "timer": "⏱️",
    "infinite": "♾️",
}

class Tick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tick")
    async def tick(self, ctx):
        """Kurangi durasi buff/debuff semua karakter & musuh di server ini."""
        results = await status_service.tick_all_effects(ctx.guild.id)

        embed = discord.Embed(
            title="⏳ Tick Round Effects",
            description=f"Server: **{ctx.guild.name}**",
            color=discord.Color.orange()
        )

        for ttype, chars in results.items():
            if not chars:
                continue
            section = []
            for name, data in chars.items():
                # efek expired
                expired_str = ", ".join([
                    f"{ICONS['expired']} {e['text']}"
                    for e in data["expired"]
                ]) or "-"

                # efek yang masih aktif
                remain_str = ", ".join([
                    (
                        f"{ICONS['buff']} {e['text']} "
                        f"({ICONS['timer']} {e['duration']})"
                        if e.get("duration", -1) > 0 else
                        f"{ICONS['buff']} {e['text']} ({ICONS['infinite']})"
                    ) if e.get("type") == "buff" else
                    (
                        f"{ICONS['debuff']} {e['text']} "
                        f"({ICONS['timer']} {e['duration']})"
                        if e.get("duration", -1) > 0 else
                        f"{ICONS['debuff']} {e['text']} ({ICONS['infinite']})"
                    )
                    for e in data["remaining"]
                ]) or "-"

                section.append(
                    f"**{name}**\n"
                    f"{ICONS['expired']} Expired: {expired_str}\n"
                    f"Active: {remain_str}"
                )

            embed.add_field(
                name=f"{ICONS[ttype]} {'Characters' if ttype=='char' else 'Enemies'}",
                value="\n\n".join(section),
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tick(bot))
