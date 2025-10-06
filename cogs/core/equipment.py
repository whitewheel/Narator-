import discord
from discord.ext import commands
from services import equipment_service, item_service

VALID_SLOTS = [
    "main_hand", "off_hand",
    "armor_inner", "armor_outer",
    "accessory1", "accessory2", "accessory3",
    "augment1", "augment2", "augment3",
    "mod"
]

CATEGORY_DIVIDERS = {
    "armor_outer": "🟦 ───────────── ⚙️ **Armor & Protection** ─────────────",
    "accessory1": "🟣 ───────────── 💍 **Accessories** ─────────────",
    "augment1": "🟢 ───────────── 🧬 **Augments** ─────────────",
    "mod": "🟠 ───────────── 🧩 **Mods** ─────────────"
}


class Equipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="equip", invoke_without_command=True)
    async def equip_group(self, ctx):
        await ctx.send(
            "🧰 **Equipment Commands**\n"
            "• `!equip set <char> <slot> <item>` → pasang item\n"
            "• `!equip remove <char> <slot>` → lepas item\n"
            "• `!equip remove_mod <char> <item>` → lepas mod tertentu\n"
            "• `!equip show <char>` → lihat semua slot\n\n"
            f"Slot valid: `{', '.join(VALID_SLOTS)}`"
        )

    @equip_group.command(name="set")
    async def equip_set(self, ctx, char: str, slot: str, *, item: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.equip_item(
            guild_id, char, slot, item, user_id=str(ctx.author.id)
        )
        embed = discord.Embed(
            title="⚔️ Equip Item" if ok else "❌ Equip Gagal",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @equip_group.command(name="remove")
    async def equip_remove(self, ctx, char: str, slot: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.unequip_item(
            guild_id, char, slot, user_id=str(ctx.author.id)
        )
        embed = discord.Embed(
            title="🛑 Unequip Item" if ok else "❌ Unequip Gagal",
            description=msg,
            color=discord.Color.orange() if ok else discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @equip_group.command(name="remove_mod")
    async def equip_remove_mod(self, ctx, char: str, *, item: str):
        guild_id = ctx.guild.id
        ok, msg = equipment_service.remove_mod(
            guild_id, char, item, user_id=str(ctx.author.id)
        )
        embed = discord.Embed(
            title="🧩 Remove Mod" if ok else "❌ Remove Mod Gagal",
            description=msg,
            color=discord.Color.orange() if ok else discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @equip_group.command(name="show")
    async def equip_show(self, ctx, char: str):
        guild_id = ctx.guild.id
        eq_dict = equipment_service.get_equipment_dict(guild_id, char)
        if not eq_dict:
            return await ctx.send(f"❌ Karakter **{char}** tidak ditemukan.")

        embed = discord.Embed(
            title=f"🧰 Equipment {char}",
            color=discord.Color.from_str("#3498db")
        )

        ordered_slots = [
            "main_hand", "off_hand",
            "armor_inner", "armor_outer",
            "accessory1", "accessory2", "accessory3",
            "augment1", "augment2", "augment3",
            "mod"
        ]

        # Loop semua slot kecuali mod dulu
        for slot in ordered_slots:
            # Divider antar kategori
            if slot in CATEGORY_DIVIDERS:
                embed.add_field(name="\u200b", value=CATEGORY_DIVIDERS[slot], inline=False)

            # Tangani slot selain mod
            if slot != "mod":
                item_name = eq_dict.get(slot, "(kosong)")
                item_data = item_service.get_item_details(guild_id, item_name)
                desc_lines = []
                if item_data:
                    if item_data.get("effect"):
                        desc_lines.append(f"- {item_data['effect']}")
                    if item_data.get("rules"):
                        desc_lines.append(f"- {item_data['rules']}")
                    if item_data.get("notes"):
                        desc_lines.append(f"- {item_data['notes']}")
                desc_text = "\n".join(desc_lines) if desc_lines else "_Tidak ada deskripsi._"

                embed.add_field(
                    name=f"**{slot}** — {item_name}",
                    value=f"{desc_text}\n\u200b",
                    inline=False
                )

                # Tambahkan jarak antar accessories & augments
                if slot in ["accessory1", "accessory2", "augment1", "augment2"]:
                    embed.add_field(name="\u200b", value="\u200b", inline=False)

        # === Bagian MOD (bisa banyak)
        embed.add_field(name="\u200b", value=CATEGORY_DIVIDERS["mod"], inline=False)

        mods = equipment_service.get_mod_list(guild_id, char)  # → list semua mod (kalau ada)
        if not mods:
            embed.add_field(name="(mod slot)", value="(kosong)\n\u200b", inline=False)
        else:
            for mod_name in mods:
                item_data = item_service.get_item_details(guild_id, mod_name)
                desc_lines = []
                if item_data:
                    if item_data.get("effect"):
                        desc_lines.append(f"- {item_data['effect']}")
                    if item_data.get("rules"):
                        desc_lines.append(f"- {item_data['rules']}")
                    if item_data.get("notes"):
                        desc_lines.append(f"- {item_data['notes']}")
                desc_text = "\n".join(desc_lines) if desc_lines else "_Tidak ada deskripsi._"

                embed.add_field(
                    name=f"🧩 {mod_name}",
                    value=f"{desc_text}\n\u200b",
                    inline=False
                )

                # jarak antar mod biar enak dibaca
                embed.add_field(name="\u200b", value="\u200b", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Equipment(bot))
