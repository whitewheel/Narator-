import discord
from discord.ext import commands

class StatusAlias(commands.Cog):
    """
    QoL alias untuk command status & enemy (gabung).
    !dmg / !heal otomatis pilih karakter atau musuh.
    """

    def __init__(self, bot):
        self.bot = bot

    # Helper untuk cek & panggil CharacterStatus
    async def _call_status(self, ctx, subcommand: str, *args):
        status_cog = self.bot.get_cog("CharacterStatus")
        if not status_cog:
            return False
        cmd = status_cog.get_command(f"status {subcommand}")
        if not cmd:
            return False
        await cmd.callback(status_cog, ctx, *args)
        return True

    # Helper untuk cek & panggil EnemyStatus
    async def _call_enemy(self, ctx, subcommand: str, *args):
        enemy_cog = self.bot.get_cog("EnemyStatus")
        if not enemy_cog:
            return False
        cmd = enemy_cog.get_command(f"enemy {subcommand}")
        if not cmd:
            return False
        await cmd.callback(enemy_cog, ctx, *args)
        return True

    # ==== Alias gabungan ====
    @commands.command(name="dmg")
    async def dmg_alias(self, ctx, name: str, amount: int, target: str = None):
        """Alias: !dmg <Nama> <jumlah> [all] → auto karakter/enemy"""
        if await self._call_status(ctx, "dmg", name, amount):
            return
        if await self._call_enemy(ctx, "dmg", name, amount, target):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="heal")
    async def heal_alias(self, ctx, name: str, amount: int, target: str = None):
        """Alias: !heal <Nama> <jumlah> [all] → auto karakter/enemy"""
        if await self._call_status(ctx, "heal", name, amount):
            return
        if await self._call_enemy(ctx, "heal", name, amount, target):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="ene-")
    async def ene_minus(self, ctx, name: str, amount: int):
        """Alias: !ene- <Nama> <jumlah> → kurangi energy"""
        if await self._call_status(ctx, "useenergy", name, amount):
            return
        if await self._call_enemy(ctx, "useenergy", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="ene+")
    async def ene_plus(self, ctx, name: str, amount: int):
        """Alias: !ene+ <Nama> <jumlah> → tambah energy"""
        if await self._call_status(ctx, "regenenergy", name, amount):
            return
        if await self._call_enemy(ctx, "regenenergy", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="stam-")
    async def stam_minus(self, ctx, name: str, amount: int):
        """Alias: !stam- <Nama> <jumlah> → kurangi stamina"""
        if await self._call_status(ctx, "usestam", name, amount):
            return
        if await self._call_enemy(ctx, "usestam", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="stam+")
    async def stam_plus(self, ctx, name: str, amount: int):
        """Alias: !stam+ <Nama> <jumlah> → tambah stamina"""
        if await self._call_status(ctx, "regenstam", name, amount):
            return
        if await self._call_enemy(ctx, "regenstam", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

async def setup(bot):
    await bot.add_cog(StatusAlias(bot))
