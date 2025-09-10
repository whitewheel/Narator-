import random
import discord
from discord.ext import commands

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx, *, dice: str):
        """Contoh: !roll 2d6+3"""
        try:
            rolls, modifier = dice.lower().split("d")

            if "+" in modifier:
                sides, bonus = modifier.split("+")
                bonus = int(bonus)
            elif "-" in modifier:
                sides, minus = modifier.split("-")
                bonus = -int(minus)
            else:
                sides, bonus = modifier, 0

            rolls, sides = int(rolls), int(sides)
            if rolls <= 0 or sides <= 0:
                raise ValueError()

            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results) + bonus

            # Catatan crit/fail sederhana untuk roll d20 tunggal
            note = ""
            if rolls == 1 and sides == 20:
                if results[0] == 20:
                    note = " **(CRIT!)**"
                elif results[0] == 1:
                    note = " **(FAIL!)**"

            embed = discord.Embed(
                title=f"🎲 Roll {dice}",
                description=f"Hasil: {results} | Modifier: {bonus}\n**Total = {total}**{note}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception:
            await ctx.send("❌ Format salah. Contoh: `!roll 2d6+3`")

async def setup(bot):
    await bot.add_cog(Roll(bot))
