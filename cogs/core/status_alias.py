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
        fn = getattr(status_cog, f"status_{subcommand}", None)
        if not fn:
            return False
        await fn(ctx, *args)
        return True

    # Helper untuk cek & panggil EnemyStatus
    async def _call_enemy(self, ctx, subcommand: str, *args):
        enemy_cog = self.bot.get_cog("EnemyStatus")
        if not enemy_cog:
            return False
        fn = getattr(enemy_cog, f"enemy_{subcommand}", None)
        if not fn:
            return False
        await fn(ctx, *args)
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

    # ==== Tambahan QoL ====
    @commands.command(name="gold+")
    async def gold_plus(self, ctx, name: str, amount: int):
        """Alias: !gold+ <Nama> <jumlah> → tambah gold ke karakter"""
        if await self._call_status(ctx, "addgold", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character.")

    @commands.command(name="xp+")
    async def xp_plus(self, ctx, name: str, amount: int):
        """Alias: !xp+ <Nama> <jumlah> → tambah XP ke karakter"""
        if await self._call_status(ctx, "addxp", name, amount):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character.")

    @commands.command(name="buff")
    async def buff_alias(self, ctx, name: str, *, text: str):
        """Alias: !buff <Nama> <efek> → tambahkan buff"""
        if await self._call_status(ctx, "buff", name, text):
            return
        if await self._call_enemy(ctx, "buff", name, text):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="debuff")
    async def debuff_alias(self, ctx, name: str, *, text: str):
        """Alias: !debuff <Nama> <efek> → tambahkan debuff"""
        if await self._call_status(ctx, "debuff", name, text):
            return
        if await self._call_enemy(ctx, "debuff", name, text):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")

    @commands.command(name="hp")
    async def hp_check(self, ctx, name: str):
        """Alias: !hp <Nama> → cek HP"""
        if await self._call_status(ctx, "showhp", name):
            return
        if await self._call_enemy(ctx, "showhp", name):
            return
        await ctx.send(f"⚠️ {name} tidak ditemukan di Character maupun Enemy.")


async def setup(bot):
    await bot.add_cog(StatusAlias(bot))
