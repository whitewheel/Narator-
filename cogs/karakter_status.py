import discord
from discord.ext import commands

def _key(ctx):
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)

def _bar(cur: int, mx: int, width: int = 12) -> str:
    if mx <= 0:
        return "░" * width
    cur = max(0, min(cur, mx))
    filled = int(round(width * (cur / mx)))
    return "█" * filled + "░" * (width - filled)

class CharacterStatus(commands.Cog):
    """
    In-memory tracker untuk Karakter: HP / Energy / Stamina (+ max).
    Per channel → { nama: {hp, hp_max, energy, energy_max, stamina, stamina_max} }
    """
    def __init__(self, bot):
        self.bot = bot
        self.state = {}  # {(guild, channel): {name: {...}}}

    # ---------- helpers ----------
    def _ensure(self, ctx):
        k = _key(ctx)
        if k not in self.state:
            self.state[k] = {}
        return self.state[k]

    def _ensure_entry(self, ctx, name: str):
        s = self._ensure(ctx)
        if name not in s:
            s[name] = {
                "hp": 0, "hp_max": 0,
                "energy": 0, "energy_max": 0,
                "stamina": 0, "stamina_max": 0
            }
        return s[name]

    def _clamp(self, v: dict):
        # batasi current ke [0, max] jika max > 0
        for cur, mx in (("hp","hp_max"), ("energy","energy_max"), ("stamina","stamina_max")):
            if v[mx] > 0:
                v[cur] = max(0, min(v[cur], v[mx]))
            else:
                v[cur] = max(0, v[cur])

    # ---------- commands ----------
    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        """Karakter Status: HP / Energy / Stamina"""
        await ctx.send(
            "```Gunakan:\n"
            "!status set <Nama> <HP> <Energy> <Stamina>     (set current & max)\n"
            "!status setmax <Nama> <HPmax> <EnergyMax> <StaminaMax>\n"
            "!status dmg <Nama> <jumlah>\n"
            "!status heal <Nama> <jumlah>\n"
            "!status useenergy <Nama> <jumlah>\n"
            "!status regenenergy <Nama> <jumlah>\n"
            "!status usestam <Nama> <jumlah>\n"
            "!status regenstam <Nama> <jumlah>\n"
            "!status show\n"
            "!status remove <Nama>\n"
            "!status clear\n```"
        )

    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        s = self._ensure(ctx)
        s[name] = {
            "hp": hp, "hp_max": hp,
            "energy": energy, "energy_max": energy,
            "stamina": stamina, "stamina_max": stamina
        }
        await ctx.send(f"✅ **{name}** ditambahkan.")

    @status_group.command(name="setmax")
    async def status_setmax(self, ctx, name: str, hp_max: int, energy_max: int, stamina_max: int):
        v = self._ensure_entry(ctx, name)
        v["hp_max"] = max(0, hp_max)
        v["energy_max"] = max(0, energy_max)
        v["stamina_max"] = max(0, stamina_max)
        self._clamp(v)
        await ctx.send(f"✅ Max status **{name}** diupdate.")

    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] = max(0, v["hp"] - amount)
        self._clamp(v)
        await ctx.send(f"💥 {name} kena {amount} dmg!")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] += amount
        self._clamp(v)
        await ctx.send(f"✨ {name} heal {amount} HP!")

    @status_group.command(name="useenergy")
    async def status_useenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] = max(0, v["energy"] - amount)
        self._clamp(v)
        await ctx.send(f"🔋 {name} pakai {amount} energy!")

    @status_group.command(name="regenenergy")
    async def status_regenenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] += amount
        self._clamp(v)
        await ctx.send(f"🔋 {name} regen {amount} energy!")

    @status_group.command(name="usestam")
    async def status_usestam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] = max(0, v["stamina"] - amount)
        self._clamp(v)
        await ctx.send(f"⚡ {name} pakai {amount} stamina!")

    @status_group.command(name="regenstam")
    async def status_regenstam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] += amount
        self._clamp(v)
        await ctx.send(f"⚡ {name} regen {amount} stamina!")

    @status_group.command(name="show")
    async def status_show(self, ctx):
        s = self._ensure(ctx)
        if not s:
            return await ctx.send("⚠️ Belum ada data. Tambah dengan `!status set <Nama> <HP> <Energy> <Stamina>`")

        # hitung rata-rata HP untuk warna embed
        total_cur, total_max = 0, 0
        for v in s.values():
            total_cur += v["hp"]
            total_max += v["hp_max"] if v["hp_max"] else v["hp"]

        hp_ratio = total_cur / total_max if total_max > 0 else 1
        if hp_ratio > 0.7:
            color = discord.Color.green()
        elif hp_ratio > 0.3:
            color = discord.Color.gold()
        else:
            color = discord.Color.red()

        embed = discord.Embed(
            title="🧍 Karakter Status",
            description=f"Status party di channel **{ctx.channel.name}**",
            color=color
        )

        for name, v in s.items():
            hp_text = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else str(v['hp'])
            en_text = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else str(v['energy'])
            st_text = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else str(v['stamina'])

            value = (
                f"❤️ HP: {hp_text}  [{_bar(v['hp'], v['hp_max'])}]\n"
                f"🔋 Energy: {en_text}  [{_bar(v['energy'], v['energy_max'])}]\n"
                f"⚡ Stamina: {st_text}  [{_bar(v['stamina'], v['stamina_max'])}]"
            )
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="Visual bar: █ penuh | ░ kosong")
        await ctx.send(embed=embed)

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        if name in s:
            del s[name]
            await ctx.send(f"🗑️ **{name}** dihapus.")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @status_group.command(name="clear")
    async def status_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Data Karakter Status channel ini direset.")

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
