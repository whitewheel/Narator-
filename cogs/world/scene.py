import discord
from discord.ext import commands
from utils.db import get_recent
import json
from cogs.world.timeline import log_event  # ✅ untuk catat ke timeline

class Scene(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scene_pin = None  # global pinned scene

    def _get_latest_scene(self):
        # Ambil recent memories dengan type="zone"
        rows = get_recent("0", "0", "zone", 10)
        for r in rows:
            try:
                d = json.loads(r["value"])
                return d
            except Exception:
                continue
        return None

    @commands.group(name="scene", invoke_without_command=True)
    async def scene(self, ctx):
        await ctx.send("Gunakan: `!scene pin`, `!scene unpin`, `!scene show`, `!scene now`")

    @scene.command(name="pin")
    async def scene_pin_cmd(self, ctx):
        scene = self._get_latest_scene()
        if not scene:
            return await ctx.send("⚠️ Tidak ada scene/zone terakhir yang ditemukan.")
        self.scene_pin = scene
        await ctx.send(f"📌 Scene **{scene.get('name','(tanpa nama)')}** dipin.")
        # log ke timeline
        log_event("0", "0", ctx.author.id,
                  code=f"SCENE_PIN_{scene.get('name','').upper()}",
                  title=f"📌 Scene dipin: {scene.get('name','(tanpa nama)')}",
                  details=scene.get("desc","-"),
                  etype="scene_pin",
                  actors=[],
                  tags=["scene","pin"])

    @scene.command(name="unpin")
    async def scene_unpin_cmd(self, ctx):
        if self.scene_pin:
            old = self.scene_pin
            self.scene_pin = None
            await ctx.send("❎ Scene unpinned.")
            log_event("0", "0", ctx.author.id,
                      code=f"SCENE_UNPIN_{old.get('name','').upper()}",
                      title=f"❎ Scene unpinned: {old.get('name','(tanpa nama)')}",
                      details=old.get("desc","-"),
                      etype="scene_unpin",
                      tags=["scene","unpin"])
        else:
            await ctx.send("⚠️ Tidak ada scene yang sedang dipin.")

    @scene.command(name="show")
    async def scene_show_cmd(self, ctx):
        data = self.scene_pin
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
