import datetime
import discord
from discord.ext import commands

# Palet warna
COLOR_OVERVIEW  = discord.Color.blurple()
COLOR_INIT      = discord.Color.green()
COLOR_STATUS    = discord.Color.red()
COLOR_DICE      = discord.Color.gold()
COLOR_POLL      = discord.Color.blue()
COLOR_GPT       = discord.Color.purple()
COLOR_QUICK     = discord.Color.orange()

# ===== Embed Builders =====
def embed_overview(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📖 Bantuan Bot",
        description=(
            f"Selamat datang di menu bantuan!\n\n"
            f"Gunakan `{prefix}help <topik>` untuk detail cepat,\n"
            f"atau klik tombol di bawah untuk pindah kategori."
        ),
        color=COLOR_OVERVIEW,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="⚔️ Initiative",
        value="Kelola urutan giliran & round saat encounter berlangsung.",
        inline=False
    )
    e.add_field(
        name="🧍 Karakter Status",
        value="Pantau dan ubah HP, Energy, dan Stamina karakter party.",
        inline=False
    )
    e.add_field(
        name="🎲 Dice Roller",
        value="Lempar dadu fleksibel dengan modifier, advantage/disadvantage, dan cek DC.",
        inline=False
    )
    e.add_field(
        name="📊 Polling",
        value="Buat voting cepat untuk keputusan party dengan reaction.",
        inline=False
    )
    e.add_field(
        name="🧠 GPT",
        value="Tanya jawab, definisi, rangkuman, atau cerita interaktif dari GPT.",
        inline=False
    )
    e.add_field(
        name="⚡ Quick Commands",
        value="Alias singkat untuk perintah yang sering dipakai. Klik tombol ⚡ Quick untuk detail.",
        inline=False
    )
    e.set_footer(text=f"Contoh: {prefix}help init  •  {prefix}help status  •  {prefix}help quick")
    return e

def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Quick Commands",
        description="Alias singkat biar nggak perlu ngetik panjang. Cocok untuk perintah yang sering dipakai.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Initiative Cepat",
        value=(
            f"- `{prefix}next` / `{prefix}n` → lanjut giliran berikut\n"
            f"- `{prefix}order` → tampilkan urutan initiative"
        ),
        inline=False
    )
    e.add_field(
        name="Status Cepat",
        value=(
            f"- `{prefix}dmg <Nama> <X>` → kurangi HP\n"
            f"- `{prefix}heal <Nama> <X>` → tambah HP\n"
            f"- `{prefix}ene- <Nama> <X>` → kurangi Energy\n"
            f"- `{prefix}ene+ <Nama> <X>` → regen Energy\n"
            f"- `{prefix}stam- <Nama> <X>` → kurangi Stamina\n"
            f"- `{prefix}stam+ <Nama> <X>` → regen Stamina"
        ),
        inline=False
    )
    e.set_footer(text=f"Contoh: {prefix}dmg Alice 5  •  {prefix}heal Borin 10")
    return e

# --- (embed_init, embed_status, embed_dice, embed_poll, embed_gpt) ---
# biarin sesuai punyamu sekarang, aku nggak ubah isinya

# ===== View dengan tombol =====
class HelpView(discord.ui.View):
    def __init__(self, prefix: str, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.prefix = prefix

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.primary, emoji="📖")
    async def btn_overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_overview(self.prefix), view=self)

    @discord.ui.button(label="Initiative", style=discord.ButtonStyle.success, emoji="⚔️")
    async def btn_init(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_init(self.prefix), view=self)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.danger, emoji="🧍")
    async def btn_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_status(self.prefix), view=self)

    @discord.ui.button(label="Dice", style=discord.ButtonStyle.secondary, emoji="🎲")
    async def btn_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_dice(self.prefix), view=self)

    @discord.ui.button(label="Poll", style=discord.ButtonStyle.secondary, emoji="📊")
    async def btn_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_poll(self.prefix), view=self)

    @discord.ui.button(label="GPT", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def btn_gpt(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_gpt(self.prefix), view=self)

    @discord.ui.button(label="Quick", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def btn_quick(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_quick(self.prefix), view=self)

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command("help")  # ganti help default

    @commands.command(name="help")
    async def help(self, ctx, *, topic: str = None):
        """Help interaktif + help per-topik, ex: !help init"""
        prefix = ctx.prefix or "!"
        if not topic:
            view = HelpView(prefix=prefix)
            await ctx.send(embed=embed_overview(prefix), view=view)
            return

        # fallback help per topik
        t = topic.lower().strip()
        if t == "init":
            await ctx.send(embed=embed_init(prefix))
        elif t == "status":
            await ctx.send(embed=embed_status(prefix))
        elif t in ("roll", "dice"):
            await ctx.send(embed=embed_dice(prefix))
        elif t == "poll":
            await ctx.send(embed=embed_poll(prefix))
        elif t in ("gpt", "ask", "define", "summarize", "story"):
            await ctx.send(embed=embed_gpt(prefix))
        elif t in ("quick", "alias"):
            await ctx.send(embed=embed_quick(prefix))
        else:
            await ctx.send(
                "❓ Topik tidak dikenali.\n"
                f"Coba: `{prefix}help init`, `{prefix}help status`, `{prefix}help roll`, `{prefix}help poll`, `{prefix}help gpt`, `{prefix}help quick`"
            )

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
