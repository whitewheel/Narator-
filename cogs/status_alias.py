import discord
from discord.ext import commands

class StatusAlias(commands.Cog):
    """
    QoL alias untuk command status.
    Memanggil ulang command utama dari CharacterStatus.
    """

    def __init__(self, bot):
        self.bot = bot

    # Helper untuk panggil command status
    async def _call_status(self, ctx, subcommand: str, *args):
        status_cog = self.bot.get_cog("CharacterStatus")
        if not status_cog:
            return await ctx.send("⚠️ Modul CharacterStatus belum aktif.")
        cmd = status_cog.get_command(f"status {subcommand}")
        if not cmd:
            return await ctx.send(f"⚠️ Subcommand status `{subcommand}` tidak ditemukan.")
        await cmd.callback(status_cog, ctx, *args)

    # === Alias cepat ===
    @commands.command(name="dmg")
    async def dmg_alias(self, ctx, name: str, amount: int):
        """Alias: !dmg <Nama> <jumlah>"""
        await self._call_status(ctx, "dmg", name, amount)

    @commands.command(name="heal")
    async def heal_alias(self, ctx, name: str, amount: int):
        """Alias: !heal <Nama> <jumlah>"""
        await self._call_status(ctx, "heal", name, amount)

    @commands.command(name="ene-")
    async def ene_minus(self, ctx, name: str, amount: int):
        """Alias: !ene- <Nama> <jumlah>  → kurangi energy"""
        await self._call_status(ctx, "useenergy", name, amount)

    @commands.command(name="ene+")
    async def ene_plus(self, ctx, name: str, amount: int):
        """Alias: !ene+ <Nama> <jumlah>  → tambah energy"""
        await self._call_status(ctx, "regenenergy", name, amount)

    @commands.command(name="stam-")
    async def stam_minus(self, ctx, name: str, amount: int):
        """Alias: !stam- <Nama> <jumlah>  → kurangi stamina"""
        await self._call_status(ctx, "usestam", name, amount)

    @commands.command(name="stam+")
    async def stam_plus(self, ctx, name: str, amount: int):
        """Alias: !stam+ <Nama> <jumlah>  → tambah stamina"""
        await self._call_status(ctx, "regenstam", name, amount)


async def setup(bot):
    await bot.add_cog(StatusAlias(bot))
