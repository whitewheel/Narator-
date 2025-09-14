
import math
import discord
from discord.ext import commands
from .history import history
from memory import save_memory, get_recent
from cogs.world.timeline import log_event
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
        return s[name]

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

    # ===== Group Command =====
    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        s = self._ensure(ctx)
        embed = self._make_embed(ctx, s)
        await ctx.send(embed=embed)

    # ===== Subcommands =====
    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        v = self._ensure_entry(ctx, name)
        v.update({"hp": hp, "hp_max": hp,
                  "energy": energy, "energy_max": energy,
                  "stamina": stamina, "stamina_max": stamina})
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"✅ Karakter **{name}** diupdate.")

    @status_group.command(name="show")
    async def status_show(self, ctx, name: str = None):
        s = self._ensure(ctx)
        data = {name: s.get(name)} if name and name in s else (s if not name else {})
        embed = self._make_embed(ctx, data)
        await ctx.send(embed=embed)

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        if name in s:
            del s[name]
            await ctx.send(f"🗑️ Karakter **{name}** dihapus.")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @status_group.command(name="clear")
    async def status_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        await ctx.send("🧹 Semua karakter dihapus.")

    @status_group.command(name="setcore")
    async def status_setcore(self, ctx, name: str, str_: int, dex: int, con: int, int_: int, wis: int, cha: int):
        v = self._ensure_entry(ctx, name)
        v["core"] = {"str": str_, "dex": dex, "con": con, "int": int_, "wis": wis, "cha": cha}
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"📊 Core stats {name} diupdate.")

    @status_group.command(name="setclass")
    async def status_setclass(self, ctx, name: str, *, class_name: str):
        v = self._ensure_entry(ctx, name)
        v["class"] = class_name
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"📘 Class {name} → {class_name}")

    @status_group.command(name="setrace")
    async def status_setrace(self, ctx, name: str, *, race_name: str):
        v = self._ensure_entry(ctx, name)
        v["race"] = race_name
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"🌍 Race {name} → {race_name}")

    @status_group.command(name="setlevel")
    async def status_setlevel(self, ctx, name: str, level: int):
        v = self._ensure_entry(ctx, name)
        v["level"] = level
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"⭐ {name} sekarang level {level}.")

    @status_group.command(name="addxp")
    async def status_addxp(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["xp"] += amount
        save_char_to_memory(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id, name, v)
        await ctx.send(f"✨ {name} mendapat {amount} XP (total {v['xp']}).")

    # Buff / Debuff
    @status_group.command(name="buff")
    async def status_buff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"].append({"text": text, "duration": -1})
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @status_group.command(name="debuff")
    async def status_debuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"].append({"text": text, "duration": -1})
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    @status_group.command(name="clearbuff")
    async def status_clearbuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"] = []
        await ctx.send(f"✨ Semua buff dihapus dari {name}.")

    @status_group.command(name="cleardebuff")
    async def status_cleardebuff(self, ctx, name: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"] = []
        await ctx.send(f"☠️ Semua debuff dihapus dari {name}.")

    @status_group.command(name="unbuff")
    async def status_unbuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["buffs"] = [b for b in v["buffs"] if b["text"] != text]
        await ctx.send(f"✨ Buff {text} dihapus dari {name}.")

    @status_group.command(name="undebuff")
    async def status_undebuff(self, ctx, name: str, *, text: str):
        v = self._ensure_entry(ctx, name)
        v["debuffs"] = [d for d in v["debuffs"] if d["text"] != text]
        await ctx.send(f"☠️ Debuff {text} dihapus dari {name}.")

    # HP, Energy, Stamina control
    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] = max(0, v["hp"] - amount)
        await ctx.send(f"💥 {name} menerima {amount} damage.")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["hp"] = min(v["hp_max"], v["hp"] + amount)
        await ctx.send(f"❤️ {name} pulih {amount} HP.")

    @status_group.command(name="useenergy")
    async def status_useenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] = max(0, v["energy"] - amount)
        await ctx.send(f"🔋 {name} menggunakan {amount} energi.")

    @status_group.command(name="regenenergy")
    async def status_regenenergy(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["energy"] = min(v["energy_max"], v["energy"] + amount)
        await ctx.send(f"🔋 {name} memulihkan {amount} energi.")

    @status_group.command(name="usestam")
    async def status_usestam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] = max(0, v["stamina"] - amount)
        await ctx.send(f"⚡ {name} menggunakan {amount} stamina.")

    @status_group.command(name="regenstam")
    async def status_regenstam(self, ctx, name: str, amount: int):
        v = self._ensure_entry(ctx, name)
        v["stamina"] = min(v["stamina_max"], v["stamina"] + amount)
        await ctx.send(f"⚡ {name} memulihkan {amount} stamina.")

    # ===== Party Ringkasan =====
    @commands.command(name="party")
    async def party(self, ctx):
        s = self._ensure(ctx)
        if not s:
            return await ctx.send("ℹ️ Belum ada karakter.")
        lines = []
        for name, v in s.items():
            hp_text = f"{v['hp']}/{v['hp_max']}" if v['hp_max'] else str(v['hp'])
            en_text = f"{v['energy']}/{v['energy_max']}" if v['energy_max'] else str(v['energy'])
            st_text = f"{v['stamina']}/{v['stamina_max']}" if v['stamina_max'] else str(v['stamina'])
            lines.append(f"**{name}** | ❤️ {hp_text} | 🔋 {en_text} | ⚡ {st_text} | Lv {v['level']} {v['class']} {v['race']}")
        await ctx.send("\n".join(lines))

async def setup(bot):
    cog = CharacterStatus(bot)
    await bot.add_cog(cog)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                cog.state.update(load_all_characters(str(guild.id), str(channel.id)))
            except:
                pass
