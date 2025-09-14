import discord
from discord.ext import commands

class HistoryManager:
    def __init__(self):
        # {(guild_id, channel_id): [list of actions]}
        self.history = {}

    def push(self, ctx, name, field, old, new):
        """Simpan perubahan ke history"""
        k = (ctx.guild.id if ctx.guild else 0, ctx.channel.id)
        if k not in self.history:
            self.history[k] = []
        self.history[k].append({
            "name": name,
            "field": field,
            "old": old,
            "new": new
        })

    def pop(self, ctx):
        """Ambil perubahan terakhir (undo)"""
        k = (ctx.guild.id if ctx.guild else 0, ctx.channel.id)
        if k in self.history and self.history[k]:
            return self.history[k].pop()
        return None

history = HistoryManager()

# Cog global untuk command !undo
class HistoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="undo")
    async def undo(self, ctx):
        last = history.pop(ctx)
        if not last:
            return await ctx.send("⚠️ Tidak ada aksi yang bisa di-undo.")

        # cek di CharacterStatus
        status_cog = self.bot.get_cog("CharacterStatus")
        if status_cog:
            s = status_cog._ensure(ctx)
            if last["name"] in s:
                s[last["name"]][last["field"]] = last["old"]
                return await ctx.send(
                    f"🔄 Undo: **{last['name']}**.{last['field']} → {last['old']} (dari {last['new']})."
                )

        # cek di EnemyStatus
        enemy_cog = self.bot.get_cog("EnemyStatus")
        if enemy_cog:
            s = enemy_cog._ensure(ctx)
            if last["name"] in s:
                s[last["name"]][last["field"]] = last["old"]
                return await ctx.send(
                    f"🔄 Undo: **{last['name']}**.{last['field']} → {last['old']} (dari {last['new']})."
                )

        await ctx.send("⚠️ Target sudah tidak ada, undo gagal.")

async def setup(bot):
    await bot.add_cog(HistoryCog(bot))
