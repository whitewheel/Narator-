import datetime
import discord
from discord.ext import commands

# ====== Warna konsisten (ikon/tema tetap) ======
COLOR_OVERVIEW  = discord.Color.blurple()
COLOR_INIT      = discord.Color.green()
COLOR_STATUS    = discord.Color.red()
COLOR_ENEMY     = discord.Color.dark_red()
COLOR_DICE      = discord.Color.gold()
COLOR_POLL      = discord.Color.blue()
COLOR_GPT       = discord.Color.purple()
COLOR_QUICK     = discord.Color.orange()

# ========= EMBED BUILDERS =========
def embed_overview(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📖 Bantuan Bot",
        description=(
            "Selamat datang! Pilih topik bantuan dengan mengetik:\n"
            f"`{prefix}help init` • `{prefix}help status` • `{prefix}help enemy` • `{prefix}help dice`\n"
            f"`{prefix}help quick` • `{prefix}help poll` • `{prefix}help gpt`\n\n"
            f"Gunakan `{prefix}help <topik>` untuk detail."
        ),
        color=COLOR_OVERVIEW,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(name="⚔️ Initiative", value="Kelola urutan giliran, mulai (`engage`) & akhiri (`victory`).", inline=False)
    e.add_field(name="🧍 Karakter Status", value="HP / Energy / Stamina, Core Stats, Buff/Debuff, tampilkan status.", inline=False)
    e.add_field(name="👾 Enemy Status", value="Tracker musuh: tambah satu/banyak, dmg/heal (AoE prefix), buff/debuff.", inline=False)
    e.add_field(name="🎲 Dice Roller", value="Roll dadu fleksibel, dukung `+str` dkk, `as <Nama>`, dan `dc`/`vs`.", inline=False)
    e.add_field(name="⚡ Quick & Utility", value="Alias cepat: `dmg`, `heal`, `ene±`, `stam±`, `stat`, `party`, `undo`, `multi`.", inline=False)
    e.add_field(name="📊 Polling", value="Buat voting cepat dengan reaction angka.", inline=False)
    e.add_field(name="🧠 GPT", value="Tanya, definisi, ringkas, cerita.", inline=False)
    e.set_footer(text=f"Contoh: {prefix}help enemy • {prefix}help quick")
    return e

def embed_init(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Initiative Tracker",
        description="Urutan giliran pertarungan (per channel, in-memory).",
        color=COLOR_INIT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}init add <Nama> <Skor>`\n"
            f"- `{prefix}init show` (alias: `{prefix}order`)\n"
            f"- `{prefix}init next` (alias: `{prefix}next` / `{prefix}n`)\n"
            f"- `{prefix}init setptr <index>` (mulai dari 1)\n"
            f"- `{prefix}init remove <Nama>` • `{prefix}init clear`\n"
            f"- `{prefix}init round` / `{prefix}init round <angka>`\n"
            f"- `{prefix}init shuffle` (acak pointer awal)"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Tambah Banyak",
        value=(
            f"- Inline: `{prefix}init addmany \"Alice 18, Goblin 12, Mage 16\"`\n"
            "- Multi-line:\n"
            f"```txt\n{prefix}init addmany\nAlice 18\nGoblin 12\nMage 16\n```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Mulai & Akhiri",
        value=(
            f"- Mulai: `{prefix}engage` (alias: `{prefix}start`, `{prefix}begin`)\n"
            f"- Akhiri: `{prefix}victory` (alias: `{prefix}end`, `{prefix}finish`, `{prefix}win`)\n"
            "  Opsi `victory`: `keep` (jangan hapus musuh), `clear` (hapus musuh, default), `force` (paksa selesai).\n"
            "_Saat semua musuh 0 HP, bot akan menyarankan pakai `victory`._"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh Alur",
        value=(
            f"```txt\n{prefix}init add Alice 18\n{prefix}init add Goblin 12\n{prefix}order\n{prefix}engage\n{prefix}next\n{prefix}victory\n```"
        ),
        inline=False
    )
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Karakter Status",
        description="Kelola karakter: HP, Energy, Stamina, Core Stats, Buff/Debuff.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>`\n"
            f"- `{prefix}status show [Nama]` • `{prefix}status remove <Nama>` • `{prefix}status clear`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Resource",
        value=(
            f"- Core: `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            f"- Energy: `{prefix}status useenergy/regenenergy <Nama> <jumlah>`\n"
            f"- Stamina: `{prefix}status usestam/regenstam <Nama> <jumlah>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 HP & Efek",
        value=(
            f"- HP: `{prefix}status dmg/heal <Nama> <jumlah>`\n"
            f"- Buff/Debuff: `{prefix}status buff/debuff <Nama> <teks> [durasi|perm]`\n"
            f"- Hapus: `{prefix}status clearbuff/cleardebuff <Nama>` • `unbuff/undebuff <Nama> <teks>`\n"
            f"- Durasi: `{prefix}status tick` (kurangi 1 pada semua efek berdurasi)"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            f"```txt\n{prefix}status set Alice 20 5 3\n{prefix}status setcore Alice 14 12 12 10 8 13\n"
            f"{prefix}status buff Alice \"+2 STR\" 3\n{prefix}status dmg Alice 4\n{prefix}status show Alice\n{prefix}status tick\n```"
        ),
        inline=False
    )
    e.add_field(
        name="ℹ️ Tips",
        value=f"Gunakan alias cepat di `{prefix}help quick` untuk operasi umum.",
        inline=False
    )
    return e

def embed_enemy(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👾 Enemy Status",
        description="Kelola musuh/NPC: HP, Energy, Stamina, Buff/Debuff, tampilkan status.",
        color=COLOR_ENEMY,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}enemy set <Nama> <HP> <Energy> <Stamina>`\n"
            f"- `{prefix}enemy show [Nama]` • `{prefix}enemy remove <Nama>` • `{prefix}enemy clear`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Tambah Banyak",
        value=(
            f"- Inline: `{prefix}enemy addmany Goblin 15 0 15 x2, Archer 10 5 10 x1`\n"
            "- Multi-line:\n"
            f"```txt\n{prefix}enemy addmany\nGoblin 15 0 15 x2\nArcher 10 5 10 x1\n```"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Pertarungan",
        value=(
            f"- HP: `{prefix}enemy dmg/heal <Nama> <jumlah>` • tambahkan `all` untuk AoE (prefix nama)\n"
            f"- Energy: `{prefix}enemy useenergy/regenenergy <Nama> <jumlah>`\n"
            f"- Stamina: `{prefix}enemy usestam/regenstam <Nama> <jumlah>`\n"
            f"- Buff/Debuff: `{prefix}enemy buff/debuff <Nama> <teks> [durasi|perm]` • `clearbuff/cleardebuff` • `unbuff/undebuff`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            f"```txt\n{prefix}enemy addmany\nGoblin 15 0 15 x2\nArcher 10 5 10 x1\n"
            f"{prefix}enemy dmg Goblin 3 all\n{prefix}enemy show\n```"
        ),
        inline=False
    )
    e.add_field(
        name="ℹ️ Catatan",
        value="AoE `all` menerapkan ke semua musuh yang **diawali** nama tersebut (mis. `Goblin` → `Goblin`, `Goblin_1`, ...).",
        inline=False
    )
    return e

