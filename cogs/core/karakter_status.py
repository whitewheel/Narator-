import math
import json
import discord
from discord.ext import commands
from services import status_service
from utils.db import fetchall, execute

def _bar(cur: int, mx: int, width: int = 12) -> str:
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

def make_embed(characters: list, ctx, title="🧍 Karakter Status"):
    embed = discord.Embed(
        title=title,
        description=f"Channel: **{ctx.channel.name}**",
        color=discord.Color.blurple()
    )
    if not characters:
        embed.add_field(name="(kosong)", value="Gunakan `!status set` untuk menambah karakter.", inline=False)
        return embed

    for c in characters:
        # ===== Basic =====
        hp_text = f"{c['hp']}/{c['hp_max']}" if c['hp_max'] else str(c['hp'])
        en_text = f"{c['energy']}/{c['energy_max']}" if c['energy_max'] else str(c['energy'])
        st_text = f"{c['stamina']}/{c['stamina_max']}" if c['stamina_max'] else str(c['stamina'])

        # ===== Stats =====
        stats_line = (
            f"STR {c['str']} ({_mod(c['str']):+d}) | "
            f"DEX {c['dex']} ({_mod(c['dex']):+d}) | "
            f"CON {c['con']} ({_mod(c['con']):+d})\n"
            f"INT {c['int']} ({_mod(c['int']):+d}) | "
            f"WIS {c['wis']} ({_mod(c['wis']):+d}) | "
            f"CHA {c['cha']} ({_mod(c['cha']):+d})"
        )

        # ===== Buffs / Debuffs =====
        buffs, debuffs = "-", "-"
        try:
            buffs = "\n".join([f"✅ {_format_effect(b)}" for b in json.loads(c["buffs"] or "[]")]) or "-"
            debuffs = "\n".join([f"❌ {_format_effect(d)}" for d in json.loads(c["debuffs"] or "[]")]) or "-"
        except:
            pass

        # ===== Profile =====
        profile_line = f"Lv {c.get('level',1)} {c.get('class','')} {c.get('race','')} | XP {c.get('xp',0)} | 💰 {c.get('gold',0)} gold"
        combat_line = f"AC {c['ac']} | Init {c['init_mod']} | Speed {c.get('speed',30)}"

        # ===== Equipment =====
        eq = json.loads(c.get("equipment") or "{}")
        equip_line = f"Weapon: {eq.get('weapon') or '-'} | Armor: {eq.get('armor') or '-'} | Accessory: {eq.get('accessory') or '-'}"

        # ===== Inventory =====
        inv_list = json.loads(c.get("inventory") or "[]")
        inv_line = "\n".join([f"{it['name']} x{it.get('qty',1)}" for it in inv_list]) or "-"

        # ===== Companions =====
        comp_list = json.loads(c.get("companions") or "[]")
        comp_line = "\n".join([f"{comp['name']} ({comp.get('type','')}) HP:{comp.get('hp','-')} - {comp.get('notes','')}" for comp in comp_list]) or "-"

        # ===== Final Value =====
        value = (
            f"{profile_line}\n"
            f"❤️ HP: {hp_text} [{_bar(c['hp'], c['hp_max'])}]\n"
            f"🔋 Energy: {en_text} [{_bar(c['energy'], c['energy_max'])}]\n"
            f"⚡ Stamina: {st_text} [{_bar(c['stamina'], c['stamina_max'])}]\n\n"
            f"📊 Stats:\n{stats_line}\n\n"
            f"🛡️ Combat: {combat_line}\n\n"
            f"🎒 Equipment: {equip_line}\n\n"
            f"📦 Inventory:\n{inv_line}\n\n"
            f"✨ Buffs:\n{buffs}\n\n"
            f"☠️ Debuffs:\n{debuffs}\n\n"
            f"🐾 Companions:\n{comp_line}"
        )
        embed.add_field(name=c["name"], value=value, inline=False)

    return embed


class CharacterStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === Group utama ===
    @commands.group(name="status", invoke_without_command=True)
    async def status_group(self, ctx):
        rows = fetchall("SELECT * FROM characters WHERE guild_id=? AND channel_id=?",
                        (str(ctx.guild.id), str(ctx.channel.id)))
        embed = make_embed(rows, ctx)
        await ctx.send(embed=embed)

    # === Set karakter baru (HP/Energy/Stamina) ===
    @status_group.command(name="set")
    async def status_set(self, ctx, name: str, hp: int, energy: int, stamina: int):
        # update via service
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "hp", hp)
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "hp_max", hp)
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "energy", energy)
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "energy_max", energy)
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "stamina", stamina)
        await status_service.set_status(ctx.guild.id, ctx.channel.id, "char", name, "stamina_max", stamina)
        await ctx.send(f"✅ Karakter **{name}** diupdate.")

    # === Show karakter spesifik ===
    @status_group.command(name="show")
    async def status_show(self, ctx, name: str = None):
        if name:
            rows = fetchall("SELECT * FROM characters WHERE guild_id=? AND channel_id=? AND name=?",
                            (str(ctx.guild.id), str(ctx.channel.id), name))
        else:
            rows = fetchall("SELECT * FROM characters WHERE guild_id=? AND channel_id=?",
                            (str(ctx.guild.id), str(ctx.channel.id)))
        embed = make_embed(rows, ctx)
        await ctx.send(embed=embed)

    # === Remove karakter ===
    @status_group.command(name="remove")
    async def status_remove(self, ctx, name: str):
        execute("DELETE FROM characters WHERE guild_id=? AND channel_id=? AND name=?",
                (str(ctx.guild.id), str(ctx.channel.id), name))
        await ctx.send(f"🗑️ Karakter **{name}** dihapus.")

    # === Damage / Heal ===
    @status_group.command(name="dmg")
    async def status_dmg(self, ctx, name: str, amount: int):
        new_hp = await status_service.damage(ctx.guild.id, ctx.channel.id, "char", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        await ctx.send(f"💥 {name} menerima {amount} damage → {new_hp} HP")

    @status_group.command(name="heal")
    async def status_heal(self, ctx, name: str, amount: int):
        new_hp = await status_service.heal(ctx.guild.id, ctx.channel.id, "char", name, amount)
        if new_hp is None:
            return await ctx.send("❌ Karakter tidak ditemukan.")
        await ctx.send(f"❤️ {name} dipulihkan {amount} HP → {new_hp} HP")

    # === Party ringkasan ===
    @commands.command(name="party")
    async def party(self, ctx):
        rows = fetchall("SELECT * FROM characters WHERE guild_id=? AND channel_id=?",
                        (str(ctx.guild.id), str(ctx.channel.id)))
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
