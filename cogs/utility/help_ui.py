
import discord
from discord.ext import commands

# Import embed builders from help.py (desain/ikon tetap)
from .help import (
    embed_overview,
    embed_init,
    embed_status,
    embed_enemy,
    embed_dice,
    embed_quick,
    embed_poll,
    embed_gpt,
    embed_quest,
    embed_item,
    embed_npc,
    embed_favor,
    embed_scene,
)

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
    "npc": embed_npc,
    "favor": embed_favor,
    "scene": embed_scene,
}

OPTIONS = [
    ("🧍 Status", "status"),
    ("👹 Enemy", "enemy"),
    ("⚔️ Init", "init"),
    ("🎲 Dice", "dice"),
    ("⚡ Quick", "quick"),
    ("📜 Quest", "quest"),
    ("👤 NPC", "npc"),
    ("🧰 Item", "item"),
    ("🪙 Favor", "favor"),
    ("📍 Scene", "scene"),
    ("📊 Poll", "poll"),
    ("🧠 GPT", "gpt"),
    ("📖 Overview", "overview"),
]


def _get_embed(prefix: str, key: str) -> discord.Embed:
    key = (key or "overview").lower()
    fn = EMBED_MAP.get(key, embed_overview)
    return fn(prefix)


class HelpSelect(discord.ui.Select):
    def __init__(self, prefix: str, current: str = "overview"):
        self.prefix = prefix
        options = [
            discord.SelectOption(label=label, value=value, default=(value == current))
            for (label, value) in OPTIONS
        ]
        super().__init__(
            placeholder="Pilih kategori bantuan…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_select",
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        embed = _get_embed(self.prefix, value)
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, prefix: str, current: str = "overview", timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.prefix = prefix
        self.current = current
        self.message: discord.Message | None = None
        # Select
        self.add_item(HelpSelect(prefix=self.prefix, current=current))

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        # Gracefully disable controls
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.secondary, custom_id="help_overview")
    async def to_overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _get_embed(self.prefix, "overview")
        # Reset default selected option
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
            # Fallback: disable the view
            for child in self.children:
                if hasattr(child, "disabled"):
                    child.disabled = True
            await interaction.response.edit_message(content="(help ditutup)", view=self)


class HelpUICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context, topic: str | None = None):
        """Help interaktif. Opsional: !help <topik> langsung menampilkan embed topik itu, tetap dengan UI."""
        prefix = ctx.prefix or "!"
        key = (topic or "overview").lower()
        embed = _get_embed(prefix, key if key in EMBED_MAP else "overview")
        view = HelpView(prefix=prefix, current=(key if key in EMBED_MAP else "overview"))
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg  # untuk cleanup saat timeout

async def setup(bot: commands.Bot):
    # Pastikan default help bawaan discord.py tidak bentrok
    bot.help_command = None
    try:
        bot.remove_command("help")
    except Exception:
        pass
    await bot.add_cog(HelpUICog(bot))
