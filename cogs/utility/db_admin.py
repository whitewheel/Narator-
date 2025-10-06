import os
import pandas as pd
import discord
from discord.ext import commands
from utils import db


class DbAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========================
    # 🔹 Group Command
    # ========================
    @commands.group(name="db", invoke_without_command=True)
    async def db_group(self, ctx):
        await ctx.send(
            "🧩 **Database Commands**\n"
            "• `!db checkschema` → cek semua tabel & kolom\n"
            "• `!db resettable <nama>` → hapus tabel tertentu\n"
            "• `!db exportitems <csv/xlsx/docx/json>` → ekspor item database"
        )

    # ========================
    # 📘 Cek Schema Database
    # ========================
    @db_group.command(name="checkschema")
    async def checkschema(self, ctx):
        """Cek semua tabel + kolom di DB guild ini"""
        guild_id = ctx.guild.id
        schema = db.check_schema(guild_id)

        msg = "📖 **Schema DB untuk guild ini:**\n"
        for table, cols in schema.items():
            msg += f"**{table}**: {', '.join(cols)}\n"

        await ctx.send(msg[:1990])  # Biar aman dari limit Discord

    # ========================
    # 🗑️ Reset Tabel
    # ========================
    @db_group.command(name="resettable")
    @commands.has_permissions(administrator=True)
    async def resettable(self, ctx, *, table: str):
        """Hapus satu tabel lalu kosongkan"""
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
            fmt = fmt.lower()

            # === Ekspor ke berbagai format ===
            if fmt == "csv":
                df.to_csv(filename, index=False)
            elif fmt == "xlsx":
                df.to_excel(filename, index=False)
            elif fmt == "json":
                df.to_json(filename, orient="records", indent=2)
            elif fmt == "docx":
                from docx import Document

                doc = Document()
                doc.add_heading("Technonesia Item Catalog", level=1)

                for _, r in df.iterrows():
                    name = r.get("name", "?")
                    rarity = r.get("rarity", "?")
                    desc = r.get("desc", "")
                    doc.add_heading(f"{name} ({rarity})", level=2)
                    doc.add_paragraph(
                        f"Type: {r.get('type', '?')} | "
                        f"Value: {r.get('value', '?')} | "
                        f"Weight: {r.get('weight', '?')}"
                    )
                    if desc:
                        doc.add_paragraph(desc)
                    doc.add_paragraph("—")

                doc.save(filename)
            else:
                return await ctx.send(
                    "❌ Format tidak dikenal! Gunakan: csv / xlsx / docx / json."
                )

            await ctx.send(
                content=f"✅ Data item diekspor sebagai **{fmt.upper()}**",
                file=discord.File(filename),
            )

        except Exception as e:
            await ctx.send(f"❌ Gagal export item: {e}")


async def setup(bot):
    await bot.add_cog(DbAdmin(bot))
