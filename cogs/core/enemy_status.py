import json
import discord
from discord.ext import commands
from utils.db import fetchall, fetchone, execute
from services import status_service

def _bar(cur: int, mx: int, width: int = 12) -> str:
    if mx <= 0:
        return "░" * width
    cur = max(0, min(cur, mx))
    filled = int(round(width * (cur / mx)))
    return "█" * filled + "░" * (width - filled)

def make_embed(enemies: list, ctx, title="👹 Enemy Status"):
    embed = discord.Embed(
        title=title,
        description=f"Channel: **{ctx.channel.name}**",
        color=discord.Color.red()
    )
    if not enemies:
        embed.add_field(name="(kosong)", value="Gunakan `!enemy add` untuk menambah musuh.", inline=False)
        return embed

    for e in enemies:
        hp_text = f"{e['hp']}/{e['hp_max']}" if e['hp_max'] else str(e['hp'])
        buffs, debuffs = "-", "-"
        try:
            effects = json.loads(e.get("effects") or "[]")
            buffs = "\n".join([f"✅ {b['text']}" for b in effects if "buff" in b.get("text","").lower()]) or "-"
            debuffs = "\n".join([f"❌ {d['text']}" for d in effects if "debuff" in d.get("text","").lower()]) or "-"
        except:
            pass

        reward_line = f"XP {e.get('xp_reward',0)} | Gold {e.get('gold_reward',0)}"
        loot_list = json.loads(e.get("loot") or "[]")
        loot_line = "\n".join([f"- {it['name']} ({it.get('rarity','')})" for it in loot_list]) or "-"

        value = (
            f"❤️ HP: {hp_text} [{_bar(e['hp'], e['hp_max'])}]\n\n"
            f"✨ Buffs:\n{buffs}\n\n"
            f"☠️ Debuffs:\n{debuffs}\n\n"
            f"🎁 Reward: {reward_line}\n\n"
            f"🎒 Loot:\n{loot_line}"
        )
        embed.add_field(name=e["name"], value=value, inline=False)
    return embed


class EnemyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy(self, ctx):
        await ctx.send("Gunakan: `!enemy add`, `!enemy show`, `!enemy dmg`, `!enemy heal`, `!enemy loot`, `!enemy buff`, `!enemy debuff`")

    # === Tambah musuh ===
    @enemy.command(name="add")
    async def enemy_add(self, ctx, name: str, hp: int, *, opts: str = None):
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
                except: pass

        execute("""
            INSERT INTO enemies (guild_id, channel_id, name, hp, hp_max, ac, xp_reward, gold_reward, loot)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (
            str(ctx.guild.id), str(ctx.channel.id), name, hp, hp, 10, xp_reward, gold_reward, json.dumps(loots)
        ))

        await ctx.send(f"👹 Enemy **{name}** ditambahkan dengan {hp} HP.")

    # === Tampilkan status musuh ===
    @enemy.command(name="show")
    async def enemy_show(self, ctx):
        rows = fetchall("SELECT * FROM enemies WHERE guild_id=? AND channel_id=?",
                        (str(ctx.guild.id), str(ctx.channel.id)))
        embed = make_embed(rows, ctx)
        await ctx.send(embed=embed)

    # === Damage ===
    @enemy.command(name="dmg")
    async def enemy_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, ctx.channel.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"💥 Enemy {name} menerima {amount} damage → {new_hp} HP")

    # === Heal ===
    @enemy.command(name="heal")
    async def enemy_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, ctx.channel.id, "enemy", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ Enemy {name} dipulihkan {amount} HP → {new_hp} HP")

    # === Loot ===
    @enemy.command(name="loot")
    async def enemy_loot(self, ctx, name: str):
        row = fetchone("SELECT * FROM enemies WHERE guild_id=? AND channel_id=? AND name=?",
                       (str(ctx.guild.id), str(ctx.channel.id), name))
        if not row:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        loots = json.loads(row.get("loot") or "[]")
        if not loots:
            return await ctx.send("❌ Enemy ini tidak punya loot.")
        out = [f"- {it['name']} ({it.get('rarity','')})" for it in loots]
        await ctx.send(f"🎁 Loot dari {name}:\n" + "\n".join(out))

    # === Tambah Buff ===
    @enemy.command(name="buff")
    async def enemy_buff(self, ctx, name: str, *, text: str):
        effects = await status_service.add_effect(ctx.guild.id, ctx.channel.id, "enemy", name, text, is_buff=True)
        if effects is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    # === Tambah Debuff ===
    @enemy.command(name="debuff")
    async def enemy_debuff(self, ctx, name: str, *, text: str):
        effects = await status_service.add_effect(ctx.guild.id, ctx.channel.id, "enemy", name, text, is_buff=False)
        if effects is None:
            return await ctx.send("❌ Enemy tidak ditemukan.")
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    # === Clear Buffs ===
    @enemy.command(name="clearbuff")
    async def enemy_clearbuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, ctx.channel.id, "enemy", name, is_buff=True)
        await ctx.send(f"✨ Semua buff dihapus dari {name}.")

    # === Clear Debuffs ===
    @enemy.command(name="cleardebuff")
    async def enemy_cleardebuff(self, ctx, name: str):
        await status_service.clear_effects(ctx.guild.id, ctx.channel.id, "enemy", name, is_buff=False)
        await ctx.send(f"☠️ Semua debuff dihapus dari {name}.")


async def setup(bot):
    await bot.add_cog(EnemyStatus(bot))
