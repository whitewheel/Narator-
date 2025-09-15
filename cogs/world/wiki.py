from discord.ext import commands
from utils.db import execute, query_all, query_one
from utils.embeds import info_embed, error_embed, ok_embed
import discord

class WikiCog(commands.Cog):
    """📚 Wiki / Lore Reference"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="wiki", invoke_without_command=True)
    async def wiki(self, ctx: commands.Context):
        """Command utama Wiki"""
        await ctx.send(embed=info_embed("📚 Wiki Commands",
        "`!wiki get <category> <name>` → lihat data tertentu\n"
        "`!wiki list <category>` → daftar semua entry\n"
        "`!wiki add <category> <name> | <content>` (GM only)\n"
        "`!wiki remove <id>` (GM only)"
        ))

    # GET entry
    @wiki.command(name="get")
    async def get(self, ctx: commands.Context, category: str, *, name: str):
        row = query_one("SELECT * FROM wiki WHERE category=? AND name=?", (category.lower(), name.lower()))
        if not row:
            await ctx.send(embed=error_embed(f"Tidak ada **{category}** bernama `{name}`"))
            return
        e = discord.Embed(
            title=f"📖 {category.title()}: {row['name'].title()}",
            description=row['content'],
            color=discord.Color.blue()
        )
        e.set_footer(text=f"ID #{row['id']} • Ditambah pada {row['created_at']}")
        await ctx.send(embed=e)

    # LIST entries
    @wiki.command(name="list")
    async def list_(self, ctx: commands.Context, category: str):
        rows = query_all("SELECT * FROM wiki WHERE category=? ORDER BY name ASC", (category.lower(),))
        if not rows:
            await ctx.send(embed=info_embed(f"📚 {category.title()}", "❌ Belum ada data."))
            return
        lines = [f"#{r['id']} • **{r['name'].title()}**" for r in rows]
        desc = "\n".join(lines)
        await ctx.send(embed=info_embed(f"📚 {category.title()} Entries", desc))

    # ADD entry (GM only)
    @wiki.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, category: str, *, text: str):
        parts = [p.strip() for p in text.split("|", 1)]
        if len(parts) < 2:
            await ctx.send(embed=error_embed("Gunakan format: `<name> | <content>`"))
            return
        name, content = parts
        execute("INSERT INTO wiki (category, name, content) VALUES (?,?,?)", 
                (category.lower(), name.lower(), content))
        await ctx.send(embed=ok_embed("✅ Wiki updated", f"{category.title()} `{name}` ditambahkan."))

    # REMOVE entry (GM only)
    @wiki.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, wid: int):
        execute("DELETE FROM wiki WHERE id=?", (wid,))
        await ctx.send(embed=ok_embed("🗑️ Wiki removed", f"Entry #{wid} dihapus."))

async def setup(bot: commands.Bot):
    await bot.add_cog(WikiCog(bot))
