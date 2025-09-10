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
    e.add_field(name="⚔️ Initiative", value="Kelola urutan giliran & round saat encounter.", inline=False)
    e.add_field(name="🧍 Karakter Status", value="Pantau HP, Energy, Stamina, Core Stats, Buff & Debuff.", inline=False)
    e.add_field(name="🎲 Dice Roller", value="Lempar dadu fleksibel + modifier + cek DC.", inline=False)
    e.add_field(name="📊 Polling", value="Buat voting cepat dengan reaction.", inline=False)
    e.add_field(name="🧠 GPT", value="Tanya jawab, definisi, rangkuman, atau cerita interaktif.", inline=False)
    e.add_field(name="⚡ Quick Commands", value="Alias singkat (contoh: `!dmg`, `!heal`, `!stat`, `!party`, `!next`).", inline=False)
    e.set_footer(text=f"Contoh: {prefix}help init  •  {prefix}help status  •  {prefix}help quick")
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Karakter Status",
        description="Tracker in-memory untuk karakter: ❤️ HP / 🔋 Energy / ⚡ Stamina + Core Stats (STR, DEX, CON, INT, WIS, CHA) + Buff/Debuff.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Perintah Dasar",
        value=(
            f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>` → buat karakter\n"
            f"- `{prefix}status setmax <Nama> <HPmax> <EnergyMax> <StaminaMax>` → set batas max\n"
            f"- `{prefix}status dmg/heal <Nama> <X>` → ubah HP\n"
            f"- `{prefix}status useenergy/regenenergy <Nama> <X>` → Energy\n"
            f"- `{prefix}status usestam/regenstam <Nama> <X>` → Stamina\n"
            f"- `{prefix}status remove <Nama>` / `{prefix}status clear` → hapus/reset"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core Stats",
        value=(
            f"- `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>` → set semua core\n"
            f"- Stats otomatis dihitung mod: (score-10)//2\n"
            f"- Ditampilkan di embed status"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Buff & Debuff",
        value=(
            f"- `{prefix}status buff <Nama> <teks>` → tambah buff\n"
            f"- `{prefix}status debuff <Nama> <teks>` → tambah debuff\n"
            f"- `{prefix}status clearbuff <Nama>` / `{prefix}status cleardebuff <Nama>` → hapus semua"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Show",
        value=(
            f"- `{prefix}status show` → tampilkan semua karakter\n"
            f"- `{prefix}status show <Nama>` → tampilkan 1 karakter\n"
            f"- Alias cepat: `{prefix}stat <Nama>` / `{prefix}party`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            "```txt\n"
            "!status set Alice 40 20 15\n"
            "!status setcore Alice 16 14 12 10 10 8\n"
            "!status buff Alice +2 STR (Potion)\n"
            "!status debuff Alice -1 AC (Weakened)\n"
            "!stat Alice\n"
            "!party\n"
            "```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh Output (!party)",
        value=(
            "```txt\n"
            "🧍 Karakter Status\n"
            "Alice:\n"
            "  ❤️ HP: 35/40 [████████░░]\n"
            "  🔋 Energy: 20/20 [██████████]\n"
            "  ⚡ Stamina: 12/15 [████████░░]\n"
            "  📊 Stats: STR 16 (+3) | DEX 14 (+2) | CON 12 (+1)\n"
            "            INT 10 (+0) | WIS 10 (+0) | CHA  8 (-1)\n"
            "  ✨ Buffs:\n"
            "  +2 STR (Potion of Giant Strength)\n"
            "  ☠️ Debuffs:\n"
            "  -1 AC (Weakened)\n"
            "```"
        ),
        inline=False
    )
    return e

def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Quick Commands",
        description="Alias singkat supaya nggak perlu ngetik panjang.",
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
            f"- `{prefix}ene- <Nama> <X>` / `{prefix}ene+ <Nama> <X>` → Energy\n"
            f"- `{prefix}stam- <Nama> <X>` / `{prefix}stam+ <Nama> <X>` → Stamina\n"
            f"- `{prefix}stat <Nama>` → tampilkan 1 karakter\n"
            f"- `{prefix}party` → tampilkan semua karakter"
        ),
        inline=False
    )
    e.set_footer(text="Contoh: !dmg Alice 5 • !stat Borin • !party")
    return e

# ===== View dengan tombol =====
class HelpView(discord.ui.View):
    def __init__(self, prefix: str, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.prefix = prefix

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.primary, emoji="📖")
    async def btn_overview(self, interaction, button):
        await interaction.response.edit_message(embed=embed_overview(self.prefix), view=self)

    @discord.ui.button(label="Initiative", style=discord.ButtonStyle.success, emoji="⚔️")
    async def btn_init(self, interaction, button):
        from .help_init import embed_init
        await interaction.response.edit_message(embed=embed_init(self.prefix), view=self)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.danger, emoji="🧍")
    async def btn_status(self, interaction, button):
        await interaction.response.edit_message(embed=embed_status(self.prefix), view=self)

    @discord.ui.button(label="Dice", style=discord.ButtonStyle.secondary, emoji="🎲")
    async def btn_dice(self, interaction, button):
        from .help_dice import embed_dice
        await interaction.response.edit_message(embed=embed_dice(self.prefix), view=self)

    @discord.ui.button(label="Poll", style=discord.ButtonStyle.secondary, emoji="📊")
    async def btn_poll(self, interaction, button):
        from .help_poll import embed_poll
        await interaction.response.edit_message(embed=embed_poll(self.prefix), view=self)

    @discord.ui.button(label="GPT", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def btn_gpt(self, interaction, button):
        from .help_gpt import embed_gpt
        await interaction.response.edit_message(embed=embed_gpt(self.prefix), view=self)

    @discord.ui.button(label="Quick", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def btn_quick(self, interaction, button):
        await interaction.response.edit_message(embed=embed_quick(self.prefix), view=self)

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command("help")

    @commands.command(name="help")
    async def help(self, ctx, *, topic: str = None):
        prefix = ctx.prefix or "!"
        if not topic:
            return await ctx.send(embed=embed_overview(prefix), view=HelpView(prefix))

        t = topic.lower().strip()
        if t == "status":
            await ctx.send(embed=embed_status(prefix))
        elif t in ("quick", "alias"):
            await ctx.send(embed=embed_quick(prefix))
        elif t == "init":
            from .help_init import embed_init
            await ctx.send(embed=embed_init(prefix))
        elif t in ("roll", "dice"):
            from .help_dice import embed_dice
            await ctx.send(embed=embed_dice(prefix))
        elif t == "poll":
            from .help_poll import embed_poll
            await ctx.send(embed=embed_poll(prefix))
        elif t in ("gpt", "ask", "define", "summarize", "story"):
            from .help_gpt import embed_gpt
            await ctx.send(embed=embed_gpt(prefix))
        else:
            await ctx.send(
                "❓ Topik tidak dikenali.\n"
                f"Coba: `{prefix}help init`, `{prefix}help status`, `{prefix}help roll`, `{prefix}help poll`, `{prefix}help gpt`, `{prefix}help quick`"
            )

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