def embed_dice(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎲 Dice Roller",
        description="Roll dadu dengan modifier, DC check, integrasi core & buff.",
        color=COLOR_DICE,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}roll 2d6 +1` (alias: `{prefix}r`)\n"
            f"- Dukung beberapa dadu: `1d20 + 2d6 - 1`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 DC / Versus",
        value=(
            f"- Tambah target: `dc 15` / `vs 15` → hasil dibandingkan otomatis\n"
            f"  Contoh: `{prefix}roll 1d20 +2 dc 14`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Buff",
        value=(
            f"- Pakai core seorang karakter: `as <Nama>` + `+str/+dex/...`\n"
            f"  Contoh: `{prefix}roll as Alice 1d20 +str +2 dc 12`\n"
            f"- Buff/debuff yang match (mis. `+2 STR`, `-1 DEX`, `+1 ALL`) ikut dihitung."
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh Lengkap",
        value=(
            f"```txt\n{prefix}status set Alice 20 5 3\n{prefix}status setcore Alice 14 12 12 10 8 13\n"
            f"{prefix}status buff Alice \"+2 STR\" 3\n{prefix}roll as Alice 1d20 +str +2 dc 12\n```"
        ),
        inline=False
    )
    return e

def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Quick Commands & Utility",
        description="Alias singkat untuk operasi umum + utilitas.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Alias Pertarungan",
        value=(
            f"- `{prefix}dmg <Nama> <jumlah> [all]` • `{prefix}heal <Nama> <jumlah> [all]`\n"
            f"- `{prefix}ene- <Nama> <jumlah>` • `{prefix}ene+ <Nama> <jumlah>`\n"
            f"- `{prefix}stam- <Nama> <jumlah>` • `{prefix}stam+ <Nama> <jumlah>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Lihat Status Cepat",
        value=(f"- `{prefix}stat <Nama>` = `{prefix}status show <Nama>`\n- `{prefix}party` = `{prefix}status show` semua karakter"),
        inline=False
    )
    e.add_field(
        name="🔹 Undo & Multi",
        value=(f"- `{prefix}undo` → batalkan perubahan terakhir (HP/EN/ST)\n- `{prefix}multi` → jalankan beberapa command dalam satu pesan"),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            f"```txt\n{prefix}dmg Alice 4\n{prefix}heal Goblin 2\n{prefix}ene- Alice 1\n{prefix}stam+ Goblin 1\n"
            f"{prefix}stat Alice\n{prefix}party\n{prefix}undo\n```"
        ),
        inline=False
    )
    return e

