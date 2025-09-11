import math
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

def _mod(score: int) -> int:
    return math.floor(score / 5)

class CharacterStatus(commands.Cog):
    """
    In-memory tracker:
    - HP / Energy / Stamina (+ max)
    - Core stats: STR, DEX, CON, INT, WIS, CHA
    - Buffs & Debuffs
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
                "stamina": 0, "stamina_max": 0,
                "core": {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
                "buffs": [],
                "debuffs": []
            }
        return s[name]

    def _clamp(self, v: dict):
        for cur, mx in (("hp","hp_max"), ("energy","energy_max"), ("stamina","stamina_max")):
            if v[mx] > 0:
                v[cur] = max(0, min(v[cur], v[mx]))
            else:
                v[cur] = max(0, v[cur])

    def _make_embed(self, ctx, data: dict, title="🧍 Karakter Status"):
        embed = discord.Embed(
            title=title,
            description=f"Channel: **{ctx.channel.name}**",
            color=discord.Color.blurple()
        )
        if not data:
            embed.add_field(name="(kosong)", value="Gunakan `!status set` untuk menambah karakter.", inline=False)
            return embed

        for name, v in data.items():
            hp_text = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else str(v['hp'])
            en_text = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else str(v['energy'])
            st_text = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else str(v['stamina'])

            core = v["core"]
            stats_line = (
                f"STR {core['str']} ({_mod(core['str']):+d}) | "
                f"DEX {core['dex']} ({_mod(core['dex']):+d}) | "
                f"CON {core['con']} ({_mod(core['con']):+d})\n"
                f"INT {core['int']} ({_mod(core['int']):+d}) | "
                f"WIS {core['wis']} ({_mod(core['wis']):+d}) | "
                f"CHA {core['cha']} ({_mod(core['cha']):+d})"
            )

            buffs = "\n".join([f"✅ {b}" for b in v["buffs"]]) if v["buffs"] else "-"
            debuffs = "\n".join([f"❌ {d}" for d in v["debuffs"]]) if v["debuffs"] else "-"

            value = (
                f"❤️ HP: {hp_text} [{_bar(v['hp'], v['hp_max'])}]\n"
                f"🔋 Energy: {en_text} [{_bar(v['energy'], v['energy_max'])}]\n"
                f"⚡ Stamina: {st_text} [{_bar(v['stamina'], v['stamina_max'])}]\n\n"
                f"📊 Stats:\n{stats_line}\n\n"
                f"✨ Buffs:\n{buffs}\n\n"
                f"☠️ Debuffs:\n{debuffs}"
            )
            embed.add_field(name=name, value=value, inline=False)
        return embed

    # ---------- commands ----------
    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Status Commands:\n"
            "!status set <Nama> <HP> <Energy> <Stamina>\n"
            "!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>\n"
            "!status buff <Nama> <teks>\n"
            "!status debuff <Nama> <teks>\n"
            "!status clearbuff <Nama>\n"
            "!status cleardebuff <Nama>\n"
            "!status show [Nama]\n"
            "!status remove <Nama>\n"
            "!status clear\n"
            "```"
        )

    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        entry = self._ensure_entry(ctx, name)
        entry.update({
            "hp": hp, "hp_max": hp,
            "energy": energy, "energy_max": energy,
            "stamina": stamina, "stamina_max": stamina
        })
        await ctx.send(f"✅ {name} dibuat/diupdate.")

    @status_group.command(name="setcore")
    async def status_setcore(self, ctx, name: str, str_: int, dex: int, con: int, int_: int, wis: int, cha: int):
        entry = self._ensure_entry(ctx, name)
        entry["core"] = {"str": str_, "dex": dex, "con": con, "int": int_, "wis": wis, "cha": cha}
        await ctx.send(f"✅ Core stats {name} diupdate.")

    @status_group.command(name="buff")
    async def status_buff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"].append(text)
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @status_group.command(name="debuff")
    async def status_debuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"].append(text)
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    @status_group.command(name="clearbuff")
    async def status_clearbuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"] = []
        await ctx.send(f"✨ Semua buff dihapus dari {name}.")

    @status_group.command(name="cleardebuff")
    async def status_cleardebuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"] = []
        await ctx.send(f"☠️ Semua debuff dihapus dari {name}.")

    @status_group.command(name="show")
    async def status_show(self, ctx, name: str = None):
        s = self._ensure(ctx)
        if not s:
            return await ctx.send("⚠️ Belum ada data karakter.")
        if name:
            if name not in s:
                return await ctx.send(f"⚠️ Karakter {name} tidak ditemukan.")
            data = {name: s[name]}
        else:
            data = s
        embed = self._make_embed(ctx, data)
        await ctx.send(embed=embed)

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        if name in s:
            del s[name]
            await ctx.send(f"🗑️ {name} dihapus.")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @status_group.command(name="clear")
    async def status_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Semua status di channel ini direset.")

    @status_group.command(name="useenergy")
    async def status_useenergy(self, ctx, name: str, amount: int):
        """Kurangi Energy karakter"""
        v = self._ensure_entry(ctx, name)
        v["energy"] -= amount
        self._clamp(v)
        await ctx.send(f"🔋 {name} menggunakan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @status_group.command(name="regenenergy")
    async def status_regenenergy(self, ctx, name: str, amount: int):
        """Tambah Energy karakter"""
        v = self._ensure_entry(ctx, name)
        v["energy"] += amount
        self._clamp(v)
        await ctx.send(f"🔋 {name} memulihkan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @status_group.command(name="usestam")
    async def status_usestam(self, ctx, name: str, amount: int):
        """Kurangi Stamina karakter"""
        v = self._ensure_entry(ctx, name)
        v["stamina"] -= amount
        self._clamp(v)
        await ctx.send(f"⚡ {name} menggunakan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    @status_group.command(name="regenstam")
    async def status_regenstam(self, ctx, name: str, amount: int):
        """Tambah Stamina karakter"""
        v = self._ensure_entry(ctx, name)
        v["stamina"] += amount
        self._clamp(v)
        await ctx.send(f"⚡ {name} memulihkan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    # ---------- Quick Commands ----------
    @commands.command(name="stat")
    async def quick_stat(self, ctx, name: str):
        """Alias cepat: !stat <Nama> → status 1 karakter"""
        await self.status_show(ctx, name=name)

    @commands.command(name="party")
    async def quick_party(self, ctx):
        """Alias cepat: !party → status semua karakter"""
        await self.status_show(ctx)

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
