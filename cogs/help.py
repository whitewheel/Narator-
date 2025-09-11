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
COLOR_ENEMY     = discord.Color.dark_red()

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
    e.add_field(name="⚔️ Initiative", value="Kelola urutan giliran & round saat encounter berlangsung.", inline=False)
    e.add_field(name="🧍 Karakter Status", value="Pantau HP/Energy/Stamina, core stats (STR, DEX, dll), buff & debuff.", inline=False)
    e.add_field(name="👾 Enemy Status", value="Tracker untuk musuh (HP, core stats, buff/debuff).", inline=False)
    e.add_field(name="🎲 Dice Roller", value="Lempar dadu fleksibel, support core stats, buff/debuff, dan cek DC.", inline=False)
    e.add_field(name="📊 Polling", value="Buat voting cepat untuk keputusan party dengan reaction.", inline=False)
    e.add_field(name="🧠 GPT", value="Tanya jawab, definisi, rangkuman, atau cerita interaktif dari GPT.", inline=False)
    e.add_field(name="⚡ Quick & Utility", value="Alias singkat + helper (contoh: `!dmg`, `!heal`, `!multi`, `!undo`).", inline=False)
    e.set_footer(text=f"Contoh: {prefix}help init • {prefix}help status • {prefix}help enemy • {prefix}help quick")
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
            f"- Bisa pakai pemisah: koma, titik koma, pipe, atau **baris baru**.\n"
            f"- Contoh multi-line:\n```txt\n{prefix}init addmany\nAlice 18\nBorin 15\nGoblin 12\n```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Shuffle Pointer",
        value=(f"- `{prefix}init shuffle` → acak pointer (siapa mulai dulu)."),
        inline=False
    )
    e.add_field(
        name="🔹 Engage (Mulai Encounter)",
        value=(f"- `{prefix}engage` (alias: `{prefix}start`, `{prefix}begin`) → mulai encounter dengan efek drumroll."),
        inline=False
    )
    e.add_field(
        name="🔹 Alias Cepat",
        value=(f"- `{prefix}next` / `{prefix}n` = `{prefix}init next`\n- `{prefix}order` = `{prefix}init show`"),
        inline=False
    )
    e.add_field(
        name="🔹 Mekanik Round",
        value=(
            "- Round dimulai di **1**.\n"
            "- Setiap kali pointer kembali ke urutan pertama saat `next` → Round naik +1.\n"
            "- Bisa set manual dengan `init round <angka>`."
        ),
        inline=False
    )
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Karakter Status",
        description="Tracker karakter: HP, Energy, Stamina, Core Stats (STR, DEX, CON, INT, WIS, CHA) + Buff/Debuff.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>`\n- `{prefix}status dmg/heal <Nama> <jumlah>`"),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=(f"- `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n- Modifier otomatis: floor(score/5)"),
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(f"- `{prefix}status buff/debuff <Nama> <teks> [durasi|perm]`\n- `{prefix}status clearbuff/cleardebuff <Nama>`"),
        inline=False
    )
    e.add_field(
        name="🔹 Show",
        value=(f"- `{prefix}status show [Nama]`\n- Alias cepat: `{prefix}stat <Nama>`, `{prefix}party`"),
        inline=False
    )
    return e

