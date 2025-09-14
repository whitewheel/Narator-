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
            f"`{prefix}help quick` • `{prefix}help poll` • `{prefix}help gpt`\n"
            f"`{prefix}help quest` • `{prefix}help item` • `{prefix}help npc` • `{prefix}help favor` • `{prefix}help scene`\n\n"
            f"Gunakan `{prefix}help <topik>` untuk detail."
        ),
        color=COLOR_OVERVIEW,
        timestamp=datetime.datetime.utcnow()
    )
    # Core play
    e.add_field(name="🧍 Karakter Status", value="HP/Energy/Stamina, Core, Buff/Debuff, ringkasan `!party`.", inline=False)
    e.add_field(name="👾 Enemy Status", value="Tambah satu/banyak, AoE `dmg/heal [all]`, buff/debuff, tick.", inline=False)
    e.add_field(name="⚔️ Initiative", value="Urutan giliran, `next`, `setptr`, `round`, `shuffle`.", inline=False)
    e.add_field(name="🎲 Dice Roller", value="`roll`/`r`, dukung `as <Nama>`, `+str|dex|…`, `dc|vs`.", inline=False)
    e.add_field(name="⚡ Quick & Utility", value="Alias cepat: `dmg/heal/ene±/stam±`, `party`, `undo`, `multi`.", inline=False)
    # World systems
    e.add_field(name="📜 Quest", value="Tambah/show/detail/done/fail/reveal/remove. Dukung `--hidden`.", inline=False)
    e.add_field(name="👤 NPC", value="Tambah/show/detail, `--hidden`, `reveal`, catatan & sikap.", inline=False)
    e.add_field(name="🧰 Item", value="Inventori & loot: add/show/detail/remove.", inline=False)
    e.add_field(name="🪙 Favor", value="Reputasi fraksi: add/set/show/detail/remove.", inline=False)
    e.add_field(name="📍 Scene", value="Pin & tampilkan lokasi/scene aktif kanal.", inline=False)
    # Misc
    e.add_field(name="📊 Polling", value="Voting cepat 1–10 dengan reaction angka.", inline=False)
    e.add_field(name="🧠 GPT", value="Define, summarize, dan story (narasi).", inline=False)
    e.set_footer(text=f"Contoh: {prefix}help enemy • {prefix}help quest • {prefix}help init")
    return e

def embed_init(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Bantuan: Initiative",
        description="Kelola urutan giliran, pointer, dan ronde.",
        color=COLOR_INIT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}init add <Nama> <initiative>` • `{prefix}init remove <Nama>`\n"
            f"- `{prefix}init show` • `{prefix}init clear`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Lanjutan",
        value=(
            f"- `{prefix}init addmany` *(multiline/inline tambah banyak)*\n"
            f"- `{prefix}init setptr <index>` • `{prefix}init next`\n"
            f"- `{prefix}init round` *(lihat/set)* • `{prefix}init shuffle`"
        ),
        inline=False
    )
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Bantuan: Status",
        description="Kelola karakter: HP, Energy, Stamina, Core, Buff/Debuff.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>`\n"
            f"- `{prefix}status show [Nama]` • `{prefix}status remove <Nama>` • `{prefix}status clear`\n"
            f"- `!party` *(ringkasan party)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Efek",
        value=(
            f"- `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            f"- `{prefix}status buff|debuff <Nama> <teks> [durasi|perm]`\n"
            f"- `{prefix}status clearbuff|cleardebuff <Nama>` • `{prefix}status unbuff|undebuff <Nama> <teks>`\n"
            f"- `{prefix}status tick` *(kurangi durasi efek 1 ronde)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Resource",
        value=(
            f"- `{prefix}status dmg|heal <Nama> <jumlah>`\n"
            f"- `{prefix}status useenergy|regenenergy <Nama> <jumlah>`\n"
            f"- `{prefix}status usestam|regenstam <Nama> <jumlah>`"
        ),
        inline=False
    )
    return e

