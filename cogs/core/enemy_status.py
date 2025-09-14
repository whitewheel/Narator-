import math
import discord
from discord.ext import commands
from memory import save_memory, get_recent, template_for
import json

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

def save_enemy_to_memory(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "enemy", json.dumps(data), {"name": name})

def load_all_enemies(guild_id, channel_id):
    rows = get_recent(guild_id, channel_id, "enemy", 100)
    state = {}
    for (_id, cat, content, meta, ts) in rows:
        try:
            e = json.loads(content)
            name = meta.get("name", e.get("name"))
            state[name] = e
        except:
            continue
    return state

class EnemyStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = {}

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
                "buffs": [], "debuffs": [],
                "xp_reward": 0, "gold_reward": 0, "loot": []
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
        v["xp_reward"] = to_int(v.get("xp_reward",0),0)
        v["gold_reward"] = to_int(v.get("gold_reward",0),0)
        v["loot"] = v.get("loot", [])
        return v

    def _make_embed(self, ctx, data: dict, title="👹 Enemy Status"):
        embed = discord.Embed(title=title, description=f"Channel: **{ctx.channel.name}**", color=discord.Color.red())
        if not data:
            embed.add_field(name="(kosong)", value="Gunakan `!enemy add` untuk menambah musuh.", inline=False)
            return embed
        for name, v in data.items():
            hp_text = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else str(v['hp'])
            stats_line = (
                f"STR {v['core']['str']} ({_mod(v['core']['str']):+d}) | "
                f"DEX {v['core']['dex']} ({_mod(v['core']['dex']):+d}) | "
                f"CON {v['core']['con']} ({_mod(v['core']['con']):+d})"
            )
            buffs = "\n".join([f"✅ {_format_effect(b)}" for b in v["buffs"]]) if v["buffs"] else "-"
            debuffs = "\n".join([f"❌ {_format_effect(d)}" for d in v["debuffs"]]) if v["debuffs"] else "-"
            reward_line = f"XP {v['xp_reward']} | Gold {v['gold_reward']}"
            loot_line = "\n".join([f"- {it['name']} ({it.get('rarity', '')})" for it in v.get("loot",[])]) or "-"
            value = (
                f"❤️ HP: {hp_text} [{_bar(v['hp'], v['hp_max'])}]\n"
                f"📊 Stats: {stats_line}\n"
                f"✨ Buffs:\n{buffs}\n"
                f"☠️ Debuffs:\n{debuffs}\n\n"
                f"🎁 Reward: {reward_line}\n"
                f"🎒 Loot:\n{loot_line}"
            )
            embed.add_field(name=name, value=value, inline=False)
        return embed

    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy(self, ctx):
        await ctx.send("Gunakan: `!enemy add`, `!enemy show`, `!enemy dmg`, `!enemy heal`, `!enemy loot`")

    @enemy.command(name="add")
    async def enemy_add(self, ctx, name: str, hp: int, *, opts: str = None):
        e = self._ensure_entry(ctx, name)
        e["name"] = name
        e["hp"] = hp
        e["hp_max"] = hp
        if opts:
            if "--xp" in opts:
                try: e["xp_reward"] = int(opts.split("--xp")[1].split()[0])
                except: pass
            if "--gold" in opts:
                try: e["gold_reward"] = int(opts.split("--gold")[1].split()[0])
                except: pass
            if "--loot" in opts:
                try:
                    loot_str = opts.split("--loot")[1].strip()
                    parts = loot_str.split(";")
                    loots = []
                    for p in parts:
                        segs = [s.strip() for s in p.split("|")]
                        if not segs or len(segs)<1: continue
                        item = {"name":segs[0]}
                        if len(segs)>1: item["type"]=segs[1]
                        if len(segs)>2: item["effect"]=segs[2]
                        if len(segs)>3: item["rarity"]=segs[3]
                        loots.append(item)
                    e["loot"] = loots
                except: pass
        save_enemy_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, e)
        await ctx.send(f"👹 Enemy **{name}** ditambahkan dengan {hp} HP.")

    @enemy.command(name="show")
    async def enemy_show(self, ctx):
        s = self._ensure(ctx)
        embed = self._make_embed(ctx, s)
        await ctx.send(embed=embed)

    @enemy.command(name="loot")
    async def enemy_loot(self, ctx, name: str):
        e = self._ensure_entry(ctx, name)
        loots = e.get("loot", [])
        if not loots:
            return await ctx.send("❌ Musuh ini tidak punya loot.")
        out = [f"- {it['name']} ({it.get('rarity', '')})" for it in loots]
        await ctx.send(f"🎁 Loot dari {name}:\n" + "\n".join(out))

async def setup(bot):
    cog = EnemyStatus(bot)
    await bot.add_cog(cog)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                cog.state.update(load_all_enemies(str(guild.id), str(channel.id)))
            except:
                pass
