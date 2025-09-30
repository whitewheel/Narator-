import discord
from discord.ext import commands
from services import skill_service

CATEGORY_EMOJI = {
    "Basic": "📘",
    "Racial": "🧬",
    "Learning": "📖",
    "Augment": "⚙️",
    "Item": "🗡️",
}

class Skill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="skill", invoke_without_command=True)
    async def skill(self, ctx):
        await ctx.send(
            "Gunakan: Player → `!skill show/use` | "
            "GM → `!skill add/remove/reset/gmglobal` | "
            "Library → `!skill library add/list/info/remove/update`"
        )

    # ===== PLAYER COMMANDS =====
    @skill.command(name="show")
    async def skill_show(self, ctx, char_name: str):
        rows = skill_service.get_char_skills(ctx.guild.id, char_name)
        if not rows:
            await ctx.send(f"❌ {char_name} belum punya skill.")
            return

        embed = discord.Embed(title=f"📜 Skill – {char_name}", color=discord.Color.teal())
        categories = {}
        for row in rows:
            categories.setdefault(row["category"], []).append(
                f"- {row['name']} (Lv {row['level']})"
            )
        for cat, skills in categories.items():
            emoji = CATEGORY_EMOJI.get(cat, "✨")
            embed.add_field(name=f"{emoji} {cat}", value="\n".join(skills), inline=False)

        await ctx.send(embed=embed)

    @skill.command(name="use")
    async def skill_use(self, ctx, char_name: str, *, skill_name: str):
        row = skill_service.use_skill(ctx.guild.id, char_name, skill_name)
        if not row:
            await ctx.send(f"❌ {char_name} tidak punya skill {skill_name}.")
            return

        emoji = CATEGORY_EMOJI.get(row["category"], "✨")
        embed = discord.Embed(
            title=f"{emoji} {char_name} menggunakan {row['name']}!",
            color=discord.Color.orange()
        )
        embed.add_field(name="Efek", value=row["effect"], inline=False)
        embed.add_field(name="Drawback", value=row["drawback"], inline=False)
        embed.add_field(name="Cost", value=row["cost"], inline=False)
        await ctx.send(embed=embed)

    # ===== GM COMMANDS =====
    @skill.command(name="add")
    async def skill_add(self, ctx, char_name: str, skill_id: int, level: int = 1):
        msg = skill_service.add_skill(ctx.guild.id, char_name, skill_id, level)
        await ctx.send(msg)

    @skill.command(name="remove")
    async def skill_remove(self, ctx, char_name: str, *, skill_name: str):
        msg = skill_service.remove_skill(ctx.guild.id, char_name, skill_name)
        await ctx.send(msg)

    @skill.command(name="reset")
    async def skill_reset(self, ctx, char_name: str):
        msg = skill_service.reset_skills(ctx.guild.id, char_name)
        await ctx.send(msg)

    @skill.command(name="gmglobal")
    async def skill_gmglobal(self, ctx):
        rows = skill_service.get_all_skills(ctx.guild.id)
        if not rows:
            await ctx.send("📂 Belum ada skill yang tercatat di database guild ini.")
            return

        embed = discord.Embed(title="🌐 Daftar Global Skill (Server)", color=discord.Color.purple())
        for row in rows:
            emoji = CATEGORY_EMOJI.get(row["category"], "✨")
            embed.add_field(
                name=f"{row['char_name']} — {emoji} {row['category']}",
                value=f"{row['name']} (Lv {row['level']})",
                inline=False
            )
        await ctx.send(embed=embed)

    # ===== LIBRARY COMMANDS =====
    @skill.group(name="library")
    async def skill_library(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Gunakan: `!skill library add/list/info/remove/update`")

    @skill_library.command(name="add")
    async def skill_library_add(self, ctx, category: str, name: str, effect: str, drawback: str, cost: str):
        msg = skill_service.add_library(ctx.guild.id, category, name, effect, drawback, cost)
        await ctx.send(msg)

    @skill_library.command(name="list")
    async def skill_library_list(self, ctx):
        rows = skill_service.list_library(ctx.guild.id)
        if not rows:
            await ctx.send("❌ Belum ada skill di library.")
            return

        embed = discord.Embed(title="📚 Skill Library", color=discord.Color.blue())
        for row in rows:
            emoji = CATEGORY_EMOJI.get(row["category"], "✨")
            embed.add_field(
                name=f"{row['id']}. {emoji} {row['name']}",
                value=f"Kategori: {row['category']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @skill_library.command(name="info")
    async def skill_library_info(self, ctx, skill_id: int):
        row = skill_service.get_library_info(ctx.guild.id, skill_id)
        if not row:
            await ctx.send("❌ Skill tidak ditemukan di library.")
            return

        emoji = CATEGORY_EMOJI.get(row["category"], "✨")
        embed = discord.Embed(title=f"{emoji} {row['name']}", color=discord.Color.green())
        embed.add_field(name="Kategori", value=row["category"], inline=False)
        embed.add_field(name="Efek", value=row["effect"], inline=False)
        embed.add_field(name="Drawback", value=row["drawback"], inline=False)
        embed.add_field(name="Cost", value=row["cost"], inline=False)
        await ctx.send(embed=embed)

    @skill_library.command(name="remove")
    async def skill_library_remove(self, ctx, skill_id: int):
        msg = skill_service.remove_library(ctx.guild.id, skill_id)
        await ctx.send(msg)

    @skill_library.command(name="update")
    async def skill_library_update(self, ctx, skill_id: int, effect: str, drawback: str, cost: str):
        msg = skill_service.update_library(ctx.guild.id, skill_id, effect, drawback, cost)
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Skill(bot))
