import math
import random
import discord
from discord.ext import commands
from discord.ui import View, button
from discord import ButtonStyle

from utils.db import execute, fetchone, fetchall
from services import inventory_service  # dipakai untuk add_item hasil crafting

# ===========================
# THEME & HELPERS
# ===========================
THEME_COLOR = 0x00FFC6  # neon cyan Technonesia
ERROR_COLOR = 0xFF5A5A

ICONS = {
    "bp": "📘",
    "start": "⚙️",
    "prog": "🧩",
    "done": "✅",
    "fail": "❌",
}


def safe_field_value(text: str, limit: int = 1024) -> str:
    if text is None:
        return "-"
    txt = str(text)
    return txt if len(txt) <= limit else txt[: limit - 3] + "..."


def ensure_tables(guild_id: int):
    # Tabel blueprint global
    execute(
        guild_id,
        """
        CREATE TABLE IF NOT EXISTS blueprints (
            name TEXT PRIMARY KEY,
            desc TEXT,
            req TEXT,
            result TEXT,
            target_progress INTEGER DEFAULT 100
        )
        """,
    )
    # Tabel crafting aktif per player
    execute(
        guild_id,
        """
        CREATE TABLE IF NOT EXISTS crafting (
            player TEXT PRIMARY KEY,
            blueprint TEXT,
            progress INTEGER DEFAULT 0
        )
        """,
    )
    # Tabel pengetahuan blueprint per player
    execute(
        guild_id,
        """
        CREATE TABLE IF NOT EXISTS known_blueprints (
            player TEXT,
            blueprint TEXT,
            PRIMARY KEY (player, blueprint)
        )
        """,
    )


def format_req_pretty(req_str: str) -> str:
    """Ubah 'Item:2, Bahan:1' jadi bullet list cantik."""
    if not req_str:
        return "-"
    parts = [p.strip() for p in req_str.split(",") if p.strip()]
    lines = []
    for p in parts:
        if ":" in p:
            item, qty = [x.strip() for x in p.split(":", 1)]
            lines.append(f"• **{item}** ×{qty}")
        else:
            lines.append(f"• **{p}**")
    return "\n".join(lines) if lines else "-"


def build_bar(current: int, target: int, length: int = 20) -> tuple[str, int]:
    """Return (bar_str, percent_int)"""
    ratio = 0.0 if target <= 0 else min(current / target, 1.0)
    filled = int(ratio * length)
    bar = "▰" * filled + "▱" * (length - filled)
    percent = int(ratio * 100)
    return bar, percent


