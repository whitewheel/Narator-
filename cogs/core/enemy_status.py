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
    if mx <= 0:
        return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if cur <= 0:
        return "💀 Tewas"
    elif pct >= 100:
        return "💪 Sehat"
    elif pct >= 75:
        return "🙂 Luka Ringan"
    elif pct >= 50:
        return "⚔️ Luka Sedang"
    elif pct >= 25:
        return "🤕 Luka Berat"
    else:
        return "☠️ Sekarat"

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

        base_stats = {
            "str": e.get("str", 0), "dex": e.get("dex", 0), "con": e.get("con", 0),
            "int": e.get("int", 0), "wis": e.get("wis", 0), "cha": e.get("cha", 0),
            "ac": e.get("ac", 10)
        }
        final_stats, notes = _apply_effects(base_stats, effects)
        note_line = f" ({', '.join(notes)})" if notes else ""
        stats_line = (
            f"STR {final_stats['str']} ({_mod(final_stats['str']):+d}) | "
            f"DEX {final_stats['dex']} ({_mod(final_stats['dex']):+d}) | "
            f"CON {final_stats['con']} ({_mod(final_stats['con']):+d}) | "
            f"AC {final_stats['ac']}{note_line}"
        )

        reward_line = f"XP {e.get('xp_reward',0)} | Gold {e.get('gold_reward',0)}"
        loot_list = json.loads(e["loot"] or "[]")
        loot_line = "\n".join([f"- {it['name']} ({it.get('rarity','')})" for it in loot_list]) or "-"

        if mode == "gm":
            hp_line = f"❤️ HP: {e['hp']}/{e['hp_max']} [{_bar(e['hp'], e['hp_max'])}]"
        else:
            hp_line = f"❤️ Kondisi: {_hp_status(e['hp'], e['hp_max'])}"

        value = (
            f"{hp_line}\n\n"
            f"📊 Stats: {stats_line}\n\n"
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
        await ctx.send("Gunakan: `!enemy add`, `!enemy show`, `!enemy gmshow`, `!enemy dmg`, `!enemy heal`, `!enemy loot`, `!enemy buff`, `!enemy debuff`")

    @enemy.command(name="add")
    async def enemy_add(self, ctx, name: str, hp: int, *, opts: str = None):
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
                SET hp=?, hp_max=?, ac=?, xp_reward=?, gold_reward=?, loot=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (hp, hp, 10, xp_reward, gold_reward, json.dumps(loots), exists["id"]))
            await ctx.send(f"♻️ Enemy **{name}** diperbarui jadi {hp} HP.")
        else:
            execute(guild_id, """
                INSERT INTO enemies (name, hp, hp_max, ac, xp_reward, gold_reward, loot)
                VALUES (?,?,?,?,?,?,?)
            """, (name, hp, hp, 10, xp_reward, gold_reward, json.dumps(loots)))
            await ctx.send(f"👹 Enemy **{name}** ditambahkan dengan {hp} HP.")

    @enemy.command(name="show")
    async def enemy_show(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        if name:
            row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
            rows = [row]
            title = f"👹 Enemy Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM enemies")
            title = "👹 Enemy Status (All)"

        embed = make_embed(rows, ctx, title=title, mode="player")
        await ctx.send(embed=embed)

    @enemy.command(name="gmshow")
    async def enemy_gmshow(self, ctx, *, name: str = None):
        guild_id = ctx.guild.id
        if name:
            row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))
            if not row:
                return await ctx.send(f"❌ Enemy **{name}** tidak ditemukan.")
            rows = [row]
            title = f"🎭 GM Enemy Status: {name}"
        else:
            rows = fetchall(guild_id, "SELECT * FROM enemies")
            title = "🎭 GM Enemy Status (All)"

        embed = make_embed(rows, ctx, title=title, mode="gm")
        await ctx.send(embed=embed)

    @enemy.command(name="dmg")
    async def enemy_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"💥 Enemy {name} menerima {amount} damage → {new_hp} HP")

    @enemy.command(name="heal")
    async def enemy_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ Enemy {name} dipulihkan {amount} HP → {new_hp} HP")

    @enemy.command(name="loot")
    async def enemy_loot(self, ctx, name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT * FROM enemies WHERE name=?", (name,))
        if not row:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        loots = json.loads(row["loot"] or "[]")
        if not loots:
            return await ctx.send("❌ Enemy ini tidak punya loot.")
        out = [f"- {it['name']} ({it.get('rarity','')})" for it in loots]
        await ctx.send(f"🎁 Loot dari {name}:\n" + "\n".join(out))

    @enemy.command(name="buff")
    async def enemy_buff(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=True)
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @enemy.command(name="debuff")
    async def enemy_debuff(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=False)
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    @enemy.command(name="clearbuff")
    async def enemy_clearbuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, "enemy", name, is_buff=True)
        await ctx.send(f"✨ Semua buff dihapus dari {name}.")

    @enemy.command(name="cleardebuff")
    async def enemy_cleardebuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, "enemy", name, is_buff=False)
        await ctx.send(f"☠️ Semua debuff dihapus dari {name}.")

    # ===== Short Aliases (global, hati2 bentrok) =====

    @commands.command(name="dmg")
    async def dmg_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"💥 Enemy {name} menerima {amount} damage → {new_hp} HP")

    @commands.command(name="heal")
    async def heal_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ Enemy {name} dipulihkan {amount} HP → {new_hp} HP")

    @commands.command(name="buff")
    async def buff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=True)
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @commands.command(name="debuff")
    async def debuff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=False)
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    # ===== GM Short Aliases (prefix e) =====

    @commands.command(name="edmg")
    async def enemy_dmg_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"💥 Enemy {name} menerima {amount} damage → {new_hp} HP")

    @commands.command(name="eheal")
    async def enemy_heal_short(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ Enemy {name} dipulihkan {amount} HP → {new_hp} HP")

    @commands.command(name="ebuff")
    async def enemy_buff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=True)
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @commands.command(name="edebuff")
    async def enemy_debuff_short(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "enemy", name, text, is_buff=False)
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

async def setup(bot):
    await bot.add_cog(EnemyStatus(bot))
