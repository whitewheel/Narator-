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


def _format_effect_detailed(e):
    """Format efek dengan durasi, formula, dan deskripsi singkat."""
    d = e.get("duration", -1)
    dur_txt = "∞" if d == -1 else f"{d}"
    form = e.get("formula", "")
    desc = e.get("description", "(tidak ada deskripsi)")
    name = e.get("text", "???")
    return f"{name} [Dur: {dur_txt}] — {form}\n🛈 {desc}"


# ===== Status Logic =====
def _hp_status(cur: int, mx: int) -> str:
    if cur <= 0: return "💀 Tewas / tidak sadarkan diri"
    if mx <= 0: return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if pct >= 90: return "💪 Kondisi prima"
    elif pct >= 75: return "🙂 Luka ringan"
    elif pct >= 50: return "⚔️ Luka sedang"
    elif pct >= 25: return "🤕 Luka berat"
    else: return "☠️ Sekarat"


def _energy_status(cur: int, mx: int) -> str:
    if mx <= 0: return "❓ Tidak diketahui"
    if cur <= 0: return "🔋 Kehabisan energi alat"
    pct = (cur / mx) * 100
    if pct >= 75: return "⚡ Semua sistem berjalan normal"
    elif pct >= 50: return "🔧 Daya alat mulai menurun"
    elif pct >= 25: return "⚙️ Alat melemah / tidak stabil"
    else: return "💤 Energi hampir habis"


def _stamina_status(cur: int, mx: int) -> str:
    if mx <= 0: return "❓ Tidak diketahui"
    if cur <= 0: return "🥴 Kelelahan total / tak bisa bergerak"
    pct = (cur / mx) * 100
    if pct >= 75: return "🏃 Masih bugar"
    elif pct >= 50: return "😤 Mulai kelelahan"
    elif pct >= 25: return "😩 Hampir tak sanggup"
    else: return "🥵 Terjatuh karena kehabisan tenaga"


# ===== Embed Builder =====
def make_embed(allies: list, title="🤝 Ally Status", mode="player"):
    embed = discord.Embed(
        title=title,
        description="📜 Status Sekutu",
        color=discord.Color.green()
    )

    if not allies:
        embed.add_field(name="(kosong)", value="Gunakan `!ally add`.", inline=False)
        return embed

    for a in allies:
        effects = json.loads(a.get("effects") or "[]")

        buffs = [eff for eff in effects if eff.get("type", "").lower() == "buff"]
        debuffs = [eff for eff in effects if eff.get("type", "").lower() == "debuff"]

        unique_buffs = {eff.get("id", eff.get("text", "")): eff for eff in buffs}.values()
        unique_debuffs = {eff.get("id", eff.get("text", "")): eff for eff in debuffs}.values()

        buffs_str = "\n\n".join([f"✅ {_format_effect_detailed(b)}" for b in unique_buffs]) or "-"
        debuffs_str = "\n\n".join([f"❌ {_format_effect_detailed(d)}" for d in unique_debuffs]) or "-"

        # GM Mode → detail angka
        if mode == "gm":
            value = (
                f"❤️ HP: {a['hp']}/{a['hp_max']} [{_bar(a['hp'], a['hp_max'])}]\n"
                f"🔋 Energi: {a['energy']}/{a['energy_max']} [{_bar(a['energy'], a['energy_max'])}]\n"
                f"⚡ Stamina: {a['stamina']}/{a['stamina_max']} [{_bar(a['stamina'], a['stamina_max'])}]\n"
                f"🛡️ AC: {a['ac']}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n☠️ Debuffs:\n{debuffs_str}"
            )
        else:
            hp_state = _hp_status(a['hp'], a['hp_max'])
            ene_state = _energy_status(a['energy'], a['energy_max'])
            stm_state = _stamina_status(a['stamina'], a['stamina_max'])

            value = (
                f"❤️ Kondisi: {hp_state}\n"
                f"🔋 Energi: {ene_state}\n"
                f"⚡ Stamina: {stm_state}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n☠️ Debuffs:\n{debuffs_str}"
            )

        embed.add_field(name=a["name"], value=value, inline=False)

    return embed


# ===== Cog =====
class AllyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            "`!ally dmg`, `!ally heal`, "
            "`!ally stam-`, `!ally stam+`, `!ally ene-`, `!ally ene+`, "
            "`!ally buff`, `!ally debuff`, `!ally remove`, `!ally clear`"
        )

    # === Add / Update ===
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

    # === Show (Player) ===
    @ally.command(name="show")
    async def ally_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)
        if name:
            row = fetchone(guild_id, "SELECT * FROM allies WHERE name=?", (name,))
            if not row:
                return await ctx.send("❌ Ally tidak ditemukan.")
            rows = [row]
            title = f"🤝 Ally Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM allies")
            title = "🤝 Ally Status (All)"
        embed = make_embed(rows, title=title, mode="player")
        await ctx.send(embed=embed)

    # === GM Show ===
    @ally.command(name="gmshow")
    async def ally_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)
        if name:
            row = fetchone(guild_id, "SELECT * FROM allies WHERE name=?", (name,))
            if not row:
                return await ctx.send("❌ Ally tidak ditemukan.")
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
        if new_hp <= 0:
            await ctx.send(f"💀 Sekutu **{name}** tumbang.")
        else:
            await ctx.send(f"💥 {name} terluka parah.")

    @ally.command(name="heal")
    async def ally_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "ally", name, amount)
        await ctx.send(f"✨ {name} memulihkan sebagian darahnya.")

    # === Resource Ops ===
    @ally.command(name="stam-")
    async def ally_stam_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "stamina", amount)
        await ctx.send(f"😤 {name} kehilangan stamina.")

    @ally.command(name="stam+")
    async def ally_stam_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "stamina", amount, regen=True)
        await ctx.send(f"🏃 {name} memulihkan tenaga.")

    @ally.command(name="ene-")
    async def ally_ene_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "energy", amount)
        await ctx.send(f"⚙️ {name} kehilangan daya alatnya.")

    @ally.command(name="ene+")
    async def ally_ene_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "ally", name, "energy", amount, regen=True)
        await ctx.send(f"🔋 {name} alatnya kembali berfungsi sebagian.")

    # === Buff / Debuff ===
    @ally.command(name="buff")
    async def ally_buff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "ally", name, effect_name, duration, is_buff=True)
        await ctx.send(msg)

    @ally.command(name="debuff")
    async def ally_debuff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "ally", name, effect_name, duration, is_buff=False)
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

    # === Alias Cepat ===
    @commands.command(name="admg")
    async def ally_dmg_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally dmg"), name=name, amount=amount)

    @commands.command(name="aheal")
    async def ally_heal_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally heal"), name=name, amount=amount)

    @commands.command(name="ausestm")
    async def ally_usestm_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally stam-"), name=name, amount=amount)

    @commands.command(name="aaddstm")
    async def ally_addstm_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally stam+"), name=name, amount=amount)

    @commands.command(name="auseene")
    async def ally_useene_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally ene-"), name=name, amount=amount)

    @commands.command(name="aaddene")
    async def ally_addene_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("ally ene+"), name=name, amount=amount)


async def setup(bot):
    await bot.add_cog(AllyStatus(bot))
