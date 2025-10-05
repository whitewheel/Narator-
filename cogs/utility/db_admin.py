import discord
from discord.ext import commands
from utils import db
import pandas as pd
import os

class DbAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="db", invoke_without_command=True)
    async def db_group(self, ctx):
        await ctx.send("Gunakan: `!db checkschema`, `!db resettable <nama>`, atau `!db exportitems <csv/xlsx/docx/json>`")

    # ========================
    # 📘 Cek Schema Database
    # ========================
    @db_group.command(name="checkschema")
    async def checkschema(self, ctx):
        """Cek semua tabel + kolom di DB guild ini"""
        guild_id = ctx.guild.id
        schema = db.check_schema(guild_id)
        msg = "📖 Schema DB untuk guild ini:\n"
        for t, cols in schema.items():
            msg += f"**{t}**: {', '.join(cols)}\n"
        await ctx.send(msg[:1990])  # biar aman tidak melebihi limit

    # ========================
    # 🗑️ Reset Tabel
    # ========================
    @db_group.command(name="resettable")
    @commands.has_permissions(administrator=True)
    async def resettable(self, ctx, *, table: str):
        """Hapus satu tabel lalu kosongin"""
        guild_id = ctx.guild.id
        try:
            db.execute(guild_id, f"DROP TABLE IF EXISTS {table}")
            await ctx.send(f"✅ Tabel `{table}` sudah dihapus.")
        except Exception as e:
            await ctx.send(f"❌ Gagal drop tabel `{table}`: {e}")

    # ========================
    # 📤 Export Item Data
    # ========================
    @db_group.command(name="exportitems")
    @commands.has_permissions(administrator=True)
    async def exportitems(self, ctx, fmt: str = "csv"):
        """📦 Export semua item ke file (csv/xlsx/docx/json)."""
        guild_id = ctx.guild.id
        rows = db.fetchall(guild_id, "SELECT * FROM items")

        if not rows:
            return await ctx.send("❌ Tidak ada data item di database!")

        df = pd.DataFrame(rows)
        os.makedirs("/tmp", exist_ok=True)
        filename = f"/tmp/items_{guild_id}.{fmt.lower()}"

        try:
            if fmt.lower() == "csv":
                df.to_csv(filename, index=False)
            elif fmt.lower() == "xlsx":
                df.to_excel(filename, index=False)
            elif fmt.lower() == "json":
                df.to_json(filename, orient="records", indent=2)
            elif fmt.lower() == "docx":
                from docx import Document
                doc = Document()
                doc.add_heading(f"Technonesia Item Catalog", level=1)
                for _, r in df.iterrows():
                    doc.add_heading(f"{r['name']} ({r.get('rarity','?')})", level=2)
                    doc.add_paragraph(f"Type: {r.get('type','?')} | Value: {r.get('value','?')} | Weight: {r.get('weight','?')}")
                    if 'desc' in r and r['desc']:
                        doc.add_paragraph(r['desc'])
                    doc.add_paragraph("—")
                doc.save(filename)
            else:
                return await ctx.send("❌ Format tidak dikenal! Gunakan csv/xlsx/docx/json.")

            await ctx.send(
                content=f"✅ Data item diekspor sebagai **{fmt.upper()}**",
                file=discord.File(filename)
            )
        except Exception as e:
            await ctx.send(f"❌ Gagal export item: {e}")

async def setup(bot):
    await bot.add_cog(DbAdmin(bot))
