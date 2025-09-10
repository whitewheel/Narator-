import discord
from discord.ext import commands

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="poll")
    async def poll(self, ctx, question: str, *options):
        """Buat polling. Contoh: !poll "Makan apa?" Nasi Mie Roti"""
        if len(options) < 2:
            return await ctx.send("⚠️ Minimal 2 opsi.")
        if len(options) > 10:
            return await ctx.send("⚠️ Maksimal 10 opsi.")

        emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        description = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.blue()
        )
        poll_message = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_message.add_reaction(emojis[i])

async def setup(bot):
    await bot.add_cog(Poll(bot))
