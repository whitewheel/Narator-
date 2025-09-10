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
        value="Pantau HP/Energy/Stamina, core stats (STR, DEX, dll), buff & debuff.",
        inline=False
    )
    e.add_field(
        name="🎲 Dice Roller",
        value="Lempar dadu fleksibel, support core stats, buff/debuff, dan cek DC.",
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
        value="Alias singkat untuk perintah populer (contoh: `!dmg`, `!heal`, `!stat`, `!next`).",
        inline=False
    )
    e.set_footer(text=f"Contoh: {prefix}help init • {prefix}help status • {prefix}help roll")
    return e

def embed_init(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Initiative Tracker",
        description="Sistem urutan giliran (initiative order) untuk combat. Data disimpan per channel & hilang saat bot restart.",
        color=COLOR_INIT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Format Dasar",
        value=(
            f"- `{prefix}init add <Nama> <Skor>` → tambah/ubah peserta.\n"
            f"- `{prefix}init show` → tampilkan urutan & giliran aktif.\n"
            f"- `{prefix}init next` → pindah ke giliran berikut (berputar).\n"
            f"- `{prefix}init setptr <index>` → set giliran manual (mulai 1).\n"
            f"- `{prefix}init remove <Nama>` → hapus peserta.\n"
            f"- `{prefix}init clear` → reset tracker channel ini.\n"
            f"- `{prefix}init round` / `{prefix}init round <angka>` → lihat/set round."
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Bulk & Multi-line",
        value=(
            f"- `{prefix}init addmany \"Alice 18, Goblin 12, Borin 15\"`\n"
            f"- Bisa pakai pemisah: koma `,`, titik koma `;`, pipe `|`, atau **baris baru**.\n"
            f"- Contoh multi-line:\n"
            "```txt\n"
            f"{prefix}init addmany\n"
            "Alice 18\n"
            "Borin 15\n"
            "Goblin 12\n"
            "```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Shuffle Pointer",
        value=(
            f"- `{prefix}init shuffle` → **acak pointer** (siapa mulai dulu).\n"
            f"- *Urutan berdasarkan skor tetap sama; hanya giliran awal yang digeser.*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Engage (Mulai Encounter)",
        value=(
            f"- `{prefix}engage` (alias: `{prefix}start`, `{prefix}begin`) → mulai encounter dengan efek drumroll + embed rapi.\n"
            f"- Footer embed mengingatkan pakai `{prefix}init next` untuk lanjut."
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Alias Cepat",
        value=(
            f"- `{prefix}next` (alias: `{prefix}n`) = `{prefix}init next`\n"
            f"- `{prefix}order` = `{prefix}init show`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Mekanik Round",
        value=(
            "- Round dimulai di **1**.\n"
            "- Setiap kali pointer kembali ke urutan pertama saat `next` → **Round naik +1** (bot mengumumkan).\n"
            "- Kamu bisa set manual dengan `init round <angka>`."
        ),
        inline=False
    )
    e.set_footer(text="Tips: Gunakan bareng !status untuk pantau HP/Energy/Stamina saat combat.")
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Karakter Status",
        description="Tracker karakter: ❤️ HP / 🔋 Energy / ⚡ Stamina + Core Stats (STR, DEX, CON, INT, WIS, CHA) + Buff/Debuff.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Perintah Dasar",
        value=(
            f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>` → buat karakter\n"
            f"- `{prefix}status setmax <Nama> <HPmax> <EnergyMax> <StaminaMax>` → atur batas max\n"
            f"- `{prefix}status dmg/heal <Nama> <jumlah>` → ubah HP\n"
            f"- `{prefix}status useenergy/regenenergy <Nama> <jumlah>` → ubah Energy\n"
            f"- `{prefix}status usestam/regenstam <Nama> <jumlah>` → ubah Stamina\n"
            f"- `{prefix}status remove <Nama>` / `{prefix}status clear` → hapus/reset"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=(
            f"- `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>` → set core stat\n"
            "- Modifier dihitung otomatis: (score-10)//2\n"
            "- Dapat dipakai langsung saat roll dengan `+str`, `+dex`, dst."
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(
            f"- `{prefix}status buff <Nama> <teks>` → tambah buff\n"
            f"- `{prefix}status debuff <Nama> <teks>` → tambah debuff\n"
            f"- `{prefix}status clearbuff/cleardebuff <Nama>` → hapus semua buff/debuff\n"
            "- Format yang dikenali: `+2 STR`, `-1 DEX`, `+1 ALL`, `+2 Attack`.\n"
            "- Buff/debuff ikut otomatis dihitung saat roll."
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Show & Alias",
        value=(
            f"- `{prefix}status show` → tampilkan semua karakter\n"
            f"- `{prefix}status show <Nama>` → tampilkan 1 karakter\n"
            f"- Alias cepat: `{prefix}stat <Nama>`, `{prefix}party`"
        ),
        inline=False
    )
    e.set_footer(text="Visual bar: █ penuh | ░ kosong • Buff/debuff tertentu ikut ke dice roller")
    return e

def embed_dice(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎲 Dice Roller",
        description="Lempar dadu fleksibel dengan support core stats, buff/debuff, dan DC check otomatis.",
        color=COLOR_DICE,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Format Dasar",
        value=(
            f"`{prefix}roll XdY [XdY...] [+mod ...] [dc N]`\n"
            "- `XdY` → jumlah X dadu sisi Y. Contoh `2d20`, `3d6`\n"
            "- Bisa gabung beberapa dadu: `1d8+1d6`\n"
            "- `+mod` → angka tambahan: `+2 +2 -1`\n"
            "- `+nama=angka` → modifier manual: `+prof=2`\n"
            "- `dc` / `vs N` → cek hasil lawan target DC"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=(
            "- Tambahkan `+str`, `+dex`, `+con`, `+int`, `+wis`, `+cha`\n"
            "- Nilai otomatis dihitung dari core stat karakter\n"
            "- Gunakan `as <Nama>` untuk pilih karakter:\n"
            f"```txt\n"
            f"{prefix}roll as Alice 1d20 +str +dex\n"
            f"{prefix}roll as Bob 2d6 +con dc 15\n"
            "```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(
            "- `+2 STR (Potion)` → aktif kalau pakai `+str`\n"
            "- `-1 DEX (Exhausted)` → aktif kalau pakai `+dex`\n"
            "- `+1 ALL (Bless)` → aktif di semua roll\n"
            "- `+2 Attack` → dihitung sebagai modifier generik\n"
            "- Semua muncul di breakdown embed"
        ),
        inline=False
    )
    e.set_footer(text="Tips: Simpan core stats & buff/debuff di !status supaya roll otomatis lebih akurat.")
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
        bot.remove_command("help")

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
            await ctx.send(
                "❓ Topik tidak dikenali. Coba `!help`, `!help init`, `!help status`, `!help roll`, `!help poll`, atau `!help gpt`."
            )

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
