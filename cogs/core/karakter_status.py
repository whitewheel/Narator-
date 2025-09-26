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
        description="📜 Status Karakter",
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

        profile_line = (
            f"Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')} "
            f"| XP {c.get('xp',0)} | 💰 {c.get('gold',0)} gold"
        )
        combat_line = f"AC {c['ac']} | Init {c['init_mod']} | Speed {c.get('speed',30)}"

        # equipment slot (dengan aksesori 3 + augment 3)
        eq = json.loads(c.get("equipment") or "{}")
        equip_lines = [
            f"🗡️ Main Hand: {eq.get('main_hand') or '-'}",
            f"🗡️ Off Hand: {eq.get('off_hand') or '-'}",
            f"👕 Armor Inner: {eq.get('armor_inner') or '-'}",
            f"🛡️ Armor Outer: {eq.get('armor_outer') or '-'}",
            f"💍 Accessory 1: {eq.get('accessory1') or '-'}",
            f"💍 Accessory 2: {eq.get('accessory2') or '-'}",
            f"💍 Accessory 3: {eq.get('accessory3') or '-'}",
            f"🧬 Augment 1: {eq.get('augment1') or '-'}",
            f"🧬 Augment 2: {eq.get('augment2') or '-'}",
            f"🧬 Augment 3: {eq.get('augment3') or '-'}",
        ]
        equip_block = "\n".join(equip_lines)

        # inventory
        items = inventory_service.get_inventory(ctx.guild.id, c["name"])
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

        # carry system
        carry_line = f"⚖️ Carry: {c.get('carry_used',0):.1f} / {c.get('carry_capacity',0)}"

        value = (
            f"{profile_line}\n"
            f"❤️ HP: {hp_text} [{_bar(c['hp'], c['hp_max'])}]\n"
            f"🔋 Energy: {en_text} [{_bar(c['energy'], c['energy_max'])}]\n"
            f"⚡ Stamina: {st_text} [{_bar(c['stamina'], c['stamina_max'])}]\n\n"
            f"📊 Stats:\n{stats_line}\n\n"
            f"🛡️ Combat: {combat_line}\n"
            f"{carry_line}\n\n"
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
        guild_id = ctx.guild.id
        rows = fetchall(guild_id, "SELECT * FROM characters")
        embed = await make_embed(rows, ctx)
        await ctx.send(embed=embed)

    # ==== Quick Show Commands ====
    async def status_showhp(self, ctx, name: str):
        row = fetchone(ctx.guild.id, "SELECT hp, hp_max FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        hp_text = f"{row['hp']}/{row['hp_max']}" if row['hp_max'] else str(row['hp'])
        await ctx.send(f"❤️ **{name}** HP: {hp_text} [{_bar(row['hp'], row['hp_max'])}]")

    async def status_showene(self, ctx, name: str):
        row = fetchone(ctx.guild.id, "SELECT energy, energy_max FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        en_text = f"{row['energy']}/{row['energy_max']}" if row['energy_max'] else str(row['energy'])
        await ctx.send(f"🔋 **{name}** Energy: {en_text} [{_bar(row['energy'], row['energy_max'])}]")

    async def status_showstam(self, ctx, name: str):
        row = fetchone(ctx.guild.id, "SELECT stamina, stamina_max FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter {name} tidak ditemukan.")
        st_text = f"{row['stamina']}/{row['stamina_max']}" if row['stamina_max'] else str(row['stamina'])
        await ctx.send(f"⚡ **{name}** Stamina: {st_text} [{_bar(row['stamina'], row['stamina_max'])}]")

    # ==== existing commands ====
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

    # ... (command lain tetap sama seperti versi kamu, tidak dihapus) ...

    @commands.command(name="party")
    async def party(self, ctx):
        guild_id = ctx.guild.id
        rows = fetchall(guild_id, "SELECT * FROM characters")
        if not rows:
            return await ctx.send("ℹ️ Belum ada karakter.")
        lines = []
        for c in rows:
            hp_text = f"{c['hp']}/{c['hp_max']}"
            en_text = f"{c['energy']}/{c['energy_max']}"
            st_text = f"{c['stamina']}/{c['stamina_max']}"
            carry_line = f"⚖️ {c.get('carry_used',0):.1f}/{c.get('carry_capacity',0)}"
            lines.append(
                f"**{c['name']}** | ❤️ {hp_text} | 🔋 {en_text} | ⚡ {st_text} "
                f"| {carry_line} | Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')}"
            )
        await ctx.send("\n".join(lines))

    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        """Hapus karakter dari database."""
        guild_id = ctx.guild.id
        row = fetchone(guild_id, "SELECT id FROM characters WHERE name=?", (name,))
        if not row:
            return await ctx.send(f"❌ Karakter **{name}** tidak ditemukan.")

        execute(guild_id, "DELETE FROM characters WHERE name=?", (name,))
        await ctx.send(f"🗑️ Karakter **{name}** berhasil dihapus.")

async def setup(bot):
    await bot.add_cog(CharacterStatus(bot))
