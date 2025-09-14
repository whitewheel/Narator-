import discord
from discord.ext import commands
from memory import save_memory, get_recent, template_for

import json

class Scene(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scene_pin = {}  # key: (guild, channel) → pinned scene

    def _key(self, ctx):
        return (str(ctx.guild.id), str(ctx.channel.id))

    def _get_latest_scene(self, ctx):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "zone", 10)
        for (_id, cat, content, meta, ts) in rows:
            try:
                d = json.loads(content)
                return d
            except:
                continue
        return None

    @commands.group(name="scene", invoke_without_command=True)
    async def scene(self, ctx):
        await ctx.send("Gunakan: `!scene pin`, `!scene unpin`, `!scene show`, `!scene now`")

    @scene.command(name="pin")
    async def scene_pin_cmd(self, ctx):
        scene = self._get_latest_scene(ctx)
        if not scene:
            return await ctx.send("⚠️ Tidak ada scene/zone terakhir yang ditemukan.")
        key = self._key(ctx)
        self.scene_pin[key] = scene
        await ctx.send(f"📌 Scene **{scene.get('name','(tanpa nama)')}** dipin.")

    @scene.command(name="unpin")
    async def scene_unpin_cmd(self, ctx):
        key = self._key(ctx)
        if key in self.scene_pin:
            del self.scene_pin[key]
            await ctx.send("❎ Scene unpinned.")
        else:
            await ctx.send("⚠️ Tidak ada scene yang sedang dipin.")

    @scene.command(name="show")
    async def scene_show_cmd(self, ctx):
        key = self._key(ctx)
        data = self.scene_pin.get(key)
        if not data:
            return await ctx.send("⚠️ Tidak ada scene yang sedang dipin.")
        embed = discord.Embed(
            title=f"📍 {data.get('name','(tanpa nama)')}",
            description=data.get("desc", "-"),
            color=discord.Color.green()
        )
        embed.add_field(name="🔺 Faksi", value=", ".join(data.get("factions", []) or ["-"]), inline=False)
        embed.add_field(name="⚠️ Bahaya", value=data.get("danger", "-"), inline=True)
        await ctx.send(embed=embed)

    @scene.command(name="now")
    async def scene_now_cmd(self, ctx):
        """Alias cepat untuk tampilkan scene terpin saat ini (untuk !next auto)"""
        await self.scene_show_cmd(ctx)

async def setup(bot):
    await bot.add_cog(Scene(bot))