def embed_enemy(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👾 Bantuan: Enemy",
        description="Kelola musuh: daftar, core, buff/debuff, dan AoE.",
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
            f"- Inline: `{prefix}enemy addmany Goblin 15 0 10 x2, Archer 10 3 10 x1`\n"
            f"- Multiline: gunakan satu baris per entri"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Efek",
        value=(
            f"- `{prefix}enemy setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            f"- `{prefix}enemy buff|debuff <Nama> <teks> [durasi|perm]`\n"
            f"- `{prefix}enemy clearbuff|cleardebuff <Nama>` • `{prefix}enemy unbuff|undebuff <Nama> <teks>`\n"
            f"- `{prefix}enemy tick`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Resource & AoE",
        value=(
            f"- `{prefix}enemy dmg|heal <Nama> <jumlah> [all]`\n"
            f"- `{prefix}enemy useenergy|regenenergy <Nama> <jumlah>`\n"
            f"- `{prefix}enemy usestam|regenstam <Nama> <jumlah>`"
        ),
        inline=False
    )
    return e

def embed_dice(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎲 Bantuan: Dice",
        description="Roll dadu fleksibel, dukung stat & DC.",
        color=COLOR_DICE,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}roll 2d20+2` • `{prefix}r 1d8+3`\n"
            f"- `{prefix}roll 1d20 +2 vs 14` *(bandingkan ke target)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Dengan Karakter",
        value=(
            f"- `{prefix}roll as <Nama> 1d20 +str +dex dc 16`\n"
            f"- Mendukung `+str|dex|con|int|wis|cha` & buff/debuff aktif"
        ),
        inline=False
    )
    return e

def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Bantuan: Quick",
        description="Alias cepat untuk aksi status/enemy.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Alias",
        value=(
            f"- `!dmg <Nama> <jumlah> [all]` • `!heal <Nama> <jumlah> [all]`\n"
            f"- `!ene- <Nama> <jumlah>` • `!ene+ <Nama> <jumlah>`\n"
            f"- `!stam- <Nama> <jumlah>` • `!stam+ <Nama> <jumlah>`\n"
            f"- `!party` • `!undo` • `!multi`"
        ),
        inline=False
    )
    return e

def embed_poll(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📊 Bantuan: Poll",
        description="Buat voting cepat dengan reaction angka (1–10).",
        color=COLOR_POLL,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Contoh",
        value=(
            f"- `{prefix}poll \"Makan apa?\" Nasi Mie Roti`"
        ),
        inline=False
    )
    return e

def embed_gpt(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧠 Bantuan: GPT",
        description="Akses GPT untuk definisi, ringkas, dan cerita.",
        color=COLOR_GPT,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Perintah",
        value=(
            f"- `{prefix}define <kata>`\n"
            f"- `{prefix}summarize <teks>`\n"
            f"- `{prefix}story <prompt>`"
        ),
        inline=False
    )
    return e

def embed_quest(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📜 Bantuan: Quest",
        description=(
            f"`{prefix}quest add <judul> | <objective> | <reward> | [deadline] [--hidden]`\n"
            f"`{prefix}quest show [all|done|failed|hidden]`\n"
            f"`{prefix}quest detail <judul>`\n"
            f"`{prefix}quest done|fail|reveal|remove <judul>`"
        ),
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    return e

def embed_item(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧰 Bantuan: Item",
        description=(
            f"`{prefix}item add <nama> | <tipe> | <efek> | [rarity]`\n"
            f"`{prefix}item show`\n"
            f"`{prefix}item detail <nama>`\n"
            f"`{prefix}item remove <nama>`"
        ),
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    return e

def embed_npc(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👤 Bantuan: NPC",
        description=(
            f"`{prefix}npc add <nama> | <peran> | [sikap] | [catatan] [--hidden]`\n"
            f"`{prefix}npc show`\n"
            f"`{prefix}npc detail <nama>`\n"
            f"`{prefix}npc reveal|remove <nama>`"
        ),
        color=COLOR_GPT,
        timestamp=datetime.datetime.utcnow()
    )
    return e

def embed_favor(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🪙 Bantuan: Favor",
        description=(
            f"`{prefix}favor add|set <faksi> | <nilai> | [catatan]`\n"
            f"`{prefix}favor show`\n"
            f"`{prefix}favor detail <faksi>`\n"
            f"`{prefix}favor remove <faksi>`"
        ),
        color=COLOR_POLL,
        timestamp=datetime.datetime.utcnow()
    )
    return e

def embed_scene(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📍 Bantuan: Scene",
        description=(
            f"`{prefix}scene pin` • `{prefix}scene show` • `{prefix}scene unpin` • `{prefix}scene now`"
        ),
        color=COLOR_INIT,
        timestamp=datetime.datetime.utcnow()
    )
    return e

# ========= COG =========

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx, topic: str = None):
        prefix = ctx.prefix or "!"
        key = (topic or "").strip().lower()

        if key in ("init", "initiative"):
            embed = embed_init(prefix)
        elif key in ("status", "char", "character"):
            embed = embed_status(prefix)
        elif key in ("enemy", "enemies", "monster", "monsters"):
            embed = embed_enemy(prefix)
        elif key in ("dice", "roll", "r"):
            embed = embed_dice(prefix)
        elif key in ("quick", "alias", "utility"):
            embed = embed_quick(prefix)
        elif key in ("poll", "vote"):
            embed = embed_poll(prefix)
        elif key in ("gpt", "ai"):
            embed = embed_gpt(prefix)
        elif key in ("quest",):
            embed = embed_quest(prefix)
        elif key in ("item",):
            embed = embed_item(prefix)
        elif key in ("npc",):
            embed = embed_npc(prefix)
        elif key in ("favor", "rep", "reputation"):
            embed = embed_favor(prefix)
        elif key in ("scene", "zone"):
            embed = embed_scene(prefix)
        else:
            embed = embed_overview(prefix)

        await ctx.send(embed=embed)

async def setup(bot):
    # Matikan default help agar tidak bentrok
    bot.help_command = None
    try:
        bot.remove_command("help")
    except Exception:
        pass
    await bot.add_cog(HelpCog(bot))
