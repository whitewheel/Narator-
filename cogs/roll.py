import re
import random
import discord
from discord.ext import commands

# Regex dasar
DICE_RE = re.compile(r"(?P<count>\d*)d(?P<sides>\d+)", re.IGNORECASE)
MOD_NUM_RE = re.compile(r"(?P<sign>[+-])\s*(?P<val>\d+)")
MOD_NAME_RE = re.compile(r"(?P<sign>[+-])\s*(?P<name>[A-Za-z_][\w\-]*)")

# Batas aman
MAX_DICE = 100
MAX_SIDES = 1000

BUFF_DEBUFF_RE = re.compile(r"^(?P<sign>[+-])\s*(?P<val>\d+)\s*(?P<stat>STR|DEX|CON|INT|WIS|CHA)\b", re.IGNORECASE)

def _parse_expression(expr: str):
    expr = re.sub(r"[dD]{2,}", "d", expr)  # toleransi dd20 → d20
    cleaned = expr

    # dice
    dice_terms = []
    for m in DICE_RE.finditer(expr):
        count = int(m.group("count")) if m.group("count") else 1
        sides = int(m.group("sides"))
        dice_terms.append((count, sides))

    # core stat refs / named mods
    stat_refs = []
    named = []
    for m in MOD_NAME_RE.finditer(expr):
        sign = -1 if m.group("sign") == "-" else 1
        name = m.group("name").lower()
        if name in ["str","dex","con","int","wis","cha"]:
            stat_refs.append((name, sign))
        else:
            named.append((name, sign))

    # plain number mods
    temp = DICE_RE.sub(" ", expr)
    temp = MOD_NAME_RE.sub(" ", temp)
    mods = []
    for m in MOD_NUM_RE.finditer(temp):
        sign = -1 if m.group("sign") == "-" else 1
        val = int(m.group("val")) * sign
        mods.append(val)

    return dice_terms, mods, stat_refs, cleaned, named

def _roll_dice(dice_terms):
    out = []
    for count, sides in dice_terms:
        c = max(0, min(count, MAX_DICE))
        s = max(1, min(sides, MAX_SIDES))
        rolls = [random.randint(1, s) for _ in range(c)]
        out.append({"count": c, "sides": s, "rolls": rolls, "sum": sum(rolls)})
    return out

def _crit_info(dice_details):
    crit = False
    fail = False
    all_d20_rolls = []
    for d in dice_details:
        if d["sides"] == 20 and d["count"] > 0:
            all_d20_rolls.extend(d["rolls"])
    if all_d20_rolls:
        if max(all_d20_rolls) == 20:
            crit = True
        if all(r == 1 for r in all_d20_rolls):
            fail = True
    return crit, fail

def _fmt_mods(mods, stat_mods, buff_mods, named_mods):
    parts = []
    if mods:
        parts.append(" ".join([f"{'+' if v>=0 else ''}{v}" for v in mods]))
    for name, v in stat_mods:
        parts.append(f"{'+' if v>=0 else ''}{v} ({name.upper()})")
    for name, v, src in buff_mods:
        parts.append(f"{'+' if v>=0 else ''}{v} ({name.upper()} {src})")
    for name, v in named_mods:
        parts.append(f"{'+' if v>=0 else ''}{v} ({name})")
    return " + ".join(parts) if parts else "0"

def _ability_mod(score: int) -> int:
    return (score - 10) // 2

class DiceCog(commands.Cog):
    """Dice roller dengan core stat + buff/debuff integration"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, query: str):
        """
        !roll <expresi> [vs <target>] / [dc <target>]
        Bisa pakai core stat dengan "as <Nama>":
          !roll as Alice 1d20 +str +dex +2 dc 15
        Buff/Debuff yang cocok (+2 STR, -1 DEX, dll) ikut dihitung otomatis.
        """
        if not query:
            return await ctx.send("Format: `!roll 2d20 +2` atau `!roll as Alice 1d20 +str +dex dc 16`")

        # deteksi "as <Nama>"
        actor = None
        m_as = re.match(r"as\s+(\w+)\s+(.*)", query, flags=re.IGNORECASE)
        if m_as:
            actor = m_as.group(1)
            query = m_as.group(2)

        # cari DC target (vs atau dc)
        target = None
        q = query
        m_vs = re.search(r"\b(vs|dc)\b\s*(\d+)", q, flags=re.IGNORECASE)
        if m_vs:
            target = int(m_vs.group(2))
            q = q[:m_vs.start()].strip()

        dice_terms, mods, stat_refs, cleaned, named = _parse_expression(q)
        if not dice_terms and not mods and not stat_refs:
            return await ctx.send("⚠️ Tidak ada pola dadu/modifier valid.")

        details = _roll_dice(dice_terms)
        dice_sum = sum(d["sum"] for d in details)

        # ambil data karakter dari CharacterStatus
        stat_mods = []
        buff_mods = []
        if actor:
            status_cog = self.bot.get_cog("CharacterStatus")
            if status_cog:
                state = status_cog._ensure(ctx)
                if actor in state:
                    core = state[actor]["core"]
                    buffs = state[actor].get("buffs", [])
                    debuffs = state[actor].get("debuffs", [])
                    for stat, sign in stat_refs:
                        base_val = _ability_mod(core.get(stat, 10)) * sign
                        stat_mods.append((stat, base_val))
                        # cek buff/debuff yang match
                        for b in buffs + debuffs:
                            m = BUFF_DEBUFF_RE.match(b.strip())
                            if m and m.group("stat").lower() == stat:
                                sign2 = -1 if m.group("sign") == "-" else 1
                                val = int(m.group("val")) * sign2 * sign
                                buff_mods.append((stat, val, b))
                else:
                    await ctx.send(f"⚠️ Karakter **{actor}** tidak ditemukan di status.")
            else:
                await ctx.send("⚠️ Modul CharacterStatus tidak aktif.")

        mod_total = sum(mods) + sum(v for _, v in stat_mods) + sum(v for _, v, _ in buff_mods)
        total = dice_sum + mod_total

        crit, fail = _crit_info(details)

        # judul embed
        title = f"🎲 Hasil: {total}"
        color = discord.Color.blurple()
        if target is not None:
            if total >= target:
                title += f" • **Success (≥ {target})**"
                color = discord.Color.green()
            else:
                title += f" • **Fail (< {target})**"
                color = discord.Color.red()

        if crit:
            title += " • **CRIT!**"
            color = discord.Color.green()
        elif fail:
            title += " • **FAIL!**"
            color = discord.Color.red()

        embed = discord.Embed(title=title, color=color)

        # dice breakdown
        if details:
            lines = []
            for d in details:
                lines.append(f"{d['count']}d{d['sides']}: {d['rolls']} = **{d['sum']}**")
            embed.add_field(name="Dice", value="\n".join(lines), inline=False)

        # modifiers breakdown
        embed.add_field(name="Modifiers", value=_fmt_mods(mods, stat_mods, buff_mods, named), inline=False)

        # total vs DC
        if target is not None:
            embed.add_field(name="DC Check", value=f"{total} vs {target}", inline=False)

        if actor:
            embed.set_footer(text=f"Roll oleh {actor}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DiceCog(bot))
