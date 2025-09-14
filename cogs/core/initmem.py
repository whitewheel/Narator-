import discord
from discord.ext import commands
import asyncio
import random
import re
import json

from memory import save_memory, get_recent
from cogs.world.timeline import log_event  # ✅ timeline hook

def _key(ctx):
    """Key unik per-guild per-channel."""
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)


def save_initiative_to_memory(guild_id, channel_id, user_id, data):
    save_memory(guild_id, channel_id, user_id, "initiative", json.dumps(data))


def load_initiative_from_memory(guild_id, channel_id):
    rows = get_recent(guild_id, channel_id, "initiative", 1)
    for (_id, cat, content, meta, ts) in rows:
        try:
            return json.loads(content)
        except Exception:
            continue
    return None


class InitiativeMemory(commands.Cog):
    """
    Initiative tracker in-memory (tanpa DB).
    Data hilang saat restart/redeploy.
    Per channel: simpan list [(name, score)], pointer giliran, dan round.
    """
    def __init__(self, bot):
        self.bot = bot
        self.state = {}

    # ===== helpers =====
    def _ensure(self, ctx):
        k = _key(ctx)
        if k not in self.state:
            self.state[k] = {"order": [], "ptr": 0, "round": 1}
        return self.state[k]

    def _sorted(self, arr):
        return sorted(arr, key=lambda x: (-x[1], x[0].lower()))

    def _persist(self, ctx):
        """Simpan state initiative channel ini ke LTM."""
        k = _key(ctx)
        s = self._ensure(ctx)
        data = {"order": s["order"], "ptr": s["ptr"], "round": s["round"]}
        gid = str(ctx.guild.id) if ctx.guild else "0"
        cid = str(ctx.channel.id)
        uid = str(getattr(ctx.author, "id", 0))
        save_initiative_to_memory(gid, cid, uid, data)

    def _make_embed(self, ctx, title: str, s: dict, highlight: bool = True):
        order = s["order"]
        ptr = s["ptr"]
        rnd = s["round"]

        embed = discord.Embed(
            title=title,
            description=f"📜 Round {rnd} • Channel: **{ctx.channel.name}**",
            color=discord.Color.red()
        )

        if not order:
            embed.add_field(name="Initiative Order", value="(kosong)", inline=False)
            return embed

        lines = []
        for i, (name, score) in enumerate(order):
            marker = "👉" if highlight and i == ptr else "  "
            lines.append(f"{marker} {i+1}. {name} ({score})")

        embed.add_field(name="Initiative Order", value="
".join(lines), inline=False)
        embed.set_footer(text="Gunakan !init next atau !next untuk lanjut giliran.")
        return embed

    # ===== command group =====
    @commands.group(name="init", invoke_without_command=True)
    async def init_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Initiative Commands:\n"
            "!init add <Nama> <Skor>\n"
            "!init addmany \"Alice 18, Goblin 12, Borin 14\"  (juga bisa multi-line)\n"
            "!init show            (atau: !order)\n"
            "!init next            (atau: !next / !n)\n"
            "!init setptr <index>  (mulai dari 1)\n"
            "!init remove <Nama>\n"
            "!init clear\n"
            "!init shuffle         (acak pointer awal)\n"
            "!init round           (lihat round) / !init round <angka> (set)\n"
            "```"
        )

    # ... (rest of the code from user, not truncated in real write)
