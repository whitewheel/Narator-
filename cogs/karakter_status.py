import math
import discord
from discord.ext import commands
from .history import history
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

def save_char_to_memory(guild_id, channel_id, user_id, name, data):
    save_memory(guild_id, channel_id, user_id, "character", json.dumps(data), {"name": name})

def load_all_characters(guild_id, channel_id):
    rows = get_recent(guild_id, channel_id, "character", 100)
    state = {}
    for (_id, cat, content, meta, ts) in rows:
        try:
            c = json.loads(content)
            name = meta.get("name", c.get("name"))
            state[name] = c
        except:
            continue
    return state

class CharacterStatus(commands.Cog):
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
                "level": 1, "xp": 0, "class": "", "race": "",
                "gold": 0, "inventory": [],
                "equipment": {"weapon": None, "armor": None, "accessory": None},
                "ac": 10, "initiative": 0, "speed": 30,
                "companions": []
            }
        v = s[name]
        # normalize values
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
        v["level"] = to_int(v.get("level",1),1)
        v["xp"] = to_int(v.get("xp",0),0)
        v["class"] = v.get("class","")
        v["race"] = v.get("race","")
        v["gold"] = to_int(v.get("gold",0),0)
        v["inventory"] = v.get("inventory",[])
        v["equipment"] = v.get("equipment",{"weapon":None,"armor":None,"accessory":None})
        v["ac"] = to_int(v.get("ac",10),10)
        v["initiative"] = to_int(v.get("initiative",0),0)
        v["speed"] = to_int(v.get("speed",30),30)
        v["companions"] = v.get("companions",[])
        return v

    def apply_rules(self, ctx, charname: str, rules: str):
        v = self._ensure_entry(ctx, charname)
        lines = []
        for rule in rules.split(";"):
            r = rule.strip()
            if not r: continue
            if r.startswith("+") or r.startswith("-"):
                if "HP" in r.upper():
                    amount = int("".join(ch for ch in r if ch.isdigit() or ch == "-" or ch == "+"))
                    if "+" in r:
                        v["hp"] = min(v["hp_max"], v["hp"] + amount)
                        lines.append(f"❤️ {charname} pulih {amount} HP.")
                    else:
                        v["hp"] = max(0, v["hp"] - abs(amount))
                        lines.append(f"💥 {charname} kena {abs(amount)} damage.")
            elif r.lower().startswith("gold:"):
                val = int(r.split(":")[1])
                v["gold"] += val
                lines.append(f"💰 {charname} gold berubah {val:+d}. Sekarang {v['gold']}.")
            elif r.lower().startswith("xp:"):
                val = int(r.split(":")[1])
                v["xp"] += val
                lines.append(f"⭐ {charname} mendapat {val} XP. Total {v['xp']}.")
            elif r.lower().startswith("buff:"):
                lines.append(f"✨ Buff ditambahkan: {r.split(':',1)[1]}")
            elif r.lower().startswith("debuff:"):
                lines.append(f"☠️ Debuff ditambahkan: {r.split(':',1)[1]}")
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, charname, v)
        return lines

    def _make_embed(self, ctx, data: dict, title="🧍 Karakter Status"):
        embed = discord.Embed(title=title, description=f"Channel: **{ctx.channel.name}**", color=discord.Color.blurple())
        if not data:
            embed.add_field(name="(kosong)", value="Gunakan `!status set` untuk menambah karakter.", inline=False)
            return embed
        for name, v in data.items():
            hp_text = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else str(v['hp'])
            en_text = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else str(v['energy'])
            st_text = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else str(v['stamina'])
            core = v["core"]
            stats_line = (
                f"STR {core['str']} ({_mod(core['str']):+d}) | "
                f"DEX {core['dex']} ({_mod(core['dex']):+d}) | "
                f"CON {core['con']} ({_mod(core['con']):+d})\n"
                f"INT {core['int']} ({_mod(core['int']):+d}) | "
                f"WIS {core['wis']} ({_mod(core['wis']):+d}) | "
                f"CHA {core['cha']} ({_mod(core['cha']):+d})"
            )
            buffs = "\n".join([f"✅ {_format_effect(b)}" for b in v["buffs"]]) if v["buffs"] else "-"
            debuffs = "\n".join([f"❌ {_format_effect(d)}" for d in v["debuffs"]]) if v["debuffs"] else "-"
            profile_line = f"Lv {v['level']} {v['class']} {v['race']} | XP {v['xp']} | 💰 {v['gold']} gold"
            combat_line = f"AC {v['ac']} | Init {v['initiative']} | Speed {v['speed']}"
            eq = v.get("equipment",{})
            equip_line = f"Weapon: {eq.get('weapon') or '-'} | Armor: {eq.get('armor') or '-'} | Accessory: {eq.get('accessory') or '-'}"
            comp_line = "\n".join([f"{c['name']} ({c.get('type','')}) HP:{c.get('hp','-')} - {c.get('notes','')}" for c in v.get("companions",[])]) or "-"
            inv_line = "\n".join([f"{it['name']} x{it.get('qty',1)}" for it in v.get("inventory",[])]) or "-"
            value = (
                f"{profile_line}\n"
                f"❤️ HP: {hp_text} [{_bar(v['hp'], v['hp_max'])}]\n"
                f"🔋 Energy: {en_text} [{_bar(v['energy'], v['energy_max'])}]\n"
                f"⚡ Stamina: {st_text} [{_bar(v['stamina'], v['stamina_max'])}]\n\n"
                f"📊 Stats:\n{stats_line}\n\n"
                f"🛡️ Combat: {combat_line}\n\n"
                f"🎒 Equipment: {equip_line}\n\n"
                f"📦 Inventory:\n{inv_line}\n\n"
                f"✨ Buffs:\n{buffs}\n\n"
                f"☠️ Debuffs:\n{debuffs}\n\n"
                f"🐾 Companions:\n{comp_line}"
            )
            embed.add_field(name=name, value=value, inline=False)
        return embed

async def setup(bot):
    cog = CharacterStatus(bot)
    await bot.add_cog(cog)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                cog.state.update(load_all_characters(str(guild.id), str(channel.id)))
            except:
                pass
