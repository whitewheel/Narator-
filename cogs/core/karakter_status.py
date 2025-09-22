import math
import json
import discord
from discord.ext import commands
from services import status_service, inventory_service
from utils.db import fetchall, fetchone, execute

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

async def make_embed(characters: list, ctx, title="🧍 Karakter Status"):
    embed = discord.Embed(
        title=title,
        description="📜 Status Karakter (Global)",
        color=discord.Color.blurple()
    )
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
        buffs_str = "\n".join([f"✅ {_format_effect(b)}" for b in buffs]) or "-"
        debuffs_str = "\n".join([f"❌ {_format_effect(d)}" for d in debuffs]) or "-"

        base_stats = {
            "str": c["str"], "dex": c["dex"], "con": c["con"],
            "int": c["int"], "wis": c["wis"], "cha": c["cha"]
        }
        final_stats, notes = _apply_effects(base_stats, effects)
        note_line = f" ({', '.join(notes)})" if notes else ""
        stats_line = (
            f"STR {final_stats['str']} ({_mod(final_stats['str']):+d}) | "
            f"DEX {final_stats['dex']} ({_mod(final_stats['dex']):+d}) | "
            f"CON {final_stats['con']} ({_mod(final_stats['con']):+d})\n"
            f"INT {final_stats['int']} ({_mod(final_stats['int']):+d}) | "
            f"WIS {final_stats['wis']} ({_mod(final_stats['wis']):+d}) | "
            f"CHA {final_stats['cha']} ({_mod(final_stats['cha']):+d}){note_line}"
        )

        profile_line = f"Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')} | XP {c.get('xp',0)} | 💰 {c.get('gold',0)} gold"
        combat_line = f"AC {c['ac']} | Init {c['init_mod']} | Speed {c.get('speed',30)}"

        # equipment slot fix
        eq = json.loads(c.get("equipment") or "{}")
        equip_lines = [
            f"🗡️ Main Hand: {eq.get('main_hand') or '-'}",
            f"🗡️ Off Hand: {eq.get('off_hand') or '-'}",
            f"👕 Armor Inner: {eq.get('armor_inner') or '-'}",
            f"🛡️ Armor Outer: {eq.get('armor_outer') or '-'}",
            f"💍 Accessory 1: {eq.get('accessory1') or '-'}",
            f"💍 Accessory 2: {eq.get('accessory2') or '-'}",
        ]
        equip_block = "\n".join(equip_lines)

        # inventory
        items = inventory_service.get_inventory(c["name"])
        inv_line = "\n".join([
            f"{it['item']} x{it['qty']} ({', '.join([f'{k}:{v}' for k,v in it['meta'].items()])})"
            if it['meta'] else f"{it['item']} x{it['qty']}"
            for it in items
        ]) or "-"

        # companions
        comp_list = json.loads(c.get("companions") or "[]")
        comp_line = "\n".join([
            f"{comp['name']} ({comp.get('type','')}) HP:{comp.get('hp','-')} - {comp.get('notes','')}"
            for comp in comp_list
        ]) or "-"

        value = (
            f"{profile_line}\n"
            f"❤️ HP: {hp_text} [{_bar(c['hp'], c['hp_max'])}]\n"
            f"🔋 Energy: {en_text} [{_bar(c['energy'], c['energy_max'])}]\n"
            f"⚡ Stamina: {st_text} [{_bar(c['stamina'], c['stamina_max'])}]\n\n"
            f"📊 Stats:\n{stats_line}\n\n"
            f"🛡️ Combat: {combat_line}\n\n"
            f"🎒 Equipment:\n{equip_block}\n\n"
            f"📦 Inventory:\n{inv_line}\n\n"
            f"✨ Buffs:\n{buffs_str}\n\n"
            f"☠️ Debuffs:\n{debuffs_str}\n\n"
            f"🐾 Companions:\n{comp_line}"
        )
        embed.add_field(name=c["name"], value=value, inline=False)

    return embed


class CharacterStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        rows = fetchall("SELECT * FROM characters")
        embed = await make_embed(rows, ctx)
        await ctx.send(embed=embed)

    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        exists = fetchone("SELECT id FROM characters WHERE name=?", (name,))
        if not exists:
            execute("""
                INSERT INTO characters (name, hp, hp_max, energy, energy_max, stamina, stamina_max)
                VALUES (?,?,?,?,?,?,?)
            """, (name, hp, hp, energy, energy, stamina, stamina))
        else:
            await status_service.set_status("char", name, "hp", hp)
            await status_service.set_status("char", name, "hp_max", hp)
            await status_service.set_status("char", name, "energy", energy)
            await status_service.set_status("char", name, "energy_max", energy)
            await status_service.set_status("char", name, "stamina", stamina)
            await status_service.set_status("char", name, "stamina_max", stamina)
        await ctx.send(f"✅ Karakter **{name}** diupdate.")

    @status_group.command(name="setcore")
    async def status_setcore(self, ctx, name: str, str_: int, dex: int, con: int, int_: int, wis: int, cha: int):
        for k, v in zip(["str","dex","con","int","wis","cha"], [str_, dex, con, int_, wis, cha]):
            await status_service.set_status("char", name, k, v)
        await ctx.send(f"📊 Core stats {name} diupdate.")

    @status_group.command(name="setclass")
    async def status_setclass(self, ctx, name: str, *, class_name: str):
        await status_service.set_status("char", name, "class", class_name)
        await ctx.send(f"📘 Class {name} → {class_name}")

    @status_group.command(name="setrace")
    async def status_setrace(self, ctx, name: str, *, race_name: str):
        await status_service.set_status("char", name, "race", race_name)
        await ctx.send(f"🌍 Race {name} → {race_name}")

    @status_group.command(name="setlevel")
    async def status_setlevel(self, ctx, name: str, level: int):
        await status_service.set_status("char", name, "level", level)
        await ctx.send(f"⭐ {name} sekarang level {level}.")

    @status_group.command(name="setac")
    async def status_setac(self, ctx, name: str, ac: int):
        await status_service.set_status("char", name, "ac", ac)
        await ctx.send(f"🛡️ AC {name} sekarang {ac}.")

    @status_group.command(name="equip")
    async def status_equip(self, ctx, name: str, slot: str, *, item: str):
        """Update slot equipment. Slot: main_hand, off_hand, armor_inner, armor_outer, accessory1, accessory2"""
        row = fetchone("SELECT equipment FROM characters WHERE name=?", (name,))
        eq = json.loads(row["equipment"] or "{}") if row else {}
        eq[slot.lower()] = item
        execute("UPDATE characters SET equipment=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
                (json.dumps(eq), name))
        await ctx.send(f"🎒 {name} → {slot} diisi {item}")

    @status_group.command(name="addxp")
    async def status_addxp(self, ctx, name: str, amount: int):
        await status_service.set_status("char", name, "xp", amount)
        await ctx.send(f"✨ {name} mendapat {amount} XP.")

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        execute("DELETE FROM characters WHERE name=?", (name,))
        await ctx.send(f"🗑️ Karakter **{name}** dihapus.")

    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage("char", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        await ctx.send(f"💥 {name} menerima {amount} damage → {new_hp} HP")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal("char", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        await ctx.send(f"❤️ {name} dipulihkan {amount} HP → {new_hp} HP")

    @commands.command(name="party")
    async def party(self, ctx):
        rows = fetchall("SELECT * FROM characters")
        if not rows:
            return await ctx.send("ℹ️ Belum ada karakter.")
        lines = []
        for c in rows:
            hp_text = f"{c['hp']}/{c['hp_max']}"
            en_text = f"{c['energy']}/{c['energy_max']}"
            st_text = f"{c['stamina']}/{c['stamina_max']}"
            lines.append(f"**{c['name']}** | ❤️ {hp_text} | 🔋 {en_text} | ⚡ {st_text} | Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')}")
        await ctx.send("\n".join(lines))

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
