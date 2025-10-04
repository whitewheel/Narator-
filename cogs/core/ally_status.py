import math
import json
import discord
from discord.ext import commands
from utils.db import fetchall, fetchone, execute
from services import status_service, effect_service

# ===== Utility =====

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
    dur_txt = "∞" if d == -1 else f"{d}"
    stack = e.get("stack", 1)
    form = e.get("formula", "")
    txt = e.get("text", "")
    if stack > 1:
        txt += f" Lv{stack}"
    if form:
        txt += f" ({form})"
    return f"{txt} [Dur: {dur_txt}]"

def _hp_status(cur: int, mx: int) -> str:
    if mx <= 0: return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if cur <= 0: return "💀 Tewas"
    elif pct >= 100: return "💪 Segar"
    elif pct >= 75: return "🙂 Luka Ringan"
    elif pct >= 50: return "⚔️ Luka Sedang"
    elif pct >= 25: return "🤕 Luka Berat"
    else: return "☠️ Sekarat"

def _energy_status(cur: int, mx: int) -> str:
    if mx <= 0: return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if pct >= 75: return "⚡ Penuh tenaga"
    elif pct >= 50: return "😐 Cukup bertenaga"
    elif pct >= 25: return "😓 Hampir habis tenaga"
    else: return "🥵 Kehabisan tenaga"

def _stamina_status(cur: int, mx: int) -> str:
    if mx <= 0: return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if pct >= 75: return "🏃 Masih segar"
    elif pct >= 50: return "😤 Terengah-engah"
    elif pct >= 25: return "😩 Hampir kelelahan"
    else: return "🥴 Ambruk kelelahan"

# ===== Embed Builder =====

def make_embed(allies: list, title="🤝 Ally Status", mode="player"):
    embed = discord.Embed(
        title=title,
        description="📜 Status Ally",
        color=discord.Color.green()
    )
    if not allies:
        embed.add_field(name="(kosong)", value="Gunakan `!ally add`.", inline=False)
        return embed

    for a in allies:
        effects = json.loads(a.get("effects") or "[]")
        buffs = [eff for eff in effects if "buff" in eff.get("type", "").lower()]
        debuffs = [eff for eff in effects if "debuff" in eff.get("type", "").lower()]
        buffs_str = "\n".join([f"✅ {_format_effect(b)}" for b in buffs]) or "-"
        debuffs_str = "\n".join([f"❌ {_format_effect(d)}" for d in debuffs]) or "-"

        if mode == "gm":
            value = (
                f"❤️ HP: {a['hp']}/{a['hp_max']} [{_bar(a['hp'], a['hp_max'])}]\n"
                f"🔋 Energy: {a['energy']}/{a['energy_max']} [{_bar(a['energy'], a['energy_max'])}]\n"
                f"⚡ Stamina: {a['stamina']}/{a['stamina_max']} [{_bar(a['stamina'], a['stamina_max'])}]\n"
                f"🛡️ AC {a['ac']}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n"
                f"☠️ Debuffs:\n{debuffs_str}"
            )
        else:
            value = (
                f"❤️ Kondisi: {_hp_status(a['hp'], a['hp_max'])}\n"
                f"🔋 Energi: {_energy_status(a['energy'], a['energy_max'])}\n"
                f"⚡ Stamina: {_stamina_status(a['stamina'], a['stamina_max'])}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n"
                f"☠️ Debuffs:\n{debuffs_str}"
            )
        embed.add_field(name=a["name"], value=value, inline=False)
    return embed

# ===== Cog =====

class AllyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ensure table ---
    def _ensure_table(self, guild_id: int):
        execute(
            guild_id,
            """
            CREATE TABLE IF NOT EXISTS allies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                hp INTEGER DEFAULT 0,
                hp_max INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 0,
                energy_max INTEGER DEFAULT 0,
                stamina INTEGER DEFAULT 0,
                stamina_max INTEGER DEFAULT 0,
                ac INTEGER DEFAULT 10,
                effects TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    @commands.group(name="ally", invoke_without_command=True)
    async def ally(self, ctx):
        await ctx.send(
            "Gunakan: `!ally add`, `!ally show`, `!ally gmshow`, "
            "`!ally dmg`, `!ally heal`, `!ally stam-`, `!ally stam+`, "
            "`!ally ene-`, `!ally ene+`, `!ally buff`, `!ally debuff`, "
            "`!ally remove`, `!ally clear`"
        )

    # === Add Ally ===
    @ally.command(name="add")
    async def ally_add(self, ctx, name: str, hp: int, energy: int, stamina: int):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        exists = fetchone(guild_id, "SELECT id FROM allies WHERE name=?", (name,))
        if exists:
            execute(guild_id, """
                UPDATE allies
                SET hp=?, hp_max=?, energy=?, energy_max=?, stamina=?, stamina_max=?, ac=10, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (hp, hp, energy, energy, stamina, stamina, exists["id"]))
            await ctx.send(f"♻️ Ally **{name}** diperbarui.")
        else:
            execute(guild_id, """
                INSERT INTO allies (name, hp, hp_max, energy, energy_max, stamina, stamina_max, ac)
                VALUES (?,?,?,?,?,?,?,10)
            """, (name, hp, hp, energy, energy, stamina, stamina))
            await ctx.send(f"🤝 Ally **{name}** ditambahkan.")

    # === Show Ally ===
    @ally.command(name="show")
    async def ally_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        if name:
            row = fetchone(guild_id, "SELECT * FROM allies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Ally **{name}** tidak ditemukan.")
            rows = [row]
            title = f"🤝 Ally Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM allies")
            title = "🤝 Ally Status (All)"
        embed = make_embed(rows, title=title, mode="player")
        await ctx.send(embed=embed)

    @ally.command(name="gmshow")
    async def ally_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)

        if name:
            row = fetchone(guild_id, "SELECT * FROM allies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Ally **{name}** tidak ditemukan.")
            rows = [row]
            title = f"🎭 GM Ally Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM allies")
            title = "🎭 GM Ally Status (All)"
        embed = make_embed(rows, title=title, mode="gm")
        await ctx.send(embed=embed)

    # === Combat Ops ===
    @ally.command(name="dmg")
    async def ally_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "ally", name, amount)
        await ctx.send(f"💥 {name} menerima {amount} damage → HP sekarang {new_hp}")

    @ally.command(name="heal")
    async def ally_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "ally", name, amount)
        await ctx.send(f"✨ {name} dipulihkan {amount} HP → {new_hp}")

    # === Resource Ops (Stamina & Energy) ===
    @ally.command(name="stam-")
    async def ally_stam_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "stamina", amount)
        await ctx.send(f"⚡ {name} kehilangan stamina {amount}")

    @ally.command(name="stam+")
    async def ally_stam_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "stamina", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan stamina {amount}")

    @ally.command(name="ene-")
    async def ally_ene_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "energy", amount)
        await ctx.send(f"🔋 {name} kehilangan energi {amount}")

    @ally.command(name="ene+")
    async def ally_ene_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "energy", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan energi {amount}")

    # === Buff / Debuff (integrasi effect_service) ===
    @ally.command(name="buff")
    async def ally_buff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "ally", name, effect_name, duration, is_buff=True)
        await ctx.send(msg)

    @ally.command(name="debuff")
    async def ally_debuff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "ally", name, effect_name, duration, is_buff=False)
        await ctx.send(msg)

    @ally.command(name="clearbuff")
    async def ally_clearbuff(self, ctx, name: str):
        msg = await status_service.clear_effects(ctx.guild.id, "ally", name, is_buff=True)
        await ctx.send(msg)

    @ally.command(name="cleardebuff")
    async def ally_cleardebuff(self, ctx, name: str):
        msg = await status_service.clear_effects(ctx.guild.id, "ally", name, is_buff=False)
        await ctx.send(msg)

    # === Remove / Clear ===
    @ally.command(name="remove")
    async def ally_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)
        row = fetchone(guild_id, "SELECT id FROM allies WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Ally **{name}** tidak ditemukan.")
        execute(guild_id, "DELETE FROM allies WHERE name=?", (name,))
        await ctx.send(f"🗑️ Ally **{name}** dihapus.")

    @ally.command(name="clear")
    async def ally_clear(self, ctx):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)
        execute(guild_id, "DELETE FROM allies")
        await ctx.send("🧹 Semua ally dihapus.")

async def setup(bot):
    await bot.add_cog(AllyStatus(bot))
