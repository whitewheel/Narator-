import discord
from discord.ext import commands
import asyncio
import random

def _key(ctx):
    """Key unik per-guild per-channel."""
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)

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

        embed.add_field(name="Initiative Order", value="\n".join(lines), inline=False)
        embed.set_footer(text="Gunakan !init next atau !next untuk lanjut giliran.")
        return embed

    # ===== command group =====
    @commands.group(name="init", invoke_without_command=True)
    async def init_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Initiative Commands:\n"
            "!init add <Nama> <Skor>\n"
            "!init addmany \"Alice 18, Goblin 12, Borin 14\"\n"
            "!init show            (atau: !order)\n"
            "!init next            (atau: !next / !n)\n"
            "!init setptr <index>  (mulai dari 1)\n"
            "!init remove <Nama>\n"
            "!init clear\n"
            "!init shuffle         (acak pointer awal)\n"
            "!init round           (lihat round) / !init round <angka> (set)\n"
            "```"
        )

    @init_group.command(name="add")
    async def init_add(self, ctx, name: str, score: int):
        s = self._ensure(ctx)
        existing = {n: sc for (n, sc) in s["order"]}
        existing[name] = score
        s["order"] = self._sorted(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        await ctx.send(f"✅ Ditambahkan/diupdate: **{name}** = {score}")

    @init_group.command(name="addmany")
    async def init_addmany(self, ctx, *, entries: str):
        """
        Tambah banyak peserta sekaligus.
        Format: "Alice 18, Goblin 12, Borin 15"
        """
        s = self._ensure(ctx)
        existing = {n: sc for (n, sc) in s["order"]}
        count = 0

        for part in entries.split(","):
            part = part.strip()
            if not part:
                continue
            toks = part.rsplit(" ", 1)
            if len(toks) != 2 or not toks[1].isdigit():
                continue
            name, score = toks[0], int(toks[1])
            existing[name] = score
            count += 1

        s["order"] = self._sorted(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        await ctx.send(f"✅ Ditambahkan {count} peserta sekaligus.")

    @init_group.command(name="remove")
    async def init_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        before = len(s["order"])
        s["order"] = [(n, sc) for (n, sc) in s["order"] if n != name]
        if len(s["order"]) < before:
            s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
            await ctx.send(f"🗑️ Hapus **{name}**")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @init_group.command(name="show")
    async def init_show(self, ctx):
        s = self._ensure(ctx)
        embed = self._make_embed(ctx, "⚔️ Initiative Order", s)
        await ctx.send(embed=embed)

    @init_group.command(name="next")
    async def init_next(self, ctx):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta. Tambah dengan `!init add <Nama> <Skor>`")

        s["ptr"] = (s["ptr"] + 1) % len(s["order"])
        if s["ptr"] == 0:
            s["round"] += 1
            await ctx.send(f"🔄 **Round {s['round']} dimulai!**")

        embed = self._make_embed(ctx, "⏭️ Initiative Next", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran", value=f"✨ **{current}**", inline=False)
        await ctx.send(embed=embed)

    @init_group.command(name="setptr")
    async def init_setptr(self, ctx, index: int):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        idx = max(1, min(index, len(s["order"]))) - 1
        s["ptr"] = idx
        embed = self._make_embed(ctx, "📌 Pointer Diset Manual", s)
        await ctx.send(embed=embed)

    @init_group.command(name="clear")
    async def init_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Initiative channel ini direset.")

    @init_group.command(name="round")
    async def init_round(self, ctx, value: int = None):
        s = self._ensure(ctx)
        if value is None:
            return await ctx.send(f"📜 Round saat ini: **{s['round']}**")
        s["round"] = max(1, value)
        await ctx.send(f"📜 Round diset ke **{s['round']}**")

    @init_group.command(name="shuffle")
    async def init_shuffle(self, ctx):
        """
        Acak pointer giliran awal.
        Tidak mengubah urutan initiative, hanya siapa yang jalan dulu.
        """
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        s["ptr"] = random.randint(0, len(s["order"]) - 1)
        embed = self._make_embed(ctx, "🎲 Shuffle Giliran", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    # ===== engage (dramatis start) =====
    @commands.command(name="engage", aliases=["start", "begin"])
    async def engage(self, ctx):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada data initiative. Tambahkan dulu dengan `!init add <Nama> <Skor>`.")

        drum = await ctx.send("🥁 Mengocok urutan giliran...")
        await asyncio.sleep(2)
        await drum.delete()

        embed = self._make_embed(ctx, "⚔️ Encounter Dimulai!", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    # ===== Aliases global =====
    @commands.command(name="next", aliases=["n"])
    async def alias_next(self, ctx):
        await self.init_next(ctx)

    @commands.command(name="order")
    async def alias_order(self, ctx):
        await self.init_show(ctx)

async def setup(bot):
    await bot.add_cog(InitiativeMemory(bot))
