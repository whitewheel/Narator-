import discord
from discord.ext import commands

# Import embed builders dari help.py
from .help import (
    embed_overview, embed_init, embed_status, embed_enemy,
    embed_dice, embed_quick, embed_poll, embed_gpt,
    embed_quest, embed_item, embed_loot, embed_npc,
    embed_favor, embed_scene, embed_timeline, embed_wiki,
    embed_classrace
)

# Mapping kategori -> embed function
EMBED_MAP = {
    "overview": embed_overview,
    "init": embed_init,
    "status": embed_status,
    "enemy": embed_enemy,
    "dice": embed_dice,
    "quick": embed_quick,
    "poll": embed_poll,
    "gpt": embed_gpt,
    "quest": embed_quest,
    "item": embed_item,
    "loot": embed_loot,
    "npc": embed_npc,
    "favor": embed_favor,
    "scene": embed_scene,
    "timeline": embed_timeline,
    "wiki": embed_wiki,
    "classrace": embed_classrace,
}

# List opsi dropdown (label, value)
OPTIONS = [
    ("🧍 Status", "status"),
    ("👹 Enemy", "enemy"),
    ("⚔️ Init", "init"),
    ("🎲 Dice", "dice"),
    ("⚡ Quick", "quick"),
    ("📜 Quest", "quest"),
    ("🧰 Item", "item"),
    ("🎁 Loot", "loot"),
    ("👤 NPC", "npc"),
    ("🪙 Favor", "favor"),
    ("📍 Scene", "scene"),
    ("⏳ Timeline", "timeline"),
    ("📚 Wiki", "wiki"),
    ("🧑‍🎓 Class & Race", "classrace"),
    ("📊 Poll", "poll"),
    ("🧠 GPT", "gpt"),
    ("📖 Overview", "overview"),
]

def _get_embed(prefix: str, key: str) -> discord.Embed:
    """Ambil embed sesuai kategori (default: overview)."""
    key = (key or "overview").lower()
    fn = EMBED_MAP.get(key, embed_overview)
    return fn(prefix)

# ==================== UI Components ====================

class HelpSelect(discord.ui.Select):
    def __init__(self, prefix: str, current: str = "overview"):
        self.prefix = prefix
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                default=(value == current),
                emoji=label.split()[0]  # ambil emoji pertama
            )
            for (label, value) in OPTIONS
        ]
        super().__init__(
            placeholder="📖 Pilih kategori bantuan…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_select",
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        embed = _get_embed(self.prefix, value)
        # Reset default pilihan dropdown
        for opt in self.options:
            opt.default = (opt.value == value)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, prefix: str, current: str = "overview", timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.prefix = prefix
        self.current = current
        self.message: discord.Message | None = None
        # Tambahkan dropdown ke view
        self.add_item(HelpSelect(prefix=self.prefix, current=current))

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        # Disable view saat timeout
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.secondary, custom_id="help_overview")
    async def to_overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _get_embed(self.prefix, "overview")
        # Reset dropdown ke overview
        for child in self.children:
            if isinstance(child, HelpSelect):
                for opt in child.options:
                    opt.default = (opt.value == "overview")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="help_close")
    async def on_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except Exception:
            # Fallback: disable view kalau gagal hapus pesan
            for child in self.children:
                if hasattr(child, "disabled"):
                    child.disabled = True
            await interaction.response.edit_message(content="(help ditutup)", view=self)

# ==================== Cog ====================

class HelpUICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help_ui")
    async def help_ui(self, ctx: commands.Context, topic: str | None = None):
        """
        Bantuan interaktif dengan dropdown menu.
        Opsional: !help_ui <topik> langsung buka embed kategori itu.
        """
        prefix = ctx.prefix or "!"
        key = (topic or "overview").lower()
        embed = _get_embed(prefix, key if key in EMBED_MAP else "overview")
        view = HelpView(prefix=prefix, current=(key if key in EMBED_MAP else "overview"))
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg  # simpan message untuk cleanup saat timeout

async def setup(bot: commands.Bot):
    bot.help_command = None
    try:
        bot.remove_command("help")
    except Exception:
        pass
    await bot.add_cog(HelpUICog(bot))
