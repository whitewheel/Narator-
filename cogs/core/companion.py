import json
import discord
from discord.ext import commands
from utils.db import fetchone, execute
from services import effect_service, item_service

# ===============================
#  Helper internal
# ===============================
def _ensure_char(guild_id: int, char_name: str):
    row = fetchone(guild_id, "SELECT * FROM characters WHERE name=?", (char_name,))
    if not row:
        raise ValueError(f"Karakter {char_name} tidak ditemukan.")
    return row

def _get_companions(guild_id: int, char_name: str):
    row = _ensure_char(guild_id, char_name)
    return json.loads(row.get("companions") or "[]")

def _save_companions(guild_id: int, char_name: str, comps: list):
    execute(
        guild_id,
        "UPDATE characters SET companions=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (json.dumps(comps), char_name)
    )

def _bar(cur: int, mx: int, width: int = 12) -> str:
    if mx <= 0: return "░" * width
    cur = max(0, min(cur, mx))
    filled = int(round(width * (cur / mx)))
    return "█" * filled + "░" * (width - filled)

def _format_effect(guild_id: int, eff: dict):
    """Ambil detail effect dari library effect_service"""
    name = eff.get("name") or eff.get("id") or "???"
    data = effect_service.get_effect_lib(guild_id, name)
    dur = eff.get("duration", data["duration"] if data else 0)
    desc = eff.get("description") or (data["description"] if data else "-")
    form = eff.get("formula") or (data["formula"] if data else "")
    typ = (eff.get("type") or (data["type"] if data else "debuff")).lower()
    return f"🔹 **{name.title()}** ({dur} turn) — `{form}`\n🛈 {desc}", typ

def _format_module(guild_id: int, name: str):
    """Ambil detail modul dari item library"""
    item = item_service.get_item(guild_id, name)
    if not item:
        return f"🧩 {name} *(tidak ditemukan di katalog)*"
    return (
        f"🧩 **{item['name']}** — {item.get('type','?')} [{item.get('rarity','Common')}]\n"
        f"✨ {item.get('effect','-')}\n"
        f"📜 {item.get('rules','-')}"
    )

# ===============================
#  Embed Builder
# ===============================
def make_comp_embed(guild_id: int, char_name: str, comps: list):
    embed = discord.Embed(
        title=f"🐜 Companion Status — {char_name}",
        description="────────────────────────────",
        color=discord.Color.from_rgb(0, 200, 150)
    )

    if not comps:
        embed.add_field(name="(kosong)", value="Belum ada companion aktif.", inline=False)
        return embed

    for c in comps:
        name = c.get("name", "???")
        hp, hp_max = c.get("hp", 0), c.get("hp_max", 0)
        energy, energy_max = c.get("energy", 0), c.get("energy_max", 0)
        stamina, stamina_max = c.get("stamina", 0), c.get("stamina_max", 0)
        ac = c.get("ac", 10)
        effects = c.get("effects", [])
        modules = c.get("modules", [])

        if isinstance(effects, str):
            try: effects = json.loads(effects)
            except: effects = []
        if isinstance(modules, str):
            try: modules = json.loads(modules)
            except: modules = []

        # --- efek dari library
        buffs, debuffs = [], []
        for e in effects:
            line, typ = _format_effect(guild_id, e)
            if typ == "buff": buffs.append(line)
            else: debuffs.append(line)

        # --- core stats bar
        stat_value = (
            f"❤️ HP {hp}/{hp_max} [{_bar(hp, hp_max)}]\n"
            f"🔋 Energy {energy}/{energy_max} [{_bar(energy, energy_max)}]\n"
            f"⚡ Stamina {stamina}/{stamina_max} [{_bar(stamina, stamina_max)}]\n"
            f"🛡️ AC: **{ac}**"
        )

        embed.add_field(name=f"🔹 {name}", value=stat_value, inline=False)

        embed.add_field(name="✨ Buffs", value="\n\n".join(buffs) if buffs else "*(tidak ada)*", inline=False)
        embed.add_field(name="☠️ Debuffs", value="\n\n".join(debuffs) if debuffs else "*(tidak ada)*", inline=False)

        module_lines = [_format_module(guild_id, m) for m in modules] if modules else ["*(tidak ada modul aktif)*"]
        embed.add_field(name="🧩 Modules", value="\n\n".join(module_lines), inline=False)

    return embed

