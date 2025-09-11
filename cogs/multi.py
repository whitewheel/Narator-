import discord
from discord.ext import commands
import asyncio

class MultiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="multi")
    async def multi(self, ctx, *, block: str):
        """
        Jalankan beberapa command sekaligus.
        Format penggunaan:
        !multi
        status set Alice 20 5 3
        status setcore Alice 10 12 14 8 13 9
        enemy set Goblin 15 2 4
        enemy setcore Goblin 8 14 12 6 10 7
        """
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        for line in lines:
            parts = line.split()
            cmd_name, *args = parts
            cmd = self.bot.get_command(cmd_name)
            if not cmd:
                await ctx.send(f"⚠️ Command `{cmd_name}` tidak ditemukan.")
                continue
            try:
                # jalankan command asli
                await ctx.invoke(cmd, *args)
            except Exception as e:
                await ctx.send(f"❌ Error di `{cmd_name}`: {e}")
            # jeda 1 detik biar output lebih natural
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(MultiCommand(bot))
  
