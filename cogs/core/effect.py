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
            title="📘 Effect / Buff-Debuff Commands",
            description=(
                "**Library (GM)**\n"
                "`!effect add <name> <type> <target_stat> <formula> <duration> <stack_mode> \"<desc>\" [max_stack]`\n"
                "`!effect edit <name> <field> <value>` → ubah satu field\n"
                "`!effect editfield <name> field=value ...` → ubah beberapa field\n"
                "`!effect list` → lihat semua efek\n"
                "`!effect info <name>` → lihat detail efek\n"
                "`!effect remove <name>` → hapus dari library\n\n"
                "**Active & Apply**\n"
                "`!apply <Target> <EffectName> [DurationOverride]` → apply dari library\n"
                "`!effect active <Target>` → daftar efek aktif target\n\n"
                "**Cleanup & Tick**\n"
                "`!effect clear <Target>` → hapus semua efek\n"
                "`!effect clearbuff <Target>` → hanya buff\n"
                "`!effect cleardebuff <Target>` → hanya debuff\n"
                "`!tick` → kurangi durasi semua efek aktif"
            ),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    # === ADD EFFECT ===
    @effect_group.command(name="add")
    async def effect_add(self, ctx, name: str, e_type: str, target_stat: str, formula: str,
                         duration: int, stack_mode: str, *, desc_and_stack: str = ""):
        """Tambah atau perbarui efek dalam library."""
        try:
            desc = desc_and_stack.strip()
            max_stack = None

            # Cek apakah ada angka terakhir sebagai max_stack
            parts = desc_and_stack.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit():
                desc = parts[0].strip()
                max_stack = int(parts[1])

            # Bersihkan tanda kutip
            if desc.startswith('"') and desc.endswith('"'):
                desc = desc[1:-1]
            elif desc.startswith("'") and desc.endswith("'"):
                desc = desc[1:-1]

            effect_service.add_effect_lib(
                ctx.guild.id, name, e_type, target_stat, formula,
                duration, stack_mode, desc, max_stack
            )

            msg = f"✅ Efek **{name}** ditambahkan/diupdate."
            if desc:
                msg += f"\n🛈 Deskripsi: {desc}"
            await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Gagal menambah efek: {e}")

    # === EDIT (SINGLE FIELD) ===
    @effect_group.command(name="edit")
    async def effect_edit_single(self, ctx, name: str, field: str, *, value: str):
        """Edit satu field dari efek (misal desc, formula, duration)."""
        try:
            ok = effect_service.update_effect_field(ctx.guild.id, name, field, value)
            if not ok:
                return await ctx.send(f"❌ Efek **{name}** tidak ditemukan atau field tidak valid.")
            await ctx.send(f"✅ Efek **{name}** diperbarui: **{field}** → `{value}`")
        except Exception as e:
            await ctx.send(f"⚠️ Gagal mengedit efek: {e}")

    # === EDIT (MULTI FIELD) ===
    @effect_group.command(name="editfield")
    async def effect_editfield(self, ctx, name: str, *fields):
        """
        Edit beberapa field sekaligus.
        Contoh:
        !effect editfield poison desc="Racun berat" duration=4 formula=-2
        """
        try:
            current = effect_service.get_effect_lib(ctx.guild.id, name)
            if not current:
                return await ctx.send(f"❌ Efek **{name}** tidak ditemukan di library.")

            allowed = ["type", "target_stat", "formula", "duration", "stack_mode", "description", "max_stack"]
            changes = {}
            for f in fields:
                if "=" not in f:
                    continue
                k, v = f.split("=", 1)
                k = k.strip().lower()
                v = v.strip().strip('"').strip("'")
                if k in allowed:
                    if k in ["duration", "max_stack"] and v.isdigit():
                        v = int(v)
                    changes[k] = v

            if not changes:
                return await ctx.send("⚠️ Tidak ada field valid untuk diubah.")

            before_preview = "\n".join([f"{k}: {current.get(k)}" for k in changes.keys()])
            for k, v in changes.items():
                current[k] = v
            after_preview = "\n".join([f"{k}: {current.get(k)}" for k in changes.keys()])

            effect_service.add_effect_lib(
                ctx.guild.id,
                name,
                current["type"],
                current["target_stat"],
                current["formula"],
                current["duration"],
                current["stack_mode"],
                current.get("description", ""),
                current.get("max_stack")
            )

            embed = discord.Embed(
                title=f"✏️ Efek '{name}' diperbarui",
                description=(
                    f"**Sebelum:**\n```{before_preview}```\n"
                    f"**Sesudah:**\n```{after_preview}```"
                ),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Gagal mengedit efek: {e}")

    # === LIST ===
    @effect_group.command(name="list")
    async def effect_list(self, ctx):
        rows = effect_service.list_effects_lib(ctx.guild.id)
        if not rows:
            return await ctx.send("ℹ️ Library efek kosong. Tambahkan dengan `!effect add`.")
        lines = []
        for r in rows:
            desc = f"\n   🛈 {r['description']}" if r.get("description") else ""
            lines.append(
                f"• **{r['name']}** — {r['type']}, stat: {r['target_stat']}, "
                f"formula: `{r['formula']}`, dur: {r['duration']}, mode: {r['stack_mode']}{desc}"
            )
        embed = discord.Embed(
            title="📚 Effect Library",
            description="\n\n".join(lines),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # === INFO ===
    @effect_group.command(name="info")
    async def effect_info(self, ctx, name: str):
        r = effect_service.get_effect_lib(ctx.guild.id, name)
        if not r:
            return await ctx.send(f"❌ Efek **{name}** tidak ditemukan.")
        desc = (
            f"**Name**: {r['name']}\n"
            f"**Type**: {r['type']}\n"
            f"**Target Stat**: {r['target_stat']}\n"
            f"**Formula**: `{r['formula']}`\n"
            f"**Duration**: {r['duration']}\n"
            f"**Stack Mode**: {r['stack_mode']} (max {r.get('max_stack',1)})\n"
            f"**Desc**: {r.get('description','-')}"
        )
        embed = discord.Embed(title=f"ℹ️ Effect Info — {r['name']}", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    # === REMOVE ===
    @effect_group.command(name="remove")
    async def effect_remove(self, ctx, name: str):
        ok = effect_service.remove_effect_lib(ctx.guild.id, name)
        if not ok:
            return await ctx.send(f"❌ Efek **{name}** tidak ditemukan.")
        await ctx.send(f"🗑️ Efek **{name}** dihapus dari library.")

    # === ACTIVE EFFECTS ===
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
            desc = e.get("description", "-")
            line = (
                f"• **{e.get('text','')}** {'Lv'+str(stack) if stack>1 else ''}\n"
                f"   ⏳ Durasi: {dur_txt} turn\n"
                f"   🛈 {desc}"
            )
            lines.append(line)
        embed = discord.Embed(
            title=f"🧷 Active Effects — {target_name}",
            description="\n\n".join(lines),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    # === CLEAR ===
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
        ok, msg = await effect_service.apply_effect(ctx.guild.id, target_name, effect_name, duration_override)
        await ctx.send(msg)

    @commands.command(name="tick")
    async def tick(self, ctx):
        results = await effect_service.tick_effects(ctx.guild.id)
        engaged_names = []
        row = fetchone(ctx.guild.id, "SELECT order_json FROM initiative LIMIT 1")
        if row:
            try:
                engaged_names = [n for n, _ in json.loads(row["order_json"] or "[]")]
            except Exception:
                pass

        embed = discord.Embed(
            title="⏳ Tick Round Effects",
            description=(
                "🔹 **Proses Tick Ronde**\n"
                "Kurangi durasi efek aktif setiap ronde baru.\n\n"
                "🎲 Hanya peserta **yang sedang engage** akan ditampilkan.\n"
                f"📜 Server: **{ctx.guild.name}**\n"
                f"👥 Total peserta aktif: **{len(engaged_names)}**"
            ),
            color=discord.Color.from_rgb(255, 190, 90)
        )

        any_data = False
        for ttype, table_name, icon in [("char","Characters","🧍"),("enemy","Enemies","👹"),("ally","Allies","🤝")]:
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
                    desc = e.get("description") or "-"
                    line = f"🔹 **{e.get('text','')}** *(sisa {d} turn)*\n{desc}"
                    active_lines.append(line)
                expired_lines = [f"• ~~{e.get('text','')}~~" for e in expired]
                block = f"**{name}**\n" + "\n".join(active_lines)
                if expired_lines:
                    block += "\n\n⌛ **Expired:**\n" + "\n".join(expired_lines)
                lines.append(block)
            if lines:
                embed.add_field(name=f"\n{icon} {table_name}", value="\n\n".join(lines), inline=False)

        if not any_data:
            embed.add_field(name="✅ Semua Efek Telah Berakhir",
                            value="Tidak ada efek aktif maupun expired pada peserta engage.", inline=False)
        embed.set_footer(text="Gunakan !tick setiap ronde untuk memperbarui efek dan durasinya.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EffectCog(bot))
