import math
import re
import discord
from discord.ext import commands
from .history import history   # ✅ import history

def _key(ctx):
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)

def to_int(x, default=0):
    try:
        return int(str(x).strip())
    except Exception:
        return default

def _bar(cur: int, mx: int, width: int = 12) -> str:
    cur = to_int(cur)
    mx = to_int(mx)
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
            out.append({"text": x.get("text",""), "duration": to_int(x.get("duration",-1), -1)})
    return out

class EnemyStatus(commands.Cog):
    """
    In-memory tracker untuk musuh
    - HP / Energy / Stamina
    - Core stats (STR..CHA)
    - Buff & Debuff (dengan durasi)
    """

    def __init__(self, bot):
        self.bot = bot
        self.state = {}

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
        v = s[name]
        v["hp"] = to_int(v.get("hp"))
        v["hp_max"] = to_int(v.get("hp_max"))
        v["energy"] = to_int(v.get("energy"))
        v["energy_max"] = to_int(v.get("energy_max"))
        v["stamina"] = to_int(v.get("stamina"))
        v["stamina_max"] = to_int(v.get("stamina_max"))
        core = v.get("core", {})
        for k in ("str","dex","con","int","wis","cha"):
            core[k] = to_int(core.get(k, 1), 1)
        v["core"] = core
        v["buffs"]   = _normalize_effects_list(v.get("buffs", []))
        v["debuffs"] = _normalize_effects_list(v.get("debuffs", []))
        return v

    def _clamp(self, v: dict):
        for cur, mx in (("hp","hp_max"), ("energy","energy_max"), ("stamina","stamina_max")):
            v[cur] = to_int(v.get(cur))
            v[mx]  = to_int(v.get(mx))
            if v[mx] > 0:
                v[cur] = max(0, min(v[cur], v[mx]))
            else:
                v[cur] = max(0, v[cur])

    async def tick_round(self, ctx):
        s = self._ensure(ctx)
        expired_lines = []
        for name, v in s.items():
            keep = []
            for eff in v.get("buffs", []):
                d = to_int(eff.get("duration", -1), -1)
                if d > 0:
                    d -= 1
                    eff["duration"] = d
                if d == 0:
                    expired_lines.append(f"✨ Buff habis → **{name}**: {eff['text']}")
                else:
                    keep.append(eff)
            v["buffs"] = keep

            keep = []
            for eff in v.get("debuffs", []):
                d = to_int(eff.get("duration", -1), -1)
                if d > 0:
                    d -= 1
                    eff["duration"] = d
                if d == 0:
                    expired_lines.append(f"☠️ Debuff habis → **{name}**: {eff['text']}")
                else:
                    keep.append(eff)
            v["debuffs"] = keep

        if expired_lines:
            await ctx.send("⏳ **Efek berakhir (Musuh):**\n" + "\n".join(expired_lines))

    def _make_embed(self, ctx, data: dict, title="👾 Enemy Status"):
        embed = discord.Embed(
            title=title,
            description=f"Channel: **{ctx.channel.name}**",
            color=discord.Color.red()
        )
        if not data:
            embed.add_field(name="(kosong)", value="Gunakan `!enemy set` atau `!enemy addmany`.", inline=False)
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
    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Enemy Commands:\n"
            "!enemy set <Nama> <HP> <Energy> <Stamina>\n"
            "!enemy addmany\n"
            "!enemy setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>\n"
            "!enemy dmg/heal <Nama> <jumlah> [all]\n"
            "!enemy useenergy/regenenergy <Nama> <jumlah>\n"
            "!enemy usestam/regenstam <Nama> <jumlah>\n"
            "!enemy buff/debuff <Nama> <teks> [durasi|perm]\n"
            "!enemy clearbuff/cleardebuff <Nama>\n"
            "!enemy unbuff/undebuff <Nama> <teks>\n"
            "!enemy show [Nama]\n"
            "!enemy remove <Nama>\n"
            "!enemy clear\n"
            "!enemy tick\n"
            "```"
        )

    @enemy_group.command(name="set")
    async def enemy_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        entry = self._ensure_entry(ctx, name)
        entry.update({
            "hp": to_int(hp), "hp_max": to_int(hp),
            "energy": to_int(energy), "energy_max": to_int(energy),
            "stamina": to_int(stamina), "stamina_max": to_int(stamina)
        })
        await ctx.send(f"👾 Musuh {name} dibuat/diupdate.")

    @enemy_group.command(name="dmg")
    async def enemy_dmg(self, ctx, name: str, amount: int, target: str = None):
        s = self._ensure(ctx)
        affected = []
        if target == "all":
            for ename in list(s.keys()):
                if ename.lower().startswith(name.lower()):
                    v = s[ename]
                    old = v["hp"]
                    v["hp"] = max(0, to_int(v["hp"]) - to_int(amount))
                    self._clamp(v)
                    history.push(ctx, ename, "hp", old, v["hp"])
                    affected.append(f"{ename} → {v['hp']}/{v['hp_max']}")
        else:
            if name not in s:
                suggestions = [n for n in s.keys() if n.lower().startswith(name.lower())]
                if suggestions:
                    return await ctx.send(f"⚠️ Musuh {name} tidak ditemukan. Mungkin maksud: {', '.join(suggestions)}")
                return await ctx.send(f"⚠️ Musuh {name} tidak ditemukan.")
            v = s[name]
            old = v["hp"]
            v["hp"] = max(0, to_int(v["hp"]) - to_int(amount))
            self._clamp(v)
            history.push(ctx, name, "hp", old, v["hp"])
            affected.append(f"{name} → {v['hp']}/{v['hp_max']}")

        if affected:
            await ctx.send("💥 Damage diterapkan:\n" + "\n".join(affected))

    @enemy_group.command(name="heal")
    async def enemy_heal(self, ctx, name: str, amount: int, target: str = None):
        s = self._ensure(ctx)
        affected = []
        if target == "all":
            for ename in list(s.keys()):
                if ename.lower().startswith(name.lower()):
                    v = s[ename]
                    old = v["hp"]
                    if to_int(v["hp_max"]) == 0:
                        v["hp"] = to_int(v["hp"]) + to_int(amount)
                    else:
                        v["hp"] = min(to_int(v["hp_max"]), to_int(v["hp"]) + to_int(amount))
                    self._clamp(v)
                    history.push(ctx, ename, "hp", old, v["hp"])
                    affected.append(f"{ename} → {v['hp']}/{v['hp_max']}")
        else:
            if name not in s:
                suggestions = [n for n in s.keys() if n.lower().startswith(name.lower())]
                if suggestions:
                    return await ctx.send(f"⚠️ Musuh {name} tidak ditemukan. Mungkin maksud: {', '.join(suggestions)}")
                return await ctx.send(f"⚠️ Musuh {name} tidak ditemukan.")
            v = s[name]
            old = v["hp"]
            if to_int(v["hp_max"]) == 0:
                v["hp"] = to_int(v["hp"]) + to_int(amount)
            else:
                v["hp"] = min(to_int(v["hp_max"]), to_int(v["hp"]) + to_int(amount))
            self._clamp(v)
            history.push(ctx, name, "hp", old, v["hp"])
            affected.append(f"{name} → {v['hp']}/{v['hp_max']}")

        if affected:
            await ctx.send("💚 Heal diterapkan:\n" + "\n".join(affected))

    @enemy_group.command(name="useenergy")
    async def enemy_useenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["energy"]
        v["energy"] = to_int(v["energy"]) - to_int(amount)
        self._clamp(v)
        history.push(ctx, name, "energy", old, v["energy"])
        await ctx.send(f"🔋 {name} menggunakan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @enemy_group.command(name="regenenergy")
    async def enemy_regenenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["energy"]
        v["energy"] = to_int(v["energy"]) + to_int(amount)
        self._clamp(v)
        history.push(ctx, name, "energy", old, v["energy"])
        await ctx.send(f"🔋 {name} memulihkan {amount} Energy. Sekarang {v['energy']}/{v['energy_max']}.")

    @enemy_group.command(name="usestam")
    async def enemy_usestam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["stamina"]
        v["stamina"] = to_int(v["stamina"]) - to_int(amount)
        self._clamp(v)
        history.push(ctx, name, "stamina", old, v["stamina"])
        await ctx.send(f"⚡ {name} menggunakan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    @enemy_group.command(name="regenstam")
    async def enemy_regenstam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        old = v["stamina"]
        v["stamina"] = to_int(v["stamina"]) + to_int(amount)
        self._clamp(v)
        history.push(ctx, name, "stamina", old, v["stamina"])
        await ctx.send(f"⚡ {name} memulihkan {amount} Stamina. Sekarang {v['stamina']}/{v['stamina_max']}.")

    @enemy_group.command(name="buff")
    async def enemy_buff(self, ctx, name: str, text: str, duration: str = "perm"):
        v = self._ensure_entry(ctx, name)
        dur = -1 if duration.lower() == "perm" else to_int(duration, -1)
        v["buffs"].append({"text": text, "duration": dur})
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {_format_effect(v['buffs'][-1])}")

    @enemy_group.command(name="debuff")
    async def enemy_debuff(self, ctx, name: str, text: str, duration: str = "perm"):
        v = self._ensure_entry(ctx, name)
        dur = -1 if duration.lower() == "perm" else to_int(duration, -1)
        v["debuffs"].append({"text": text, "duration": dur})
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {_format_effect(v['debuffs'][-1])}")

    @enemy_group.command(name="clearbuff")
    async def enemy_clearbuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"] = []
        await ctx.send(f"✨ Semua buff dihapus dari {name}.")

    @enemy_group.command(name="cleardebuff")
    async def enemy_cleardebuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"] = []
        await ctx.send(f"☠️ Semua debuff dihapus dari {name}.")

    @enemy_group.command(name="unbuff")
    async def enemy_unbuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        before = len(v["buffs"])
        v["buffs"] = [e for e in v["buffs"] if e["text"] != text]
        await ctx.send("✨ Buff dihapus." if len(v["buffs"]) < before else "⚠️ Buff tidak ditemukan.")

    @enemy_group.command(name="undebuff")
    async def enemy_undebuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        before = len(v["debuffs"])
        v["debuffs"] = [e for e in v["debuffs"] if e["text"] != text]
        await ctx.send("☠️ Debuff dihapus." if len(v["debuffs"]) < before else "⚠️ Debuff tidak ditemukan.")

    @enemy_group.command(name="show")
    async def enemy_show(self, ctx, name: str = None):
        s = self._ensure(ctx)
        if not s:
            return await ctx.send("⚠️ Belum ada musuh.")
        if name:
            filtered = {n:v for n,v in s.items() if n.lower().startswith(name.lower())}
            if not filtered:
                return await ctx.send(f"⚠️ Musuh {name} tidak ditemukan.")
            for ename, edata in filtered.items():
                embed = self._make_embed(ctx, {ename: edata})
                await ctx.send(embed=embed)
        else:
            for ename, edata in s.items():
                embed = self._make_embed(ctx, {ename: edata})
                await ctx.send(embed=embed)

    @enemy_group.command(name="remove")
    async def enemy_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        if name in s:
            del s[name]
            await ctx.send(f"🗑️ Musuh {name} dihapus.")
        else:
            await ctx.send("⚠️ Nama musuh tidak ditemukan.")

    @enemy_group.command(name="clear")
    async def enemy_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Semua musuh di channel ini direset.")

    @enemy_group.command(name="tick")
    async def enemy_tick(self, ctx):
        await self.tick_round(ctx)

async def setup(bot):
    await bot.add_cog(EnemyStatus(bot))
