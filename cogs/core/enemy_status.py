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
    elif pct >= 100: return "💪 Sehat"
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

def make_embed(enemies: list, ctx, title="👹 Enemy Status", mode="player"):
    embed = discord.Embed(title=title, description="📜 Status Musuh", color=discord.Color.red())
    if not enemies:
        embed.add_field(name="(kosong)", value="Gunakan `!enemy add`.", inline=False)
        return embed

    for e in enemies:
        effects = json.loads(e.get("effects") or "[]")
        buffs = [eff for eff in effects if "buff" in eff.get("type", "").lower()]
        debuffs = [eff for eff in effects if "debuff" in eff.get("type", "").lower()]
        buffs_str = "\n".join([f"✅ {_format_effect(b)}" for b in buffs]) or "-"
        debuffs_str = "\n".join([f"❌ {_format_effect(d)}" for d in debuffs]) or "-"

        loot_list = json.loads(e.get("loot") or "[]")
        loot_line = "\n".join([f"- {it['name']} ({it.get('rarity','')})" for it in loot_list]) or "-"

        if mode == "gm":
            hp_line = f"❤️ HP: {e['hp']}/{e['hp_max']} [{_bar(e['hp'], e['hp_max'])}]"
            en_line = f"🔋 Energy: {e['energy']}/{e['energy_max']} [{_bar(e['energy'], e['energy_max'])}]"
            st_line = f"⚡ Stamina: {e['stamina']}/{e['stamina_max']} [{_bar(e['stamina'], e['stamina_max'])}]"
        else:
            hp_line = f"❤️ Kondisi: {_hp_status(e['hp'], e['hp_max'])}"
            en_line = f"🔋 Energi: {_energy_status(e['energy'], e['energy_max'])}"
            st_line = f"⚡ Stamina: {_stamina_status(e['stamina'], e['stamina_max'])}"

        reward_line = f"XP {e.get('xp_reward',0)} | Gold {e.get('gold_reward',0)}"

        value = (
            f"{hp_line}\n{en_line}\n{st_line}\n\n"
            f"✨ Buffs:\n{buffs_str}\n\n"
            f"☠️ Debuffs:\n{debuffs_str}\n\n"
            f"🎁 Reward: {reward_line}\n\n"
            f"🎒 Loot:\n{loot_line}"
        )
        embed.add_field(name=e["name"], value=value, inline=False)
    return embed

# ===== Cog =====

class EnemyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy(self, ctx):
        await ctx.send(
            "Gunakan: `!enemy add`, `!enemy show`, `!enemy gmshow`, "
            "`!enemy dmg`, `!enemy heal`, "
            "`!enemy buff`, `!enemy debuff`, `!enemy clearbuff`, `!enemy cleardebuff`, "
            "`!enemy remove`, `!enemy stam-`, `!enemy stam+`, `!enemy ene-`, `!enemy ene+`"
        )

    # === Tambah / Update Enemy ===
    @enemy.command(name="add")
    async def enemy_add(self, ctx, name: str, hp: int, energy: int = 50, stamina: int = 50, *, opts: str = None):
        guild_id = ctx.guild.id
        xp_reward, gold_reward, loots = 0, 0, []
        if opts:
            if "--xp" in opts:
                try: xp_reward = int(opts.split("--xp")[1].split()[0])
                except: pass
            if "--gold" in opts:
                try: gold_reward = int(opts.split("--gold")[1].split()[0])
                except: pass
            if "--loot" in opts:
                try:
                    loot_str = opts.split("--loot")[1].strip()
                    parts = loot_str.split(";")
                    for p in parts:
                        segs = [s.strip() for s in p.split("|")]
                        if not segs: continue
                        item = {"name": segs[0]}
                        if len(segs) > 1: item["type"] = segs[1]
                        if len(segs) > 2: item["effect"] = segs[2]
                        if len(segs) > 3: item["rarity"] = segs[3]
                        loots.append(item)
                except Exception as e:
                    await ctx.send(f"⚠️ Loot parsing gagal: {e}")

        exists = fetchone(guild_id, "SELECT id FROM enemies WHERE name=?", (name,))
        if exists:
            execute(guild_id, """
                UPDATE enemies
                SET hp=?, hp_max=?, energy=?, energy_max=?, stamina=?, stamina_max=?,
                    xp_reward=?, gold_reward=?, loot=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (hp, hp, energy, energy, stamina, stamina, xp_reward, gold_reward, json.dumps(loots), exists["id"]))
            await ctx.send(f"♻️ Enemy **{name}** diperbarui.")
        else:
            execute(guild_id, """
                INSERT INTO enemies (name, hp, hp_max, energy, energy_max, stamina, stamina_max,
                                     xp_reward, gold_reward, loot)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (name, hp, hp, energy, energy, stamina, stamina, xp_reward, gold_reward, json.dumps(loots)))
            await ctx.send(f"👹 Enemy **{name}** ditambahkan.")

    # === Show ===
    @enemy.command(name="show")
    async def enemy_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        rows = [fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))] if name else fetchall(guild_id, "SELECT * FROM enemies")
        if not rows:
            return await ctx.send(f"❌ Enemy tidak ditemukan.")
        title = f"👹 Enemy Status: {name}" if name else "👹 Enemy Status (All)"
        embed = make_embed(rows, ctx, title=title, mode="player")
        await ctx.send(embed=embed)

    @enemy.command(name="gmshow")
    async def enemy_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        rows = [fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))] if name else fetchall(guild_id, "SELECT * FROM enemies")
        if not rows:
            return await ctx.send(f"❌ Enemy tidak ditemukan.")
        title = f"🎭 GM Enemy Status: {name}" if name else "🎭 GM Enemy Status (All)"
        embed = make_embed(rows, ctx, title=title, mode="gm")
        await ctx.send(embed=embed)

    # === Combat Ops ===
    @enemy.command(name="dmg")
    async def enemy_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        await ctx.send(f"💥 {name} menerima {amount} damage → HP sekarang {new_hp}")

    @enemy.command(name="heal")
    async def enemy_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        await ctx.send(f"✨ {name} dipulihkan {amount} HP → {new_hp}")

    # === Buff / Debuff ===
    @enemy.command(name="buff")
    async def enemy_buff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "enemy", name, effect_name, duration, is_buff=True)
        await ctx.send(msg)

    @enemy.command(name="debuff")
    async def enemy_debuff(self, ctx, name: str, effect_name: str, duration: int = None):
        msg = await status_service.add_effect(ctx.guild.id, "enemy", name, effect_name, duration, is_buff=False)
        await ctx.send(msg)

    # === Resource Ops ===
    @enemy.command(name="stam-")
    async def enemy_stam_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount)
        await ctx.send(f"⚡ {name} kehilangan stamina {amount}")

    @enemy.command(name="stam+")
    async def enemy_stam_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan stamina {amount}")

    @enemy.command(name="ene-")
    async def enemy_ene_use(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount)
        await ctx.send(f"🔋 {name} kehilangan energi {amount}")

    @enemy.command(name="ene+")
    async def enemy_ene_regen(self, ctx, name: str, amount: int):
        await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan energi {amount}")

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
