import math
import json
import discord
from discord.ext import commands
from utils.db import fetchall, fetchone, execute
from services import status_service

# ===== Utility =====

def _bar(cur: int, mx: int, width: int = 12) -> str:
    if mx <= 0:
        return "░" * width
    cur = max(0, min(cur, mx))
    filled = int(round(width * (cur / mx)))
    return "█" * filled + "░" * (width - filled)

def _mod(score: int) -> int:
    return math.floor(score / 5)

def _apply_effects(base_stats, effects):
    stats = base_stats.copy()
    notes = []
    for eff in effects:
        text = eff.get("text", "")
        for key in ["str","dex","con","int","wis","cha","ac"]:
            if key.upper() in text.upper():
                try:
                    val = int(text.replace(key.upper(), "").strip())
                except:
                    val = 0
                stats[key] = stats.get(key, 0) + val
                notes.append(f"{'+' if val>=0 else ''}{val} {key.upper()}")
    return stats, notes

def _format_effect(e):
    d = e.get("duration", -1)
    return f"{e['text']} [Durasi: {d if d >= 0 else 'Permanent'}]"

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
    embed = discord.Embed(
        title=title,
        description="📜 Status Musuh",
        color=discord.Color.red()
    )
    if not enemies:
        embed.add_field(name="(kosong)", value="Gunakan `!enemy add`.", inline=False)
        return embed

    for e in enemies:
        effects = json.loads(e["effects"] or "[]")
        buffs = [eff for eff in effects if "buff" in eff.get("type","").lower()]
        debuffs = [eff for eff in effects if "debuff" in eff.get("type","").lower()]
        buffs_str = "\n".join([f"✅ {_format_effect(b)}" for b in buffs]) or "-"
        debuffs_str = "\n".join([f"❌ {_format_effect(d)}" for d in debuffs]) or "-"

        loot_list = json.loads(e["loot"] or "[]")
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
            "`!enemy remove`, `!enemy reveal`, `!enemy loot`, "
            "`!enemy clearbuff`, `!enemy cleardebuff`, `!enemy reward`, "
            "`!enemy stam-`, `!enemy stam+`, `!enemy ene-`, `!enemy ene+`"
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

    # === Remove Enemy ===
    @enemy.command(name="remove")
    async def enemy_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT id FROM enemies WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
        execute(guild_id, "DELETE FROM enemies WHERE name=?", (name,))
        await ctx.send(f"🗑️ Enemy **{name}** berhasil dihapus.")

    # === Reveal / Rename Enemy ===
    @enemy.command(name="reveal")
    async def enemy_reveal(self, ctx, old_name: str, new_name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT id FROM enemies WHERE name=?", (old_name,))
        if not row:
            return await ctx.send(f"❌ Enemy **{old_name}** tidak ditemukan.")
        execute(guild_id, "UPDATE enemies SET name=? WHERE id=?", (new_name, row["id"]))
        await ctx.send(f"🕵️ Enemy **{old_name}** kini diketahui sebagai **{new_name}**!")

    # === Show Enemy ===
    @enemy.command(name="show")
    async def enemy_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        if name:
            row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
            rows = [row]; title = f"👹 Enemy Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM enemies"); title = "👹 Enemy Status (All)"
        embed = make_embed(rows, ctx, title=title, mode="player")
        await ctx.send(embed=embed)

    @enemy.command(name="gmshow")
    async def enemy_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        if name:
            row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
            rows = [row]; title = f"🎭 GM Enemy Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM enemies"); title = "🎭 GM Enemy Status (All)"
        embed = make_embed(rows, ctx, title=title, mode="gm")
        await ctx.send(embed=embed)

    # === Loot / Reward ===
    @enemy.command(name="loot")
    async def enemy_loot(self, ctx, enemy_name: str, char_name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (enemy_name,))
        if not row:
            return await ctx.send(f"❌ Enemy **{enemy_name}** tidak ditemukan.")
        loot_list = json.loads(row["loot"] or "[]")
        if not loot_list:
            return await ctx.send(f"🎁 Enemy **{enemy_name}** tidak punya loot.")
        for item in loot_list:
            await status_service.add_inventory(guild_id, char_name, item["name"], 1, meta=item)
        execute(guild_id, "UPDATE enemies SET loot=? WHERE name=?", ("[]", enemy_name))
        await ctx.send(f"🎁 {char_name} mendapatkan loot dari {enemy_name}: {', '.join([it['name'] for it in loot_list])}")

    @enemy.command(name="reward")
    async def enemy_reward(self, ctx, enemy_name: str, char_name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (enemy_name,))
        if not row:
            return await ctx.send(f"❌ Enemy **{enemy_name}** tidak ditemukan.")
        xp, gold = row.get("xp_reward", 0), row.get("gold_reward", 0)
        if xp: await status_service.add_xp(guild_id, char_name, xp)
        if gold: await status_service.add_gold(guild_id, char_name, gold)
        await ctx.send(f"🏆 {char_name} menerima reward dari {enemy_name}: +{xp} XP, +{gold} gold")

    # === Clear Effects ===
    @enemy.command(name="clearbuff")
    async def enemy_clearbuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, "enemy", name, is_buff=True)
        await ctx.send(f"✨ Semua buff pada {name} dihapus.")

    @enemy.command(name="cleardebuff")
    async def enemy_cleardebuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, "enemy", name, is_buff=False)
        await ctx.send(f"☠️ Semua debuff pada {name} dihapus.")

    # === Resource Ops (Stamina & Energy) ===
    @enemy.command(name="stam-")
    async def enemy_stam_use(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"⚡ {name} kehilangan {amount} stamina")

    @enemy.command(name="stam+")
    async def enemy_stam_regen(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount, regen=True)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ {name} memulihkan {amount} stamina")

    @enemy.command(name="ene-")
    async def enemy_ene_use(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"🔋 {name} kehilangan {amount} energi")

    @enemy.command(name="ene+")
    async def enemy_ene_regen(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount, regen=True)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ {name} memulihkan {amount} energi")

    # === GM Short Aliases ===
    @commands.command(name="edmg")
    async def enemy_dmg_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        
        if new_hp <= 0:
            await ctx.send(f"💀 Enemy **{name}** telah dikalahkan!")
        else:
            await ctx.send(f"💥 [GM] {name} menerima {amount} damage")

    @commands.command(name="eheal")
    async def enemy_heal_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        if new_hp is None: return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ [GM] {name} dipulihkan {amount} HP")

    @commands.command(name="ebuff")
    async def enemy_buff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=True)
        await ctx.send(f"✨ [GM] Buff ditambahkan ke {name}: {text}")

    @commands.command(name="edebuff")
    async def enemy_debuff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=False)
        await ctx.send(f"☠️ [GM] Debuff ditambahkan ke {name}: {text}")

    @commands.command(name="estam-")
    async def enemy_stam_use_short(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"⚡ [GM] {name} kehilangan {amount} stamina")

    @commands.command(name="estam+")
    async def enemy_stam_regen_short(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "stamina", amount, regen=True)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ [GM] {name} memulihkan {amount} stamina")

    @commands.command(name="eene-")
    async def enemy_ene_use_short(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"🔋 [GM] {name} kehilangan {amount} energi")

    @commands.command(name="eene+")
    async def enemy_ene_regen_short(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "enemy", name, "energy", amount, regen=True)
        if new_val is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ [GM] {name} memulihkan {amount} energi")

async def setup(bot):
    await bot.add_cog(EnemyStatus(bot))
