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

    def _fmt_all(self, s: dict) -> str:
        if not s:
            return "Karakter Status\n(kosong) Gunakan !status set <Nama> <HP> <Energy> <Stamina>"
        lines = ["Karakter Status"]
        # urut alfabet biar rapi
        for n in sorted(s.keys(), key=lambda x: x.lower()):
            v = s[n]
            hp = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else f"{v['hp']}"
            en = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else f"{v['energy']}"
            st = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else f"{v['stamina']}"
            lines.append(
                f"{n}:\n"
                f"  ❤️ {hp} [{_bar(v['hp'], v['hp_max'])}]\n"
                f"  🔋 {en} [{_bar(v['energy'], v['energy_max'])}]\n"
                f"  ⚡ {st} [{_bar(v['stamina'], v['stamina_max'])}]"
            )
        return "\n".join(lines)

    def _fmt_one(self, name: str, v: dict) -> str:
        hp = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else f"{v['hp']}"
        en = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else f"{v['energy']}"
        st = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else f"{v['stamina']}"
        return (
            f"{name}:\n"
            f"  ❤️ {hp} [{_bar(v['hp'], v['hp_max'])}]\n"
            f"  🔋 {en} [{_bar(v['energy'], v['energy_max'])}]\n"
            f"  ⚡ {st} [{_bar(v['stamina'], v['stamina_max'])}]"
        )

    def _clamp(self, v: dict):
        # batasi current ke [0, max] jika max > 0
        for k in (("hp","hp_max"), ("energy","energy_max"), ("stamina","stamina_max")):
            cur, mx = k
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
        await ctx.send(f"```{self._fmt_one(name, s[name])}```")

    @status_group.command(name="setmax")
    async def status_setmax(self, ctx, name: str, hp_max: int, energy_max: int, stamina_max: int):
        v = self._ensure_entry(ctx, name)
        v["hp_max"] = max(0, hp_max)
        v["energy_max"] = max(0, energy_max)
        v["stamina_max"] = max(0, stamina_max)
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] = max(0, v["hp"] - amount)
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] += amount
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="useenergy")
    async def status_useenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] = max(0, v["energy"] - amount)
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="regenenergy")
    async def status_regenenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] += amount
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="usestam")
    async def status_usestam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] = max(0, v["stamina"] - amount)
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="regenstam")
    async def status_regenstam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] += amount
        self._clamp(v)
        await ctx.send(f"```{self._fmt_one(name, v)}```")

    @status_group.command(name="show")
    async def status_show(self, ctx):
        s = self._ensure(ctx)
        await ctx.send(f"```{self._fmt_all(s)}```")

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