# ===============================
#  Cog utama
# ===============================
class Companion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Group utama
    @commands.group(name="comp", invoke_without_command=True)
    async def comp_group(self, ctx):
        await ctx.send(
            "Gunakan:\n"
            "`!comp show <Char>` → lihat companion\n"
            "`!comp add <Char> <Nama>` → tambah companion\n"
            "`!comp edit <Char> <Nama> <Field> <Value>` → ubah data\n"
            "`!comp remove <Char> <Nama>` → hapus companion\n"
            "`!comp clear <Char>` → hapus semua companion"
        )

    @comp_group.command(name="show")
    async def comp_show(self, ctx, char_name: str):
        guild_id = ctx.guild.id
        try: comps = _get_companions(guild_id, char_name)
        except ValueError as e: return await ctx.send(f"❌ {e}")
        await ctx.send(embed=make_comp_embed(guild_id, char_name, comps))

    @comp_group.command(name="add")
    async def comp_add(self, ctx, char_name: str, comp_name: str):
        guild_id = ctx.guild.id
        try: comps = _get_companions(guild_id, char_name)
        except ValueError as e: return await ctx.send(f"❌ {e}")

        if any(c.get("name", "").lower() == comp_name.lower() for c in comps):
            return await ctx.send(f"⚠️ Companion {comp_name} sudah ada.")

        new_comp = {
            "name": comp_name,
            "hp": 10, "hp_max": 10,
            "energy": 5, "energy_max": 5,
            "stamina": 5, "stamina_max": 5,
            "ac": 10,
            "effects": [], "modules": []
        }
        comps.append(new_comp)
        _save_companions(guild_id, char_name, comps)
        await ctx.send(f"✅ Companion **{comp_name}** ditambahkan ke {char_name}.")

    @comp_group.command(name="edit")
    async def comp_edit(self, ctx, char_name: str, comp_name: str, field: str, *, value: str):
        guild_id = ctx.guild.id
        try: comps = _get_companions(guild_id, char_name)
        except ValueError as e: return await ctx.send(f"❌ {e}")
        for c in comps:
            if c.get("name", "").lower() == comp_name.lower():
                if field not in c: return await ctx.send(f"❌ Field '{field}' tidak ditemukan.")
                if value.isdigit(): value = int(value)
                c[field] = value
                _save_companions(guild_id, char_name, comps)
                return await ctx.send(f"🛠️ Field **{field}** companion **{comp_name}** diubah menjadi **{value}**.")
        await ctx.send(f"❌ Companion {comp_name} tidak ditemukan.")

    @comp_group.command(name="remove")
    async def comp_remove(self, ctx, char_name: str, comp_name: str):
        guild_id = ctx.guild.id
        try: comps = _get_companions(guild_id, char_name)
        except ValueError as e: return await ctx.send(f"❌ {e}")
        comps = [c for c in comps if c.get("name", "").lower() != comp_name.lower()]
        _save_companions(guild_id, char_name, comps)
        await ctx.send(f"🗑️ Companion **{comp_name}** dihapus dari {char_name}.")

    @comp_group.command(name="clear")
    async def comp_clear(self, ctx, char_name: str):
        guild_id = ctx.guild.id
        try: _ensure_char(guild_id, char_name)
        except ValueError as e: return await ctx.send(f"❌ {e}")
        _save_companions(guild_id, char_name, [])
        await ctx.send(f"🧹 Semua companion **{char_name}** telah dihapus.")

    # ===============================
    # RESOURCE MANAGEMENT (HP/STM/ENE)
    # ===============================
    def _get_comp(self, guild_id, char_name, comp_name):
        comps = _get_companions(guild_id, char_name)
        for c in comps:
            if c.get("name", "").lower() == comp_name.lower():
                return comps, c
        return comps, None

    async def _save_and_reply(self, ctx, guild_id, char_name, comps, comp, field, old, new):
        _save_companions(guild_id, char_name, comps)
        bar = lambda a, b: "█" * int(12 * (a / max(b, 1))) + "░" * int(12 - 12 * (a / max(b, 1)))
        if "hp" in field: symbol = "❤️"
        elif "energy" in field: symbol = "🔋"
        else: symbol = "⚡"
        await ctx.send(f"{symbol} {comp['name']} → {field.upper()} {old} → {new} [{bar(new, comp.get(field.replace('_max',''), new))}]")

    @commands.command(name="cdmg")
    async def comp_damage(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, new = comp.get("hp", 0), max(0, comp.get("hp", 0) - amount)
        comp["hp"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "hp", old, new)

    @commands.command(name="cheal")
    async def comp_heal(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, mx = comp.get("hp", 0), comp.get("hp_max", 0)
        new = min(mx, old + amount)
        comp["hp"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "hp", old, new)

    @commands.command(name="cusestm")
    async def comp_use_stamina(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, new = comp.get("stamina", 0), max(0, comp.get("stamina", 0) - amount)
        comp["stamina"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "stamina", old, new)

    @commands.command(name="caddstm")
    async def comp_add_stamina(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, mx = comp.get("stamina", 0), comp.get("stamina_max", 0)
        new = min(mx, old + amount)
        comp["stamina"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "stamina", old, new)

    @commands.command(name="cuseene")
    async def comp_use_energy(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, new = comp.get("energy", 0), max(0, comp.get("energy", 0) - amount)
        comp["energy"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "energy", old, new)

    @commands.command(name="caddene")
    async def comp_add_energy(self, ctx, char_name: str, comp_name: str, amount: int):
        guild_id = ctx.guild.id
        comps, comp = self._get_comp(guild_id, char_name, comp_name)
        if not comp: return await ctx.send("❌ Companion tidak ditemukan.")
        old, mx = comp.get("energy", 0), comp.get("energy_max", 0)
        new = min(mx, old + amount)
        comp["energy"] = new
        await self._save_and_reply(ctx, guild_id, char_name, comps, comp, "energy", old, new)

async def setup(bot):
    await bot.add_cog(Companion(bot))
