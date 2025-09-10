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

# ===== Embed Builders =====
def embed_overview(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📖 Bantuan Bot",
        description=(
            f"Gunakan `{prefix}help <topik>` untuk detail cepat.\n"
            f"Atau klik tombol di bawah untuk pindah kategori."
        ),
        color=COLOR_OVERVIEW,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="⚔️ Initiative",
        value=f"`{prefix}init add/show/next/remove/clear/setptr`",
        inline=False
    )
    e.add_field(
        name="🧍 Karakter Status",
        value=f"`{prefix}status set/show/dmg/heal/useenergy/usestam/...`",
        inline=False
    )
    e.add_field(
        name="🎲 Dice Roller",
        value=f"`{prefix}roll <XdY+Z>`  • Contoh: `{prefix}roll 2d6+3`",
        inline=False
    )
    e.add_field(
        name="📊 Polling",
        value=f"`{prefix}poll \"Judul\" opsi1 opsi2 ...`",
        inline=False
    )
    e.add_field(
        name="🧠 GPT",
        value=f"`{prefix}ask` · `{prefix}define` · `{prefix}summarize` · `{prefix}story`",
        inline=False
    )
    e.set_footer(text="Tips: ketik !help init atau !help status untuk detail.")
    return e

def embed_init(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Initiative Tracker",
        description="In-memory tracker per channel (hilang saat restart).",
        color=COLOR_INIT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Perintah",
        value=(
            f"• `{prefix}init add <Nama> <Skor>` — tambah/ubah peserta\n"
            f"• `{prefix}init show` — tampilkan urutan & giliran\n"
            f"• `{prefix}init next` — ganti ke giliran berikut\n"
            f"• `{prefix}init setptr <nomor>` — set giliran manual (mulai 1)\n"
            f"• `{prefix}init remove <Nama>` — hapus peserta\n"
            f"• `{prefix}init clear` — reset tracker"
        ),
        inline=False
    )
    e.add_field(
        name="Contoh",
        value=(
            "```txt\n"
            "!init add Alice 18\n"
            "!init add Goblin 12\n"
            "!init show\n"
            "!init next\n"
            "```"
        ),
        inline=False
    )
    e.set_footer(text="Data disortir: skor desc, nama asc. Panah 👉 menandai giliran.")
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Karakter Status",
        description="Tracker in-memory untuk ❤️ HP / 🔋 Energy / ⚡ Stamina (hilang saat bot restart).",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Perintah",
        value=(
            f"• `{prefix}status set <Nama> <HP> <Energy> <Stamina>` → buat karakter\n"
            f"• `{prefix}status setmax <Nama> <HPmax> <EnergyMax> <StaminaMax>` → atur batas max\n"
            f"• `{prefix}status dmg <Nama> <jumlah>` → kurangi HP\n"
            f"• `{prefix}status heal <Nama> <jumlah>` → tambah HP\n"
            f"• `{prefix}status useenergy <Nama> <jumlah>` / `{prefix}status regenenergy <Nama> <jumlah>`\n"
            f"• `{prefix}status usestam <Nama> <jumlah>` / `{prefix}status regenstam <Nama> <jumlah>`\n"
            f"• `{prefix}status show` → tampilkan semua (embed)\n"
            f"• `{prefix}status remove <Nama>` → hapus karakter\n"
            f"• `{prefix}status clear` → reset channel"
        ),
        inline=False
    )
    e.add_field(
        name="Contoh",
        value=(
            "```txt\n"
            "!status set Alice 40 20 15\n"
            "!status dmg Alice 5\n"
            "!status usestam Alice 3\n"
            "!status show\n"
            "```"
        ),
        inline=False
    )
    e.add_field(
        name="Contoh Output",
        value=(
            "```\n"
            "🧍 Karakter Status\n"
            "Alice:\n"
            "  ❤️ HP: 35/40 [██████████░░]\n"
            "  🔋 Energy: 20/20 [████████████]\n"
            "  ⚡ Stamina: 12/15 [██████████░░]\n"
            "```"
        ),
        inline=False
    )
    e.set_footer(text="Visual bar: █ penuh | ░ kosong")
    return e

def embed_dice(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎲 Dice Roller",
        description="Lempar dadu fleksibel dengan modifier.",
        color=COLOR_DICE,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Format",
        value=f"`{prefix}roll XdY+Z`  • contoh: `{prefix}roll 3d8+2`, `{prefix}roll 1d20`",
        inline=False
    )
    e.add_field(
        name="Fitur",
        value="• Embed hasil roll\n• Deteksi CRIT (20) / FAIL (1) untuk 1d20",
        inline=False
    )
    e.add_field(
        name="Contoh",
        value="```txt\n!roll 2d6+3\nHasil: 🎲 5 + 2 + 3 = 10```",
        inline=False
    )
    return e

def embed_poll(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📊 Polling Cepat",
        description="Buat voting dengan reaction angka 1️⃣–🔟.",
        color=COLOR_POLL,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Format",
        value=f"`{prefix}poll \"Judul\" opsi1 opsi2 ...`",
        inline=False
    )
    e.add_field(
        name="Contoh",
        value="```txt\n!poll \"Ke mana selanjutnya?\" Utara Selatan Timur\n```",
        inline=False
    )
    e.set_footer(text="Judul multi-kata WAJIB pakai tanda kutip.")
    return e

def embed_gpt(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧠 GPT Utilities",
        description="Jawaban otomatis dibungkus blok kode untuk rapi.",
        color=COLOR_GPT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Perintah",
        value=(
            f"• `{prefix}ask <pertanyaan>`\n"
            f"• `{prefix}define <kata>`\n"
            f"• `{prefix}summarize <teks>`\n"
            f"• `{prefix}story <prompt>`"
        ),
        inline=False
    )
    e.add_field(
        name="Catatan",
        value="Jawaban panjang otomatis dipotong jadi beberapa pesan, atau dikirim .txt bila sangat panjang.",
        inline=False
    )
    return e

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
        else:
            await ctx.send("❓ Topik tidak dikenali. Coba `!help`, `!help init`, `!help status`, `!help roll`, `!help poll`, atau `!help gpt`.")

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