# ===========================
# PAGINATION VIEWS
# ===========================
class PagedEmbed(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0

    async def update(self, interaction: discord.Interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="◀", style=ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
            await self.update(interaction)
        else:
            await interaction.response.defer()

    @button(label="▶", style=ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
            await self.update(interaction)
        else:
            await interaction.response.defer()


# ===========================
# COG
# ===========================
class Crafting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------------------
    # ROOT
    # ---------------------------
    @commands.group(name="crafting", invoke_without_command=True)
    async def crafting_root(self, ctx: commands.Context):
        ensure_tables(ctx.guild.id)
        embed = discord.Embed(
            title=f"{ICONS['start']} Crafting System – Technonesia",
            description=(
                "**Blueprint:**\n"
                "`!crafting blueprint add <Nama> | <Desc> | <Bahan:qty, ...> | <Hasil> | <TargetProgress>`\n"
                "`!crafting blueprint list`\n"
                "`!crafting blueprint detail <Nama>`\n\n"
                "**Knowledge:**\n"
                "`!crafting learn <Player> <Blueprint>`\n"
                "`!crafting known <Player>`\n\n"
                "**Process:**\n"
                "`!crafting start <Player> <Blueprint>`\n"
                "`!crafting progress <Player> <+angka/-angka>`\n"
                "`!crafting show <Player>`\n"
                "`!crafting finish <Player>`\n"
                "`!crafting cancel <Player>`\n"
            ),
            color=THEME_COLOR,
        )
        embed.set_footer(text="Forge v3 – Manual GM roll, bar dinamis, auto-finish.")
        await ctx.send(embed=embed)

    # ---------------------------
    # BLUEPRINT MGMT
    # ---------------------------
    @crafting_root.group(name="blueprint")
    async def crafting_bp(self, ctx: commands.Context):
        ensure_tables(ctx.guild.id)

    @crafting_bp.command(name="add")
    async def bp_add(self, ctx: commands.Context, *, data: str):
        """
        Format:
        !crafting blueprint add <Nama> | <Deskripsi> | <Bahan:qty, Bahan:qty> | <Hasil> | <TargetProgress>
        """
        ensure_tables(ctx.guild.id)
        parts = [p.strip() for p in data.split("|")]
        if len(parts) < 5:
            return await ctx.send(
                "❌ Format salah.\n"
                "Gunakan: `!crafting blueprint add <Nama> | <Deskripsi> | <Bahan:qty, ...> | <Hasil> | <TargetProgress>`"
            )
        name, desc, req, result, tp = parts
        try:
            tp_int = int(tp)
            if tp_int <= 0:
                raise ValueError
        except Exception:
            return await ctx.send("❌ TargetProgress harus angka > 0.")

        execute(
            ctx.guild.id,
            """
            INSERT INTO blueprints (name, desc, req, result, target_progress)
            VALUES (?,?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET
                desc=excluded.desc,
                req=excluded.req,
                result=excluded.result,
                target_progress=excluded.target_progress
            """,
            (name, desc, req, result, tp_int),
        )

        embed = discord.Embed(
            title=f"{ICONS['bp']} Blueprint Ditambahkan",
            color=THEME_COLOR,
            description=f"**{name}**",
        )
        embed.add_field(name="🎯 Target Progress", value=str(tp_int), inline=True)
        embed.add_field(name="🎁 Hasil", value=result, inline=True)
        embed.add_field(name="📦 Bahan", value=format_req_pretty(req), inline=False)
        embed.add_field(name="💬 Deskripsi", value=safe_field_value(desc), inline=False)
        await ctx.send(embed=embed)

    @crafting_bp.command(name="list")
    async def bp_list(self, ctx: commands.Context):
        """List semua blueprint (paged)."""
        ensure_tables(ctx.guild.id)
        rows = fetchall(ctx.guild.id, "SELECT * FROM blueprints ORDER BY name ASC", ())
        if not rows:
            return await ctx.send("📭 Belum ada blueprint.")

        # build pages
        per_page = 8
        pages = []
        for i in range(0, len(rows), per_page):
            chunk = rows[i : i + per_page]
            embed = discord.Embed(
                title=f"{ICONS['bp']} Daftar Blueprint (Global)",
                color=THEME_COLOR,
                description="Gunakan `!crafting blueprint detail <Nama>` untuk rincian.",
            )
            for bp in chunk:
                embed.add_field(
                    name=f"🔹 {bp['name']}",
                    value=f"🎁 **{bp['result']}**  •  🎯 **{bp['target_progress']}**",
                    inline=False,
                )
            embed.set_footer(text=f"Page {i//per_page+1}/{math.ceil(len(rows)/per_page)}")
            pages.append(embed)

        view = PagedEmbed(pages)
        await ctx.send(embed=pages[0], view=view)

    @crafting_bp.command(name="detail")
    async def bp_detail(self, ctx: commands.Context, *, name: str):
        """Detail 1 blueprint (desc, bahan, hasil, target)."""
        ensure_tables(ctx.guild.id)
        bp = fetchone(ctx.guild.id, "SELECT * FROM blueprints WHERE name=?", (name,))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan.")

        embed = discord.Embed(
            title=f"{ICONS['bp']} Blueprint: {bp['name']}",
            color=THEME_COLOR,
        )
        embed.add_field(name="🎯 Target Progress", value=str(bp["target_progress"]), inline=True)
        embed.add_field(name="🎁 Hasil", value=bp["result"], inline=True)
        embed.add_field(name="📦 Bahan", value=format_req_pretty(bp["req"]), inline=False)
        if bp["desc"]:
            embed.add_field(name="💬 Deskripsi", value=safe_field_value(bp["desc"]), inline=False)
        await ctx.send(embed=embed)

    # ---------------------------
    # KNOWLEDGE
    # ---------------------------
    @crafting_root.command(name="learn")
    async def bp_learn(self, ctx: commands.Context, player: str, *, blueprint: str):
        """GM menandai player telah mempelajari blueprint tertentu."""
        ensure_tables(ctx.guild.id)
        bp = fetchone(ctx.guild.id, "SELECT name FROM blueprints WHERE name=?", (blueprint,))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan di database.")

        execute(
            ctx.guild.id,
            "INSERT OR IGNORE INTO known_blueprints (player, blueprint) VALUES (?,?)",
            (player, bp["name"]),
        )
        embed = discord.Embed(
            title="🧠 Blueprint Dipelajari",
            description=f"**{player}** kini mengetahui **{bp['name']}**.",
            color=THEME_COLOR,
        )
        embed.set_footer(text="Sinkronisasi neural database: OK")
        await ctx.send(embed=embed)

    @crafting_root.command(name="known")
    async def bp_known(self, ctx: commands.Context, player: str):
        """List blueprint yang diketahui player (paged)."""
        ensure_tables(ctx.guild.id)
        rows = fetchall(
            ctx.guild.id,
            "SELECT b.name, b.result, b.target_progress, b.desc FROM known_blueprints k "
            "JOIN blueprints b ON b.name = k.blueprint WHERE k.player=? ORDER BY b.name ASC",
            (player,),
        )
        if not rows:
            return await ctx.send(f"📭 **{player}** belum mengetahui blueprint apa pun.")

        per_page = 8
        pages = []
        for i in range(0, len(rows), per_page):
            chunk = rows[i : i + per_page]
            embed = discord.Embed(
                title=f"📘 Blueprint Dikenal – {player}",
                color=THEME_COLOR,
                description="*(Sinkronisasi Neural Database: OK)*",
            )
            for bp in chunk:
                desc = f"\n*{safe_field_value(bp['desc'], 120)}*" if bp["desc"] else ""
                embed.add_field(
                    name=f"🔹 {bp['name']}",
                    value=f"🎁 **{bp['result']}**  •  🎯 **{bp['target_progress']}**{desc}",
                    inline=False,
                )
            embed.set_footer(text=f"Page {i//per_page+1}/{math.ceil(len(rows)/per_page)}")
            pages.append(embed)

        view = PagedEmbed(pages)
        await ctx.send(embed=pages[0], view=view)

    # ---------------------------
    # PROCESS
    # ---------------------------
    @crafting_root.command(name="start")
    async def craft_start(self, ctx: commands.Context, player: str, *, blueprint: str):
        """
        Mulai crafting:
        - Hanya boleh untuk blueprint yang telah dipelajari (locked mode)
        - Cek 'stat crafting' (jika tidak ada -> gagal)
        - Cek & kurangi bahan dari inventory
        """
        ensure_tables(ctx.guild.id)
        guild_id = ctx.guild.id

        # Locked mode: harus sudah learn
        known = fetchone(
            guild_id,
            "SELECT 1 FROM known_blueprints WHERE player=? AND blueprint=?",
            (player, blueprint),
        )
        if not known:
            embed = discord.Embed(
                title=f"{ICONS['fail']} Gagal Crafting",
                description=f"**{player}** belum mempelajari blueprint **{blueprint}**.",
                color=ERROR_COLOR,
            )
            embed.set_footer(text="Dapatkan blueprint dari loot/NPC/quest.")
            return await ctx.send(embed=embed)

        # Ambil blueprint
        bp = fetchone(guild_id, "SELECT * FROM blueprints WHERE name=?", (blueprint,))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan.")

        # Cek 'stat crafting' (opsional, fail kalau tidak ada)
        # Kita coba baca dari table characters.crafting_lvl; jika tidak ada table/kolom → dianggap gagal.
        has_craft_stat = False
        try:
            row_stat = fetchone(
                guild_id,
                "SELECT crafting_lvl FROM characters WHERE name=?",
                (player,),
            )
            if row_stat and (row_stat["crafting_lvl"] is not None) and int(row_stat["crafting_lvl"]) >= 0:
                has_craft_stat = True
        except Exception:
            has_craft_stat = False

        if not has_craft_stat:
            embed = discord.Embed(
                title=f"{ICONS['fail']} Gagal Crafting",
                description=(
                    f"**{player}** tidak memiliki **stat crafting** yang valid.\n"
                    "Mohon set `crafting_lvl` karakter dahulu."
                ),
                color=ERROR_COLOR,
            )
            return await ctx.send(embed=embed)

        # Cek bahan
        missing = []
        req_str = bp["req"] or ""
        parts = [p.strip() for p in req_str.split(",") if p.strip()]
        for p in parts:
            if ":" in p:
                item, qty = [x.strip() for x in p.split(":", 1)]
                try:
                    need = int(qty)
                except Exception:
                    need = 1
            else:
                item, need = p, 1

            have = inventory_service.get_qty(guild_id, player, item)
            if have < need:
                missing.append(f"{item} ({have}/{need})")

        if missing:
            embed = discord.Embed(
                title=f"{ICONS['fail']} Gagal Crafting",
                description="Bahan kurang:",
                color=ERROR_COLOR,
            )
            embed.add_field(name="📦 Kekurangan", value="\n".join(missing), inline=False)
            return await ctx.send(embed=embed)

        # Kurangi bahan
        for p in parts:
            if ":" in p:
                item, qty = [x.strip() for x in p.split(":", 1)]
                need = int(qty) if qty.isdigit() else 1
            else:
                item, need = p, 1
            inventory_service.remove_item(guild_id, player, item, need)

        # Set crafting aktif progress=0
        execute(
            guild_id,
            "INSERT OR REPLACE INTO crafting (player, blueprint, progress) VALUES (?,?,0)",
            (player, bp["name"]),
        )

        embed = discord.Embed(
            title=f"{ICONS['start']} Crafting Dimulai",
            description=f"**{player}** memulai pembuatan **{bp['result']}**.",
            color=THEME_COLOR,
        )
        embed.add_field(name="🧪 Blueprint", value=bp["name"], inline=True)
        embed.add_field(name="🎯 Target", value=str(bp["target_progress"]), inline=True)
        embed.add_field(name="⚙️ Progress", value="[▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱] 0%", inline=False)
        embed.set_footer(text="Update progress pakai hasil roll GM.")
        await ctx.send(embed=embed)

    @crafting_root.command(name="progress")
    async def craft_progress(self, ctx: commands.Context, player: str, value: int):
        """
        Update progress manual (GM input dari hasil roll).
        Contoh: !crafting progress Rain +72
        """
        ensure_tables(ctx.guild.id)
        guild_id = ctx.guild.id

        row = fetchone(guild_id, "SELECT * FROM crafting WHERE player=?", (player,))
        if not row:
            return await ctx.send("❌ Tidak ada crafting aktif untuk player ini.")

        bp = fetchone(guild_id, "SELECT * FROM blueprints WHERE name=?", (row["blueprint"],))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan.")

        old = int(row["progress"])
        new = max(0, old + int(value))
        execute(guild_id, "UPDATE crafting SET progress=? WHERE player=?", (new, player))

        bar, pct = build_bar(new, int(bp["target_progress"]))
        embed = discord.Embed(
            title=f"{ICONS['prog']} Forge Progress – {player}",
            description="_Update manual berdasarkan hasil roll GM._",
            color=THEME_COLOR,
        )
        embed.add_field(name="Blueprint", value=row["blueprint"], inline=False)
        embed.add_field(name="🎯 Target", value=str(bp["target_progress"]), inline=True)
        embed.add_field(name="⚙️ Progress", value=f"[{bar}] {new}/{bp['target_progress']} ({pct}%)", inline=False)
        await ctx.send(embed=embed)

        # Auto-finish
        if new >= int(bp["target_progress"]):
            await self._auto_finish(ctx, player, row["blueprint"])

    @crafting_root.command(name="show")
    async def craft_show(self, ctx: commands.Context, player: str):
        """Tampilkan bar: nama, target, progress (minimalis)."""
        ensure_tables(ctx.guild.id)
        guild_id = ctx.guild.id

        row = fetchone(guild_id, "SELECT * FROM crafting WHERE player=?", (player,))
        if not row:
            return await ctx.send("❌ Tidak ada crafting aktif.")

        bp = fetchone(guild_id, "SELECT * FROM blueprints WHERE name=?", (row["blueprint"],))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan.")

        bar, pct = build_bar(int(row["progress"]), int(bp["target_progress"]))
        embed = discord.Embed(title=f"🧩 Crafting Progress – {player}", color=THEME_COLOR)
        embed.add_field(name="Blueprint", value=row["blueprint"], inline=False)
        embed.add_field(name="🎯 Target", value=str(bp["target_progress"]), inline=True)
        embed.add_field(
            name="⚙️ Progress",
            value=f"[{bar}] {row['progress']}/{bp['target_progress']} ({pct}%)",
            inline=False,
        )
        embed.set_footer(text="Progress di-update manual oleh GM dari hasil roll.")
        await ctx.send(embed=embed)

    @crafting_root.command(name="finish")
    async def craft_finish(self, ctx: commands.Context, player: str):
        """Selesaikan crafting bila progress sudah cukup (dipanggil otomatis)."""
        ensure_tables(ctx.guild.id)
        guild_id = ctx.guild.id

        row = fetchone(guild_id, "SELECT * FROM crafting WHERE player=?", (player,))
        if not row:
            return await ctx.send("❌ Tidak ada crafting aktif.")
        bp = fetchone(guild_id, "SELECT result, target_progress FROM blueprints WHERE name=?", (row["blueprint"],))
        if not bp:
            return await ctx.send("❌ Blueprint tidak ditemukan.")
        if int(row["progress"]) < int(bp["target_progress"]):
            return await ctx.send("⚠️ Belum selesai. Progress belum mencapai target.")

        # Tambahkan item ke inventory & hapus crafting
        inventory_service.add_item(guild_id, player, bp["result"], 1)
        execute(guild_id, "DELETE FROM crafting WHERE player=?", (player,))

        embed = discord.Embed(
            title=f"{ICONS['done']} Crafting Selesai!",
            description=f"**{player}** berhasil menyelesaikan **{bp['result']}**.\nBarang telah ditambahkan ke inventory.",
            color=THEME_COLOR,
        )
        await ctx.send(embed=embed)

    @crafting_root.command(name="cancel")
    async def craft_cancel(self, ctx: commands.Context, player: str):
        """Batalkan crafting aktif (bahan tidak dikembalikan)."""
        ensure_tables(ctx.guild.id)
        execute(ctx.guild.id, "DELETE FROM crafting WHERE player=?", (player,))
        embed = discord.Embed(
            title=f"{ICONS['fail']} Crafting Dibatalkan",
            description=f"Proses crafting milik **{player}** dibatalkan.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="Catatan: Bahan tidak dikembalikan.")
        await ctx.send(embed=embed)

    # ---------------------------
    # INTERNAL
    # ---------------------------
    async def _auto_finish(self, ctx: commands.Context, player: str, blueprint_name: str):
        """Dipanggil otomatis saat progress >= target."""
        guild_id = ctx.guild.id
        bp = fetchone(guild_id, "SELECT result FROM blueprints WHERE name=?", (blueprint_name,))
        if not bp:
            return await ctx.send("⚠️ Blueprint rusak atau tidak lengkap.")
        inventory_service.add_item(guild_id, player, bp["result"], 1)
        execute(guild_id, "DELETE FROM crafting WHERE player=?", (player,))

        embed = discord.Embed(
            title=f"{ICONS['done']} Crafting Selesai!",
            description=f"**{player}** berhasil menyelesaikan **{bp['result']}**.\nBarang telah ditambahkan ke inventory.",
            color=THEME_COLOR,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Crafting(bot))
