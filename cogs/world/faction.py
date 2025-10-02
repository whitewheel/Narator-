import discord
from discord.ext import commands
from discord.ui import View, button
from services import faction_service

FACTION_ICONS = {
    "city": "🏙️",
    "region": "🏞️",
    "corp": "🏢",
    "gang": "🏴‍☠️",
    "military": "⚔️",
    "science": "🧪",
    "frontier": "🌌",
    "general": "🏷️",
}

# === Pagination View ===
class FactionPaginator(View):
    def __init__(self, pages, user):
        super().__init__(timeout=60)
        self.pages = pages
        self.user = user
        self.index = 0

    async def update_msg(self, interaction):
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @button(label="⏮️", style=discord.ButtonStyle.gray)
    async def first(self, interaction, _):
        if interaction.user != self.user: return
        self.index = 0
        await self.update_msg(interaction)

    @button(label="◀️", style=discord.ButtonStyle.blurple)
    async def prev(self, interaction, _):
        if interaction.user != self.user: return
        if self.index > 0:
            self.index -= 1
        await self.update_msg(interaction)

    @button(label="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, _):
        if interaction.user != self.user: return
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self.update_msg(interaction)

    @button(label="⏭️", style=discord.ButtonStyle.gray)
    async def last(self, interaction, _):
        if interaction.user != self.user: return
        self.index = len(self.pages) - 1
        await self.update_msg(interaction)


class Faction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="faction", invoke_without_command=True)
    async def faction(self, ctx):
        await ctx.send("Gunakan: `!faction add|list [type]|detail|remove|hide|show|gmshow|type|resetdb`")

    @faction.command(name="add")
    async def faction_add(self, ctx, *, entry: str):
        """Tambah faction baru. Format: Nama | Deskripsi | [Type]"""
        guild_id = ctx.guild.id
        parts = [p.strip() for p in entry.split("|")]
        if len(parts) < 1:
            return await ctx.send("⚠️ Format: `!faction add Nama | Deskripsi | [Type]`")
        name = parts[0]
        desc = parts[1] if len(parts) > 1 else ""
        ftype = parts[2].lower() if len(parts) > 2 else "general"
        msg = faction_service.add_faction(guild_id, name, desc, ftype, hidden=0)
        await ctx.send(msg)

    @faction.command(name="list")
    async def faction_list(self, ctx, ftype: str = None):
        """List semua faction visible (bisa filter: corp/gang/city/etc).
        Kalau tanpa filter → group per kategori"""
        guild_id = ctx.guild.id
        rows = faction_service.list_factions(guild_id, include_hidden=False)

        if not rows:
            return await ctx.send("❌ Tidak ada faction ditemukan.")

        # === Kalau pakai filter (misal !faction list corp) ===
        if ftype:
            rows = [r for r in rows if r.get("type") == ftype]
            if not rows:
                return await ctx.send(f"❌ Tidak ada faction dengan type `{ftype}`.")
            
            pages = []
            chunk_size = 10
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i+chunk_size]
                embed = discord.Embed(
                    title=f"🏷️ Daftar Factions ({ftype})",
                    description="Faction yang diketahui publik.",
                    color=discord.Color.blue()
                )
                for r in chunk:
                    icon = FACTION_ICONS.get(r.get("type", "general"), "🏷️")
                    embed.add_field(
                        name=f"{icon} **{r['name']}**",
                        value=r.get("desc", "-"),
                        inline=False
                    )
                embed.set_footer(text=f"Halaman {len(pages)+1}/{(len(rows)-1)//chunk_size+1}")
                pages.append(embed)

            view = FactionPaginator(pages, ctx.author)
            return await ctx.send(embed=pages[0], view=view)

        # === Kalau tanpa filter → Group per kategori ===
        categories = {}
        for r in rows:
            cat = r.get("type", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        pages = []
        for cat, items in categories.items():
            embed = discord.Embed(
                title=f"{FACTION_ICONS.get(cat,'🏷️')} {cat.capitalize()} Factions",
                description=f"Daftar faction type **{cat}**.",
                color=discord.Color.blue()
            )
            for r in items:
                icon = FACTION_ICONS.get(r.get("type", "general"), "🏷️")
                embed.add_field(
                    name=f"{icon} **{r['name']}**",
                    value=r.get("desc", "-"),
                    inline=False
                )
            pages.append(embed)

        view = FactionPaginator(pages, ctx.author)
        await ctx.send(embed=pages[0], view=view)

    @faction.command(name="gmshow")
    @commands.has_permissions(administrator=True)
    async def faction_gmshow(self, ctx):
        """List semua faction termasuk hidden (dengan pagination)"""
        guild_id = ctx.guild.id
        rows = faction_service.list_factions(guild_id, include_hidden=True)
        if not rows:
            return await ctx.send("❌ Tidak ada faction.")
        
        pages = []
        chunk_size = 10
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i+chunk_size]
            embed = discord.Embed(
                title="🏷️ [GM] Daftar Semua Factions",
                description="Termasuk faction yang disembunyikan.",
                color=discord.Color.purple()
            )
            for r in chunk:
                status = "🙈 Hidden" if r.get("hidden", 0) == 1 else "👁️ Visible"
                icon = FACTION_ICONS.get(r.get("type", "general"), "🏷️")
                embed.add_field(
                    name=f"{icon} **{r['name']}** ({status})",
                    value=r.get("desc", "-"),
                    inline=False
                )
            embed.set_footer(text=f"Halaman {len(pages)+1}/{(len(rows)-1)//chunk_size+1}")
            pages.append(embed)

        view = FactionPaginator(pages, ctx.author)
        await ctx.send(embed=pages[0], view=view)

    @faction.command(name="detail")
    async def faction_detail(self, ctx, *, name: str):
        """Detail 1 faction"""
        guild_id = ctx.guild.id
        f = faction_service.get_faction(guild_id, name)
        if not f:
            return await ctx.send("❌ Faction tidak ditemukan.")
        status = "🙈 Hidden" if f.get("hidden", 0) == 1 else "👁️ Visible"
        icon = FACTION_ICONS.get(f.get("type", "general"), "🏷️")
        embed = discord.Embed(
            title=f"{icon} Faction: {f['name']}",
            description=f.get("desc", "-"),
            color=discord.Color.gold()
        )
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Type", value=f.get("type", "general"), inline=True)
        await ctx.send(embed=embed)

    @faction.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def faction_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.remove_faction(guild_id, name)
        await ctx.send(msg)

    @faction.command(name="hide")
    @commands.has_permissions(administrator=True)
    async def faction_hide(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.hide_faction(guild_id, name, hidden=1)
        await ctx.send(msg)

    @faction.command(name="show")
    @commands.has_permissions(administrator=True)
    async def faction_show(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        msg = faction_service.hide_faction(guild_id, name, hidden=0)
        await ctx.send(msg)

    @faction.command(name="type")
    @commands.has_permissions(administrator=True)
    async def faction_type(self, ctx, name: str, ftype: str):
        """Ubah type faction (city/region/corp/gang/etc)"""
        guild_id = ctx.guild.id
        msg = faction_service.set_faction_type(guild_id, name, ftype)
        await ctx.send(msg)

    @faction.command(name="resetdb")
    @commands.has_permissions(administrator=True)
    async def faction_resetdb(self, ctx):
        """Reset tabel factions & favors (hapus semua data)."""
        guild_id = ctx.guild.id
        try:
            from utils.db import execute
            from services import faction_service, favor_service

            # Drop tabel lama
            execute(guild_id, "DROP TABLE IF EXISTS factions")
            execute(guild_id, "DROP TABLE IF EXISTS favors")

            # Buat ulang
            faction_service.ensure_table(guild_id)
            favor_service.ensure_table(guild_id)

            await ctx.send("✅ Tabel `factions` & `favors` sudah direset. Semua data lama hilang.")
        except Exception as e:
            await ctx.send(f"❌ Gagal reset tabel: {e}")

async def setup(bot):
    await bot.add_cog(Faction(bot))
