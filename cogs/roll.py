import re
import random
import discord
from discord.ext import commands

# Regex dasar
DICE_RE = re.compile(r"(?P<count>\d*)d(?P<sides>\d+)", re.IGNORECASE)
MOD_NUM_RE = re.compile(r"(?P<sign>[+-])\s*(?P<val>\d+)")
MOD_NAMED_RE = re.compile(r"(?P<sign>[+-])\s*(?P<name>[A-Za-z_][\w\-]*)\s*[:=]\s*(?P<val>\d+)")

# Batas aman
MAX_DICE = 100
MAX_SIDES = 1000

def _parse_expression(expr: str):
    """
    Parse ekspresi roll:
      - multi dice: 2d20, 3d6, dst
      - multi modifier: +2 +2 -1
      - modifier bernama: +str=2, +int:2
    return (dice_terms, mods, named_mods, cleaned_expr)
    """
    expr = re.sub(r"[dD]{2,}", "d", expr)  # toleransi dd20 → d20
    cleaned = expr

    dice_terms = []
    for m in DICE_RE.finditer(expr):
        count = int(m.group("count")) if m.group("count") else 1
        sides = int(m.group("sides"))
        dice_terms.append((count, sides))

    # modifier bernama
    named_mods = []
    for m in MOD_NAMED_RE.finditer(expr):
        sign = -1 if m.group("sign") == "-" else 1
        name = m.group("name")
        val = int(m.group("val")) * sign
        named_mods.append((name, val))

    # modifier angka polos (hindari overlap dengan dice/named)
    temp = DICE_RE.sub(" ", expr)
    temp = MOD_NAMED_RE.sub(" ", temp)
    mods = []
    for m in MOD_NUM_RE.finditer(temp):
        sign = -1 if m.group("sign") == "-" else 1
        val = int(m.group("val")) * sign
        mods.append(val)

    return dice_terms, mods, named_mods, cleaned

def _roll_dice(dice_terms):
    """Roll setiap (count, sides)."""
    out = []
    for count, sides in dice_terms:
        c = max(0, min(count, MAX_DICE))
        s = max(1, min(sides, MAX_SIDES))
        rolls = [random.randint(1, s) for _ in range(c)]
        out.append({"count": c, "sides": s, "rolls": rolls, "sum": sum(rolls)})
    return out

def _crit_info(dice_details):
    """Deteksi CRIT / FAIL kalau ada d20."""
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

def _sum_modifiers(mods, named_mods):
    return sum(mods) + sum(v for _, v in named_mods)

def _fmt_mods(mods, named_mods):
    parts = []
    if mods:
        parts.append(" ".join([f"{'+' if v>=0 else ''}{v}" for v in mods]))
    for name, v in named_mods:
        parts.append(f"{'+' if v>=0 else ''}{abs(v)} ({name})")
    return " + ".join(parts) if parts else "0"

class DiceCog(commands.Cog):
    """Dice roller dengan multi-modifier, DC check, dan breakdown"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, query: str):
        """
        !roll <expresi> [vs <target>] / [dc <target>]
        Contoh:
          !roll 2d20 +2 +2
          !roll 1d20 +str=2 +int:1 vs 16
          !roll 1d20 +str=2 +prof=3 dc 18
          !roll 1d8+1d6 +3
        """
        if not query:
            return await ctx.send("Format: `!roll 2d20 +2 +2` atau `!roll 1d20 +str=2 +int:2 dc 16`")

        # cari DC target (vs atau dc)
        target = None
        q = query
        m_vs = re.search(r"\b(vs|dc)\b\s*(\d+)", q, flags=re.IGNORECASE)
        if m_vs:
            target = int(m_vs.group(2))
            q = q[:m_vs.start()].strip()

        dice_terms, mods, named_mods, cleaned = _parse_expression(q)
        if not dice_terms and not mods and not named_mods:
            return await ctx.send("⚠️ Tidak ada pola dadu/modifier valid. Contoh: `!roll 2d6 +2`")

        details = _roll_dice(dice_terms)
        dice_sum = sum(d["sum"] for d in details)
        mod_total = _sum_modifiers(mods, named_mods)
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
        embed.add_field(name="Modifiers", value=_fmt_mods(mods, named_mods), inline=False)

        # total vs DC
        if target is not None:
            embed.add_field(name="DC Check", value=f"{total} vs {target}", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DiceCog(bot))
