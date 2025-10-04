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
def make_embed(enemies: list, title="👹 Enemy Status", mode="player"):
    embed = discord.Embed(title=title, description="📜 Status Musuh", color=discord.Color.red())

    if not enemies:
        embed.add_field(name="(kosong)", value="Gunakan `!enemy add`.", inline=False)
        return embed

    for e in enemies:
        effects = json.loads(e.get("effects") or "[]")

        buffs = [eff for eff in effects if eff.get("type", "").lower() == "buff"]
        debuffs = [eff for eff in effects if eff.get("type", "").lower() == "debuff"]

        unique_buffs = {eff.get("id", eff.get("text", "")): eff for eff in buffs}.values()
        unique_debuffs = {eff.get("id", eff.get("text", "")): eff for eff in debuffs}.values()

        buffs_str = "\n\n".join([f"✅ {_format_effect_detailed(b)}" for b in unique_buffs]) or "-"
        debuffs_str = "\n\n".join([f"❌ {_format_effect_detailed(d)}" for d in unique_debuffs]) or "-"

        # GM Mode → detail angka
        if mode == "gm":
            value = (
                f"❤️ HP: {e['hp']}/{e['hp_max']} [{_bar(e['hp'], e['hp_max'])}]\n"
                f"🔋 Energi: {e['energy']}/{e['energy_max']} [{_bar(e['energy'], e['energy_max'])}]\n"
                f"⚡ Stamina: {e['stamina']}/{e['stamina_max']} [{_bar(e['stamina'], e['stamina_max'])}]\n"
                f"🛡️ AC: {e['ac']}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n☠️ Debuffs:\n{debuffs_str}"
            )
        else:
            # Player Mode → hanya kondisi naratif
            hp_state = _hp_status(e['hp'], e['hp_max'])
            ene_state = _energy_status(e['energy'], e['energy_max'])
            stm_state = _stamina_status(e['stamina'], e['stamina_max'])

            value = (
                f"❤️ Kondisi: {hp_state}\n"
                f"🔋 Energi: {ene_state}\n"
                f"⚡ Stamina: {stm_state}\n\n"
                f"✨ Buffs:\n{buffs_str}\n\n☠️ Debuffs:\n{debuffs_str}"
            )

        embed.add_field(name=e["name"], value=value, inline=False)
    return embed


# ===== Cog =====
class EnemyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _ensure_table(self, guild_id: int):
        execute(
            guild_id,
            """
            CREATE TABLE IF NOT EXISTS enemies (
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

    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy(self, ctx):
        await ctx.send(
            "Gunakan: `!enemy add`, `!enemy show`, `!enemy gmshow`, "
            "`!enemy dmg`, `!enemy heal`, "
            "`!enemy stam-`, `!enemy stam+`, `!enemy ene-`, `!enemy ene+`, "
            "`!enemy buff`, `!enemy debuff`, `!enemy remove`, `!enemy clear`"
        )

    # === Add / Update ===
    @enemy.command(name="add")
    async def enemy_add(self, ctx, name: str, hp: int, energy: int, stamina: int):
        guild_id = ctx.guild.id
        self._ensure_table(guild_id)
        exists = fetchone(guild_id, "SELECT id FROM enemies WHERE name=?", (name,))
        if exists:
            execute(guild_id, """
                UPDATE enemies
                SET hp=?, hp_max=?, energy=?, energy_max=?, stamina=?, stamina_max=?, ac=10, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (hp, hp, energy, energy, stamina, stamina, exists["id"]))
            await ctx.send(f"♻️ Enemy **{name}** diperbarui.")
        else:
            execute(guild_id, """
                INSERT INTO enemies (name, hp, hp_max, energy, energy_max, stamina, stamina_max, ac)
                VALUES (?,?,?,?,?,?,?,10)
            """, (name, hp, hp, energy, energy, stamina, stamina))
            await ctx.send(f"👹 Enemy **{name}** ditambahkan.")

    # === Show (Player) ===
    @enemy.command(name="show")
    async def enemy_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        rows = [fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))] if name else fetchall(guild_id, "SELECT * FROM enemies")
        if not rows:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        title = f"👹 Enemy Status: {name}" if name else "👹 Enemy Status (All)"
        embed = make_embed(rows, title=title, mode="player")
        await ctx.send(embed=embed)

    # === GM Show ===
    @enemy.command(name="gmshow")
    async def enemy_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        rows = [fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))] if name else fetchall(guild_id, "SELECT * FROM enemies")
        if not rows:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        title = f"🎭 GM Enemy Status: {name}" if name else "🎭 GM Enemy Status (All)"
        embed = make_embed(rows, title=title, mode="gm")
        await ctx.send(embed=embed)

    # === Combat Ops ===
    @enemy.command(name="dmg")
    async def enemy_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        if new_hp <= 0:
            await ctx.send(f"💀 **{name}** tewas.")
        else:
            await ctx.send(f"💥 {name} terluka cukup parah.")

    @enemy.command(name="heal")
    async def enemy_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        await ctx.send(f"✨ {name} memulihkan sebagian darahnya.")

    # === Resource Ops ===
    @enemy.command(name="stam-")
    async def enemy_stam_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount)
        await ctx.send(f"😤 {name} kehilangan stamina.")

    @enemy.command(name="stam+")
    async def enemy_stam_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount, regen=True)
        await ctx.send(f"🏃 {name} memulihkan tenaganya.")

    @enemy.command(name="ene-")
    async def enemy_ene_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount)
        await ctx.send(f"⚙️ {name} kehilangan daya alatnya.")

    @enemy.command(name="ene+")
    async def enemy_ene_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount, regen=True)
        await ctx.send(f"🔋 {name} alatnya kembali berfungsi sebagian.")

    # === Buff / Debuff ===
    @enemy.command(name="buff")
    async def enemy_buff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "enemy", name, effect_name, duration, is_buff=True)
        await ctx.send(msg)

    @enemy.command(name="debuff")
    async def enemy_debuff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "enemy", name, effect_name, duration, is_buff=False)
        await ctx.send(msg)

    # === Remove / Clear ===
    @enemy.command(name="remove")
    async def enemy_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT id FROM enemies WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
        execute(guild_id, "DELETE FROM enemies WHERE name=?", (name,))
        await ctx.send(f"🗑️ Enemy **{name}** dihapus.")

    @enemy.command(name="clear")
    async def enemy_clear(self, ctx):
        guild_id = ctx.guild.id
        execute(guild_id, "DELETE FROM enemies")
        await ctx.send("🧹 Semua enemy dihapus.")

    # === Alias Cepat ===
    @commands.command(name="edmg")
    async def enemy_dmg_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy dmg"), name=name, amount=amount)

    @commands.command(name="eheal")
    async def enemy_heal_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy heal"), name=name, amount=amount)

    @commands.command(name="eusestm")
    async def enemy_usestm_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy stam-"), name=name, amount=amount)

    @commands.command(name="eaddstm")
    async def enemy_addstm_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy stam+"), name=name, amount=amount)

    @commands.command(name="euseene")
    async def enemy_useene_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy ene-"), name=name, amount=amount)

    @commands.command(name="eaddene")
    async def enemy_addene_alias(self, ctx, name: str, amount: int):
        await ctx.invoke(self.bot.get_command("enemy ene+"), name=name, amount=amount)


async def setup(bot):
    await bot.add_cog(EnemyStatus(bot))
