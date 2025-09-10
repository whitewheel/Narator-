import discord
from discord.ext import commands

def _key(ctx):
    """Key unik per-guild per-channel."""
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)

class InitiativeMemory(commands.Cog):
    """
    Initiative tracker in-memory (tanpa DB).
    Data hilang saat restart/redeploy.
    Per channel: simpan list [(name, score)] dan pointer giliran.
    """
    def __init__(self, bot):
        self.bot = bot
        # Struktur data: { (guild_id, channel_id): {"order":[(name,score),...], "ptr":int} }
        self.state = {}

    # ===== helpers =====
    def _ensure(self, ctx):
        k = _key(ctx)
        if k not in self.state:
            self.state[k] = {"order": [], "ptr": 0}
        return self.state[k]

    def _sorted(self, arr):
        # urut skor desc, nama asc biar deterministic
        return sorted(arr, key=lambda x: (-x[1], x[0].lower()))

    def _fmt(self, order, ptr):
        if not order:
            return "Initiative Order\n(kosong)"
        lines = []
        n = len(order)
        ptr = ptr % n if n > 0 else 0
        for i, (name, score) in enumerate(order):
            marker = "👉 " if i == ptr else "   "
            lines.append(f"{marker}{i+1}. {name} ({score})")
        return "Initiative Order\n" + "\n".join(lines)

    # ===== command group =====
    @commands.group(name="init", invoke_without_command=True)
    async def init_group(self, ctx):
        """Initiative tracker (in-memory).
        Subcommands: add|show|next|remove|clear|setptr
        """
        await ctx.send(
            "```Gunakan:\n"
            "!init add <Nama> <Skor>\n"
            "!init show\n"
            "!init next\n"
            "!init remove <Nama>\n"
            "!init clear\n"
            "!init setptr <index>   (opsional; mulai dari 1)\n"
            "```"
        )

    @init_group.command(name="add")
    async def init_add(self, ctx, name: str, score: int):
        """Tambah/ubah peserta dengan skor."""
        s = self._ensure(ctx)
        # ganti kalau nama sama sudah ada
        existing = {n: sc for (n, sc) in s["order"]}
        existing[name] = score
        s["order"] = self._sorted(list(existing.items()))
        # sinkronkan ptr supaya tetap valid
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        await ctx.send(f"✅ Ditambahkan/diupdate: **{name}** = {score}")

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
        text = self._fmt(s["order"], s["ptr"])
        await ctx.send(f"```{text}```")

    @init_group.command(name="next")
    async def init_next(self, ctx):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta. Tambah dengan `!init add <Nama> <Skor>`")
        s["ptr"] = (s["ptr"] + 1) % len(s["order"])
        await self.init_show(ctx)
        current = s["order"][s["ptr"]][0]
        await ctx.send(f"⏭️ Giliran **{current}**")

    @init_group.command(name="setptr")
    async def init_setptr(self, ctx, index: int):
        """Set pointer manual (mulai dari 1)."""
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        idx = max(1, min(index, len(s["order"]))) - 1
        s["ptr"] = idx
        await self.init_show(ctx)

    @init_group.command(name="clear")
    async def init_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Initiative channel ini direset.")

async def setup(bot):
    await bot.add_cog(InitiativeMemory(bot))
