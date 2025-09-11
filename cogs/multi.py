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
        Gunakan format multi-line:
        !multi
        status set Alice 20 5 3
        status setcore Alice 10 12 14 8 13 9
        enemy set Goblin 15 2 4
        enemy setcore Goblin 8 14 12 6 10 7
        dmg Goblin 5
        heal Alice 3
        """
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        for line in lines:
            parts = line.split()
            if not parts:
                continue

            cmd = None
            args = []

            # coba cek 2 kata (subcommand, misal: "status set", "enemy dmg")
            if len(parts) > 1:
                maybe = f"{parts[0]} {parts[1]}"
                cmd = self.bot.get_command(maybe)
                if cmd:
                    args = parts[2:]

            # fallback ke single command (termasuk alias: dmg, heal, ene-, ene+ dll)
            if not cmd:
                cmd = self.bot.get_command(parts[0])
                args = parts[1:]

            if not cmd:
                await ctx.send(f"⚠️ Command `{parts[0]}` tidak ditemukan.")
                continue

            try:
                await ctx.invoke(cmd, *args)
            except Exception as e:
                await ctx.send(f"❌ Error di `{line}`: {e}")

            # jeda supaya output rapi
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(MultiCommand(bot))
