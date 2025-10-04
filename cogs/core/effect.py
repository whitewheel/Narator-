# cogs/core/effect.py
import json
import discord
from discord.ext import commands
from utils.db import fetchone
from services import effect_service

class EffectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # LIBRARY COMMANDS (GM)
    # =========================
    @commands.group(name="effect", invoke_without_command=True)
    async def effect_group(self, ctx):
        embed = discord.Embed(
            title="📚 Effect Library Commands",
            description=(
                "• `!effect add <name> <type> <target_stat> <formula> <duration> <stack_mode> \"<desc>\" [max_stack]`\n"
                "• `!effect list`\n"
                "• `!effect info <name>`\n"
                "• `!effect remove <name>`\n"
                "• `!effect active <target_name>`\n"
                "• `!effect clear <target_name>` (hapus semua)\n"
                "• `!effect clearbuff <target_name>` / `!effect cleardebuff <target_name>`\n\n"
                "Apply ke target: `!apply <target_name> <effect_name>`\n"
                "Tick ronde: `!tick` (laporan saja, tanpa auto damage, hanya peserta engage)"
            ),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @effect_group.command(name="add")
    async def effect_add(self, ctx, name: str, e_type: str, target_stat: str, formula: str,
                         duration: int, stack_mode: str, desc: str, max_stack: int = None):
        """Tambah/replace entry di library efek DB."""
        try:
            effect_service.add_effect_lib(
                ctx.guild.id, name, e_type, target_stat, formula, duration, stack_mode, desc, max_stack
            )
            await ctx.send(f"✅ Efek **{name}** ditambahkan/diupdate.")
        except Exception as e:
            await ctx.send(f"❌ Gagal menambah efek: {e}")

    @effect_group.command(name="list")
    async def effect_list(self, ctx):
        rows = effect_service.list_effects_lib(ctx.guild.id)
        if not rows:
            return await ctx.send("ℹ️ Library efek kosong. Tambahkan dengan `!effect add`.")
        lines = []
        for r in rows:
            lines.append(
                f"• **{r['name']}** — {r['type']}, stat: {r['target_stat']}, "
                f"formula: `{r['formula']}`, dur: {r['duration']}, mode: {r['stack_mode']}"
            )
        embed = discord.Embed(
            title="📚 Effect Library",
            description="\n".join(lines),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @effect_group.command(name="info")
    async def effect_info(self, ctx, name: str):
        r = effect_service.get_effect_lib(ctx.guild.id, name)
        if not r:
            return await ctx.send(f"❌ Efek **{name}** tidak ada.")
        desc = (
            f"**Name**: {r['name']}\n"
            f"**Type**: {r['type']}\n"
            f"**Target Stat**: {r['target_stat']}\n"
            f"**Formula**: `{r['formula']}`\n"
            f"**Duration**: {r['duration']}\n"
            f"**Stack Mode**: {r['stack_mode']} (max {r.get('max_stack',1)})\n"
            f"**Desc**: {r.get('description','-')}"
        )
        embed = discord.Embed(title="ℹ️ Effect Info", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @effect_group.command(name="remove")
    async def effect_remove(self, ctx, name: str):
        ok = effect_service.remove_effect_lib(ctx.guild.id, name)
        if not ok:
            return await ctx.send(f"❌ Efek **{name}** tidak ditemukan.")
        await ctx.send(f"🗑️ Efek **{name}** dihapus dari library.")

    @effect_group.command(name="active")
    async def effect_active(self, ctx, *, target_name: str):
        ok, table, effs = effect_service.get_active_effects(ctx.guild.id, target_name)
        if not ok:
            return await ctx.send(table)
        if not effs:
            return await ctx.send(f"ℹ️ **{target_name}** tidak memiliki efek aktif.")
        lines = []
        for e in effs:
            dur = e.get("duration", -1)
            dur_txt = f"{dur}" if dur >= 0 else "∞"
            stack = e.get("stack", 1)
            form = e.get("formula", "")
            desc = e.get("description", "-")
            line = (
                f"• **{e.get('text','')}** {'Lv'+str(stack) if stack>1 else ''}\n"
                f"   ┗ `{form}` [Durasi: {dur_txt}]\n"
                f"   🛈 {desc}"
            )
            lines.append(line)
        embed = discord.Embed(
            title=f"🧷 Active Effects: {target_name}",
            description="\n".join(lines),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @effect_group.command(name="clear")
    async def effect_clear(self, ctx, *, target_name: str):
        ok, msg = await effect_service.clear_effects(ctx.guild.id, target_name)
        await ctx.send(msg)

    @effect_group.command(name="clearbuff")
    async def effect_clearbuff(self, ctx, *, target_name: str):
        ok, msg = await effect_service.clear_effects(ctx.guild.id, target_name, is_buff=True)
        await ctx.send(msg)

    @effect_group.command(name="cleardebuff")
    async def effect_cleardebuff(self, ctx, *, target_name: str):
        ok, msg = await effect_service.clear_effects(ctx.guild.id, target_name, is_buff=False)
        await ctx.send(msg)

    # =========================
    # APPLY & TICK
    # =========================
    @commands.command(name="apply")
    async def apply(self, ctx, target_name: str, effect_name: str, duration_override: int = None):
        """Apply efek dari LIBRARY ke target. Tidak mengubah HP/dll (manual GM mode)."""
        ok, msg = await effect_service.apply_effect(
            ctx.guild.id, target_name, effect_name, duration_override
        )
        await ctx.send(msg)

    @commands.command(name="tick")
    async def tick(self, ctx):
        """Kurangi durasi semua efek & tampilkan laporan.
        Hanya menampilkan peserta yang sedang engage (ada di initiative)."""
        results = await effect_service.tick_effects(ctx.guild.id)

        # Ambil daftar peserta engage dari tabel initiative
        engaged_names = []
        row = fetchone(ctx.guild.id, "SELECT order_json FROM initiative LIMIT 1")
        if row:
            try:
                engaged_names = [n for n, _ in json.loads(row["order_json"] or "[]")]
            except Exception:
                pass

        # Header utama
        embed = discord.Embed(
            title="⏳ Tick Round Effects",
            description=(
                "🔹 **Proses Tick Ronde**\n"
                "Gunakan perintah ini setiap kali ronde baru dimulai untuk "
                "mengurangi **durasi semua efek aktif (buff/debuff)**.\n\n"
                "🎲 Hanya peserta yang **terlibat dalam encounter (initiative)** yang akan ditampilkan.\n"
                f"📜 Server: **{ctx.guild.name}**\n"
                f"👥 Total peserta aktif: **{len(engaged_names)}**"
            ),
            color=discord.Color.from_rgb(255, 190, 90)
        )

        any_data = False

        for ttype, table_name, icon in [
            ("char", "Characters", "🧍"),
            ("enemy", "Enemies", "👹"),
            ("ally", "Allies", "🤝"),
        ]:
            data = results.get(ttype) or {}
            lines = []

            for name, info in data.items():
                if name not in engaged_names:
                    continue

                active = info.get("active", [])
                expired = info.get("expired", [])

                if not active and not expired:
                    continue

                any_data = True

                active_lines = []
                for e in active:
                    d = e.get("duration", -1)
                    formula = e.get("formula", "")
                    stack = e.get("stack", 1)
                    stack_txt = f" Lv{stack}" if stack > 1 else ""
                    desc = e.get("description") or "-"
                    line = (
                        f"🔹 **{e.get('text','')}**{stack_txt}\n"
                        f"   ┗ `{formula}` *(sisa {d} turn)*\n"
                        f"   🛈 {desc}"
                    )
                    active_lines.append(line)

                if not active_lines:
                    active_lines = ["• *(tidak ada efek aktif)*"]

                expired_lines = [f"• ~~{e.get('text','')}~~" for e in expired]

                block = f"**{name}**\n" + "\n".join(active_lines)
                if expired_lines:
                    block += "\n\n⌛ **Expired:**\n" + "\n".join(expired_lines)
                lines.append(block)

            if lines:
                embed.add_field(
                    name=f"\n{icon} {table_name}",
                    value="\n\n".join(lines),
                    inline=False
                )

        if not any_data:
            embed.add_field(
                name="✅ Semua Efek Telah Berakhir",
                value="Tidak ada efek aktif maupun expired pada peserta yang sedang engage.",
                inline=False
            )

        embed.set_footer(text="Gunakan !tick setiap ronde untuk memperbarui efek dan durasinya.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EffectCog(bot))
