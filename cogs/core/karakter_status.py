import math
import json
import discord
from discord.ext import commands
from services import status_service, inventory_service
from services.equipment_service import SLOT_ICONS, SLOTS
from utils.db import fetchall, fetchone, execute

# ===== Utility =====

def _table_exists(guild_id: int, table: str) -> bool:
    row = fetchone(guild_id, "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return row is not None

def _bar(cur: int, mx: int, width: int = 12) -> str:
    if mx <= 0:
        return "░" * width
    cur = max(0, min(cur, mx))
    filled = int(round(width * (cur / mx)))
    return "█" * filled + "░" * (width - filled)

def _apply_effects(base_stats, effects):
    stats = base_stats.copy()
    notes = []
    for eff in effects:
        text = eff.get("text", "")
        for key in ["str","dex","con","int","wis","cha"]:
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

def _status_text(cur: int, mx: int) -> str:
    if mx <= 0:
        return "❓ Tidak diketahui"
    pct = (cur / mx) * 100
    if cur <= 0:
        return "💀 Tewas"
    elif pct >= 100:
        return "💪 Segar"
    elif pct >= 75:
        return "🙂 Luka Ringan"
    elif pct >= 50:
        return "⚔️ Luka Sedang"
    elif pct >= 25:
        return "🤕 Luka Berat"
    else:
        return "☠️ Sekarat"

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

async def make_embed(characters: list, ctx, title="🧍 Status Karakter"):
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    if not characters:
        embed.add_field(name="(kosong)", value="Gunakan `!status set` untuk menambah karakter.", inline=False)
        return embed

    for c in characters:
        hp_text = f"{c['hp']}/{c['hp_max']}" if c['hp_max'] else str(c['hp'])
        en_text = f"{c['energy']}/{c['energy_max']}" if c['energy_max'] else str(c['energy'])
        st_text = f"{c['stamina']}/{c['stamina_max']}" if c['stamina_max'] else str(c['stamina'])

        effects = json.loads(c.get("effects") or "[]")
        buffs = [e for e in effects if "buff" in e.get("type","").lower()]
        debuffs = [e for e in effects if "debuff" in e.get("type","").lower()]

        base_stats = {
            "str": c["str"], "dex": c["dex"], "con": c["con"],
            "int": c["int"], "wis": c["wis"], "cha": c["cha"]
        }
        final_stats, notes = _apply_effects(base_stats, effects)
        note_line = f" ({', '.join(notes)})" if notes else ""
        stats_line = (
            f"STR {final_stats['str']} | "
            f"DEX {final_stats['dex']} | "
            f"CON {final_stats['con']}\n"
            f"INT {final_stats['int']} | "
            f"WIS {final_stats['wis']} | "
            f"CHA {final_stats['cha']}{note_line}"
        )

        profile_line = (
            f"Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')} "
            f"| XP {c.get('xp',0)} | 💰 {c.get('gold',0)} gold"
        )
        combat_line = f"AC {c['ac']} | Init {c['init_mod']} | Speed {c.get('speed',30)}"
        carry_line = f"⚖️ Carry: {c.get('carry_used',0):.1f} / {c.get('carry_capacity',0)}"

        # equipment slot
        eq = json.loads(c.get("equipment") or "{}")
        if not eq:
            eq = {s: "" for s in SLOTS}

        equip_block = "\n".join([
            f"{SLOT_ICONS.get(slot,'▫️')} {slot}: {eq.get(slot) or '(kosong)'}"
            for slot in SLOTS
        ])

        # inventory
        items = inventory_service.get_inventory(ctx.guild.id, c["name"])
        inv_line = "\n".join([
            f"({it['qty']}x) {it['item']}"
            for it in items
        ]) or "-"

        # companions
        comp_list = json.loads(c.get("companions") or "[]")
        comp_line = "\n".join([
            f"{comp['name']} ({comp.get('type','')}) HP:{comp.get('hp','-')} - {comp.get('notes','')}"
            for comp in comp_list
        ]) or "-"

        value = (
            f"{profile_line}\n\n"
            f"❤️ HP {hp_text} [{_bar(c['hp'], c['hp_max'])}]\n"
            f"🔋 Energy {en_text} [{_bar(c['energy'], c['energy_max'])}]\n"
            f"⚡ Stamina {st_text} [{_bar(c['stamina'], c['stamina_max'])}]\n\n"
            f"📊 Stats\n{stats_line}\n\n"
            f"⚔️ Combat\n{combat_line}\n{carry_line}\n\n"
            f"🎒 Equipment\n{equip_block}\n\n"
            f"📦 Inventory\n{inv_line}"
        )
        embed.add_field(name=f"🧍 {c['name']}", value=value, inline=False)

        if buffs:
            embed.add_field(name="✨ Buffs", value="\n".join([f"✅ {_format_effect(b)}" for b in buffs]), inline=False)
        if debuffs:
            embed.add_field(name="☠️ Debuffs", value="\n".join([f"❌ {_format_effect(d)}" for d in debuffs]), inline=False)
        if comp_list:
            embed.add_field(name="🐾 Companions", value=comp_line, inline=False)

    return embed

# ===== Cog =====

class CharacterStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==== Base Group ====
    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        guild_id = ctx.guild.id
        rows = fetchall(guild_id, "SELECT * FROM characters")

        # refresh semua carry sebelum tampil
        for r in rows:
            inventory_service.calc_carry(guild_id, r["name"])

        embed = await make_embed(rows, ctx)
        await ctx.send(embed=embed)

    # ==== Show Commands ====
    @status_group.command(name="show")
    async def status_show(self, ctx, name: str):
        guild_id = ctx.guild.id
        inventory_service.calc_carry(guild_id, name)
        row = fetchone(guild_id, "SELECT * FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        embed = await make_embed([row], ctx, title=f"🧍 Status {name}")
        await ctx.send(embed=embed)

    # ==== Combat (HP) ====
    @commands.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        new_val = await status_service.damage(ctx.guild.id, "char", name, amount)
        await ctx.send(f"💥 {name} menerima {amount} damage → HP sekarang {new_val}")

    @commands.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        new_val = await status_service.heal(ctx.guild.id, "char", name, amount)
        await ctx.send(f"✨ {name} dipulihkan {amount} HP → HP sekarang {new_val}")

    # ==== Buff & Debuff ====
    @commands.command(name="buff")
    async def add_buff(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "char", name, text, is_buff=True)
        await ctx.send(f"✨ Buff ditambahkan ke {name}: {text}")

    @commands.command(name="debuff")
    async def add_debuff(self, ctx, name: str, *, text: str):
        await status_service.add_effect(ctx.guild.id, "char", name, text, is_buff=False)
        await ctx.send(f"☠️ Debuff ditambahkan ke {name}: {text}")

    # ==== Resource Commands (Stamina & Energy) ====
    @commands.command(name="addstm")
    async def stamina_regen(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "char", name, "stamina", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan {amount} stamina → {new_val}")

    @commands.command(name="usestm")
    async def stamina_use(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "char", name, "stamina", amount)
        await ctx.send(f"⚡ {name} menggunakan {amount} stamina → tersisa {new_val}")

    @commands.command(name="addene")
    async def energy_regen(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "char", name, "energy", amount, regen=True)
        await ctx.send(f"✨ {name} memulihkan {amount} energy → {new_val}")

    @commands.command(name="useene")
    async def energy_use(self, ctx, name: str, amount: int):
        new_val = await status_service.use_resource(ctx.guild.id, "char", name, "energy", amount)
        await ctx.send(f"🔋 {name} menggunakan {amount} energy → tersisa {new_val}")

    # ==== Setters ====
    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        guild_id = ctx.guild.id
        exists = fetchone(guild_id, "SELECT id FROM characters WHERE name=?", (name,))
        if not exists:
            execute(guild_id, """
                INSERT INTO characters (name, hp, hp_max, energy, energy_max, stamina, stamina_max)
                VALUES (?,?,?,?,?,?,?)
            """, (name, hp, hp, energy, energy, stamina, stamina))
        else:
            await status_service.set_status(guild_id, "char", name, "hp", hp)
            await status_service.set_status(guild_id, "char", name, "hp_max", hp)
            await status_service.set_status(guild_id, "char", name, "energy", energy)
            await status_service.set_status(guild_id, "char", name, "energy_max", energy)
            await status_service.set_status(guild_id, "char", name, "stamina", stamina)
            await status_service.set_status(guild_id, "char", name, "stamina_max", stamina)
        await ctx.send(f"✅ Karakter **{name}** diupdate.")

    @status_group.command(name="setcore")
    async def status_setcore(self, ctx, name: str, STR: int, DEX: int, CON: int, INT: int, WIS: int, CHA: int):
        guild_id = ctx.guild.id
        for stat, val in zip(["str","dex","con","int","wis","cha"], [STR,DEX,CON,INT,WIS,CHA]):
            await status_service.set_status(guild_id, "char", name, stat, val)
        await ctx.send(f"✅ Core stats {name} diupdate.")

    @status_group.command(name="setclass")
    async def status_setclass(self, ctx, name: str, *, classname: str):
        await status_service.set_status(ctx.guild.id, "char", name, "class", classname)
        await ctx.send(f"🎓 Class {name} → {classname}")

    @status_group.command(name="setrace")
    async def status_setrace(self, ctx, name: str, *, racename: str):
        await status_service.set_status(ctx.guild.id, "char", name, "race", racename)
        await ctx.send(f"🧬 Race {name} → {racename}")

    @status_group.command(name="setlevel")
    async def status_setlevel(self, ctx, name: str, level: int):
        await status_service.set_status(ctx.guild.id, "char", name, "level", level)
        await ctx.send(f"⬆️ Level {name} → {level}")

    @status_group.command(name="setac")
    async def status_setac(self, ctx, name: str, ac: int):
        await status_service.set_status(ctx.guild.id, "char", name, "ac", ac)
        await ctx.send(f"🛡️ AC {name} → {ac}")

    @status_group.command(name="setcarry")
    async def status_setcarry(self, ctx, name: str, capacity: float):
        guild_id = ctx.guild.id
        execute(guild_id, "UPDATE characters SET carry_capacity=? WHERE name=?", (capacity, name))
        await ctx.send(f"⚖️ Kapasitas carry {name} → {capacity}")

    # ==== XP & Gold ====
    @status_group.command(name="addxp")
    async def status_addxp(self, ctx, name: str, amount: int):
        level_up = await status_service.add_xp(ctx.guild.id, name, amount)
        if level_up:
            await ctx.send(f"✨ {name} naik ke **Level {level_up}**!")
        else:
            await ctx.send(f"📈 {name} mendapat {amount} XP")

    @status_group.command(name="subxp")
    async def status_subxp(self, ctx, name: str, amount: int):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT xp FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        current = row["xp"] or 0
        new_val = max(0, current - amount)
        execute(guild_id, "UPDATE characters SET xp=? WHERE name=?", (new_val, name))
        await ctx.send(f"📉 {name} kehilangan {amount} XP → sisa {new_val}")

    @status_group.command(name="addgold")
    async def status_addgold(self, ctx, name: str, amount: int):
        await status_service.add_gold(ctx.guild.id, name, amount)
        await ctx.send(f"💰 {name} mendapat {amount} gold")

    @status_group.command(name="subgold")
    async def status_subgold(self, ctx, name: str, amount: int):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT gold FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        current = row["gold"] or 0
        new_val = max(0, current - amount)
        execute(guild_id, "UPDATE characters SET gold=? WHERE name=?", (new_val, name))
        await ctx.send(f"💸 {name} mengeluarkan {amount} gold → sisa {new_val}")

    # ==== Party & Remove ====
    @commands.command(name="party")
    async def party(self, ctx):
        guild_id = ctx.guild.id
        chars = fetchall(guild_id, "SELECT * FROM characters")

        allies = []
        if _table_exists(guild_id, "allies"):
            allies = fetchall(guild_id, "SELECT * FROM allies")

        if not chars and not allies:
            return await ctx.send("ℹ️ Belum ada karakter atau ally.")

        lines = ["🧑‍🤝‍🧑 **Party Status**"]

        # === Player characters ===
        for c in chars:
            inventory_service.calc_carry(guild_id, c["name"])
            hp_text = f"{c['hp']}/{c['hp_max']} [{_bar(c['hp'], c['hp_max'])}]"
            en_text = f"{c['energy']}/{c['energy_max']} [{_bar(c['energy'], c['energy_max'])}]"
            st_text = f"{c['stamina']}/{c['stamina_max']} [{_bar(c['stamina'], c['stamina_max'])}]"

            line = f"🧍 **{c['name']}** | ❤️ {hp_text} | 🔋 {en_text} | ⚡ {st_text}"
            lines.append(line)

        # === Allies ===
        for a in allies:
            hp_status = _status_text(a['hp'], a['hp_max'])
            en_status = _energy_status(a['energy'], a['energy_max'])
            st_status = _stamina_status(a['stamina'], a['stamina_max'])

            line = (
                f"🤝 **{a['name']}** | "
                f"❤️ - {hp_status} | "
                f"🔋 - {en_status} | "
                f"⚡ - {st_status}"
            )
            lines.append(line)

        await ctx.send("\n".join(lines))

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT id FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter **{name}** tidak ditemukan.")
        execute(guild_id, "DELETE FROM characters WHERE name=?", (name,))
        await ctx.send(f"🗑️ Karakter **{name}** berhasil dihapus.")

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