def embed_poll(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📊 Polling",
        description="Buat voting cepat dengan reaction angka.",
        color=COLOR_POLL,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Cara pakai",
        value=(
            f"- `{prefix}poll \"Pertanyaan?\" opsi1 opsi2 opsi3 ...`\n"
            f"  Contoh: `{prefix}poll \"Masuk dungeon?\" Ya Tidak Nanti`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=f"```txt\n{prefix}poll \"Pilih arah?\" Kanan Kiri Mundur\n```",
        inline=False
    )
    return e

def embed_gpt(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧠 GPT",
        description="Tanya, definisi, ringkas, dan cerita.",
        color=COLOR_GPT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Perintah",
        value=(
            f"- `{prefix}ask <pertanyaan>`\n"
            f"- `{prefix}define <kata>`\n"
            f"- `{prefix}summarize <teks>`\n"
            f"- `{prefix}story <prompt>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            f"```txt\n{prefix}ask Apa itu advantage di d20?\n{prefix}define parry\n"
            f"{prefix}summarize \"Teks panjang lore...\"\n{prefix}story \"Pembuka one-shot fantasi gelap\"\n```"
        ),
        inline=False
    )
    return e

# ========= HELP COG =========
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx, topic: str = None):
        prefix = ctx.prefix or "!"
        key = (topic or "").strip().lower()

        if key in ("init", "initiative", "engage", "victory"):
            embed = embed_init(prefix)
        elif key in ("status", "char", "character"):
            embed = embed_status(prefix)
        elif key in ("enemy", "enemies", "monster", "monsters"):
            embed = embed_enemy(prefix)
        elif key in ("dice", "roll", "r"):
            embed = embed_dice(prefix)
        elif key in ("quick", "alias", "aliases", "utility", "utils"):
            embed = embed_quick(prefix)
        elif key in ("poll", "polling", "vote"):
            embed = embed_poll(prefix)
        elif key in ("gpt", "ai"):
            embed = embed_gpt(prefix)
        elif key in ("overview", "detail", "menu", "home"):  # alias resmi untuk Overview
            embed = embed_overview(prefix)
        else:
            embed = embed_overview(prefix)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