def embed_enemy(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👾 Enemy Status",
        description="Tracker musuh (NPC/monster): HP, Energy, Stamina, Core Stats + Buff/Debuff.",
        color=COLOR_ENEMY,
        timestamp=datetime.datetime.utcnow()
  )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}enemy set <Nama> <HP> <Energy> <Stamina>`\n"
            f"- `{prefix}enemy addmany` → tambah banyak musuh sekaligus.\n"
            "  Contoh inline:\n"
            f"  ```txt\n"
            f"  {prefix}enemy addmany Goblin 15 0 5 x2, Archer 10 5 3 x1\n"
            "  ```\n"
            "  Contoh multi-line:\n"
            f"  ```txt\n"
            f"  {prefix}enemy addmany\n"
            "  Goblin 15 0 5 x2\n"
            "  Archer 10 5 3 x1\n"
            "  ```\n"
            f"- `{prefix}enemy dmg <Nama> <jumlah>` → kurangi HP musuh\n"
            f"- `{prefix}enemy heal <Nama> <jumlah>` → tambah HP musuh\n"
            f"- Tambahkan `all` di akhir untuk AoE (kena semua musuh dengan nama sama)"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=f"- `{prefix}enemy setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`",
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(
            f"- `{prefix}enemy buff/debuff <Nama> <teks> [durasi|perm]`\n"
            f"- `{prefix}enemy clearbuff/cleardebuff <Nama>`\n"
            f"- `{prefix}enemy unbuff/undebuff <Nama> <teks>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Show",
        value=(
            f"- `{prefix}enemy show` → tampilkan semua musuh (embed per musuh)\n"
            f"- `{prefix}enemy show Goblin` → filter semua musuh yang namanya mulai dengan Goblin"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Tick Round",
        value=f"- `{prefix}enemy tick` → kurangi durasi buff/debuff semua musuh per round",
        inline=False
    )
    return e

def embed_dice(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎲 Dice Roller",
        description="Lempar dadu dengan support core stats, buff/debuff, dan DC check.",
        color=COLOR_DICE,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(f"`{prefix}roll XdY [+mod] [dc N]`\nContoh: `{prefix}roll 2d20 +3 dc 15`"),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=(f"- Tambahkan `+str`, `+dex`, `+con`, `+int`, `+wis`, `+cha`\n- Gunakan `as <Nama>` untuk pilih karakter/enemy"),
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(f"- Buff/debuff aktif otomatis kalau pakai stat terkait\n- Semua muncul di breakdown embed"),
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
        value=f"```txt\n{prefix}poll \"Ke mana selanjutnya?\" Utara Selatan Timur\n```",
        inline=False
    )
    return e

def embed_gpt(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧠 GPT Utilities",
        description="Tanya jawab, definisi, rangkuman, atau cerita interaktif dari GPT.",
        color=COLOR_GPT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="Perintah",
        value=(f"- `{prefix}ask <pertanyaan>`\n- `{prefix}define <kata>`\n- `{prefix}summarize <teks>`\n- `{prefix}story <prompt>`"),
        inline=False
    )
    return e

def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Quick Commands & Utility",
        description="Alias singkat & utilitas untuk mempercepat command yang sering dipakai.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Status",
        value=(
            f"- `{prefix}dmg <Nama> <jumlah>` = `{prefix}status dmg`\n"
            f"- `{prefix}heal <Nama> <jumlah>` = `{prefix}status heal`\n"
            f"- `{prefix}stat <Nama>` = `{prefix}status show <Nama>`\n"
            f"- `{prefix}party` = `{prefix}status show` (semua karakter)"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Initiative",
        value=(
            f"- `{prefix}next` / `{prefix}n` = `{prefix}init next`\n"
            f"- `{prefix}order` = `{prefix}init show`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Dice",
        value=(
            f"- `{prefix}r` = `{prefix}roll`\n"
            f"  Contoh: `{prefix}r 1d20 +str`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Utility",
        value=(
            f"- `{prefix}multi` → jalankan beberapa command sekaligus.\n"
            "  Cara pakai:\n"
            "  ```txt\n"
            f"  {prefix}multi\n"
            "  status set Alice 20 5 3\n"
            "  status setcore Alice 10 12 14 8 13 9\n"
            "  enemy set Goblin 15 2 4\n"
            "  dmg Alice 5\n"
            "  roll 1d20 +str\n"
            "  ```\n"
            f"- `{prefix}undo` → batalkan aksi terakhir (HP/Energy/Stamina karakter atau musuh)"
        ),
        inline=False
    )
    e.set_footer(text="Quick & Utility = shortcut dan helper → hasil sama seperti command panjangnya.")
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

    @discord.ui.button(label="Enemy", style=discord.ButtonStyle.secondary, emoji="👾")
    async def btn_enemy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_enemy(self.prefix), view=self)

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
        bot.remove_command("help")

    @commands.command(name="help")
    async def help(self, ctx, *, topic: str = None):
        """Help interaktif + help per-topik, ex: !help init"""
        prefix = ctx.prefix or "!"
        if not topic:
            view = HelpView(prefix=prefix)
            await ctx.send(embed=embed_overview(prefix), view=view)
            return

        t = topic.lower().strip()
        if t == "init":
            await ctx.send(embed=embed_init(prefix))
        elif t == "status":
            await ctx.send(embed=embed_status(prefix))
        elif t in ("enemy", "monsters", "npc"):
            await ctx.send(embed=embed_enemy(prefix))
        elif t in ("roll", "dice"):
            await ctx.send(embed=embed_dice(prefix))
        elif t == "poll":
            await ctx.send(embed=embed_poll(prefix))
        elif t in ("gpt", "ask", "define", "summarize", "story"):
            await ctx.send(embed=embed_gpt(prefix))
        elif t in ("quick", "alias", "shortcut", "utility"):
            await ctx.send(embed=embed_quick(prefix))
        else:
            await ctx.send("❓ Topik tidak dikenali. Coba `!help` untuk daftar lengkap.")

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
