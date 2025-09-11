import math
import discord
from discord.ext import commands
from .history import history   # ✅ import history

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

def _format_effect(e):
    d = e.get("duration", -1)
    return f"{e['text']} [Durasi: {d if d >= 0 else 'Permanent'}]"

def _normalize_effects_list(lst):
    out = []
    for x in lst:
        if isinstance(x, str):
            out.append({"text": x, "duration": -1})
        elif isinstance(x, dict):
            out.append({"text": x.get("text",""), "duration": int(x.get("duration",-1))})
    return out

class CharacterStatus(commands.Cog):
    """
    In-memory tracker:
    - HP / Energy / Stamina (+ max)
    - Core stats: STR, DEX, CON, INT, WIS, CHA
    - Buffs & Debuffs (dengan durasi)
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
        s[name]["buffs"]   = _normalize_effects_list(s[name]["buffs"])
        s[name]["debuffs"] = _normalize_effects_list(s[name]["debuffs"])
        return s[name]

    def _clamp(self, v: dict):
        for cur, mx in (("hp","hp_max"), ("energy","energy_max"), ("stamina","stamina_max")):
            if v[mx] > 0:
                v[cur] = max(0, min(v[cur], v[mx]))
            else:
                v[cur] = max(0, v[cur])

    async def tick_round(self, ctx):
        """Kurangi durasi buff/debuff per round dan hapus yang expired"""
        s = self._ensure(ctx)
        expired_lines = []
        for name, v in s.items():
            keep = []
            for eff in v["buffs"]:
                d = eff["duration"]
                if d > 0:
                    d -= 1
                    eff["duration"] = d
                if d == 0:
                    expired_lines.append(f"✨ Buff habis → **{name}**: {eff['text']}")
                else:
                    keep.append(eff)
            v["buffs"] = keep

            keep = []
            for eff in v["debuffs"]:
                d = eff["duration"]
                if d > 0:
                    d -= 1
                    eff["duration"] = d
                if d == 0:
                    expired_lines.append(f"☠️ Debuff habis → **{name}**: {eff['text']}")
                else:
                    keep.append(eff)
            v["debuffs"] = keep

        if expired_lines:
            await ctx.send("⏳ **Efek berakhir (Karakter):**\n" + "\n".join(expired_lines))

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

            buffs = "\n".join([f"✅ {_format_effect(b)}" for b in v["buffs"]]) if v["buffs"] else "-"
            debuffs = "\n".join([f"❌ {_format_effect(d)}" for d in v["debuffs"]]) if v["debuffs"] else "-"

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
            "!status dmg/heal <Nama> <jumlah>\n"
            "!status buff <Nama> <teks> [durasi|perm]\n"
            "!status debuff <Nama> <teks> [durasi|perm]\n"
            "!status clearbuff <Nama>\n"
            "!status cleardebuff <Nama>\n"
            "!status unbuff <Nama> <teks>\n"
            "!status undebuff <Nama> <teks>\n"
            "!status show [Nama]\n"
            "!status remove <Nama>\n"
            "!status clear\n"
            "!status tick (kurangi durasi efek 1 round)\n"
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

    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["hp"]
        v["hp"] = max(0, v["hp"] - amount)
        self._clamp(v)
        history.push(ctx, name, "hp", old, v["hp"])
        await ctx.send(f"💥 {name} menerima {amount} damage. Sekarang {v['hp']}/{v['hp_max']}.")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["hp"]
        v["hp"] = v["hp"] + amount if v["hp_max"] == 0 else min(v["hp_max"], v["hp"] + amount)
        self._clamp(v)
        history.push(ctx, name, "hp", old, v["hp"])
        await ctx.send(f"❤️ {name} dipulihkan {amount} HP. Sekarang {v['hp']}/{v['hp_max']}.")

    @status_group.command(name="buff")
    async def status_buff(self, ctx, name: str, text: str, duration: str = "perm"):
        v = self._ensure_entry(ctx, name)
        dur = -1 if duration.lower() == "perm" else int(duration)
        v["buffs"].append({"text": text, "duration": dur})
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {_format_effect(v['buffs'][-1])}")

    @status_group.command(name="debuff")
    async def status_debuff(self, ctx, name: str, text: str, duration: str = "perm"):
        v = self._ensure_entry(ctx, name)
        dur = -1 if duration.lower() == "perm" else int(duration)
        v["debuffs"].append({"text": text, "duration": dur})
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {_format_effect(v['debuffs'][-1])}")

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

    @status_group.command(name="unbuff")
    async def status_unbuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        before = len(v["buffs"])
        v["buffs"] = [e for e in v["buffs"] if e["text"] != text]
        await ctx.send("✨ Buff dihapus." if len(v["buffs"]) < before else "⚠️ Buff tidak ditemukan.")

    @status_group.command(name="undebuff")
    async def status_undebuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        before = len(v["debuffs"])
        v["debuffs"] = [e for e in v["debuffs"] if e["text"] != text]
        await ctx.send("☠️ Debuff dihapus." if len(v["debuffs"]) < before else "⚠️ Debuff tidak ditemukan.")

    @status_group.command(name="show")
    async def status_show(self, ctx, name: str = None):
        s = self._ensure(ctx)
        if not s:
            return await ctx.send("⚠️ Belum ada data karakter.")

        if name:
            if name not in s:
                return await ctx.send(f"⚠️ Karakter {name} tidak ditemukan.")
            data = {name: s[name]}
            embed = self._make_embed(ctx, data)
            await ctx.send(embed=embed)
        else:
            for cname, cdata in s.items():
                embed = self._make_embed(ctx, {cname: cdata})
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
        v = self._ensure_entry(ctx, name)
        old = v["energy"]
        v["energy"] -= amount
        self._clamp(v)
        history.push(ctx, name, "energy", old, v["energy"])
        await ctx.send(f"🔋 {name} menggunakan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @status_group.command(name="regenenergy")
    async def status_regenenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["energy"]
        v["energy"] += amount
        self._clamp(v)
        history.push(ctx, name, "energy", old, v["energy"])
        await ctx.send(f"🔋 {name} memulihkan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @status_group.command(name="usestam")
    async def status_usestam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["stamina"]
        v["stamina"] -= amount
        self._clamp(v)
        history.push(ctx, name, "stamina", old, v["stamina"])
        await ctx.send(f"⚡ {name} menggunakan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    @status_group.command(name="regenstam")
    async def status_regenstam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["stamina"]
        v["stamina"] += amount
        self._clamp(v)
        history.push(ctx, name, "stamina", old, v["stamina"])
        await ctx.send(f"⚡ {name} memulihkan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    @status_group.command(name="tick")
    async def status_tick(self, ctx):
        await self.tick_round(ctx)

    # ---------- Quick Commands ----------
    @commands.command(name="stat")
    async def quick_stat(self, ctx, name: str):
        await self.status_show(ctx, name=name)

    @commands.command(name="party")
    async def quick_party(self, ctx):
        await self.status_show(ctx)

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
