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
COLOR_WORLD     = discord.Color.teal()

# ========= EMBED BUILDERS =========

def embed_overview(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📖 Bantuan Bot",
        description=(
            "Selamat datang! Pilih topik bantuan dengan mengetik:\n"
            f"`{prefix}help init` • `{prefix}help status` • `{prefix}help enemy` • `{prefix}help dice`\n"
            f"`{prefix}help quick` • `{prefix}help poll` • `{prefix}help gpt`\n"
            f"`{prefix}help quest` • `{prefix}help item` • `{prefix}help npc` • `{prefix}help favor` • `{prefix}help scene`\n"
            f"`{prefix}help timeline` • `{prefix}help wiki` • `{prefix}help class` • `{prefix}help race` • `{prefix}help loot`\n\n"
            f"Gunakan `{prefix}help <topik>` untuk detail."
        ),
        color=COLOR_OVERVIEW,
        timestamp=datetime.datetime.utcnow()
    )
    # Core play
    e.add_field(name="🧍 Karakter Status", value="Kelola HP/Energy/Stamina, core stat, buff/debuff, ringkasan `!party`.", inline=False)
    e.add_field(name="👾 Enemy Status", value="Tambah musuh, AoE `dmg/heal [all]`, buff/debuff, tick.", inline=False)
    e.add_field(name="⚔️ Initiative", value="Urutan giliran, `addmany`, `next`, `setptr`, `round`, `shuffle`.", inline=False)
    e.add_field(name="🎲 Dice Roller", value="`roll`/`r`, dukung `as <Nama>`, `+str|dex|…`, `dc|vs`.", inline=False)
    e.add_field(name="⚡ Quick & Utility", value="Alias cepat: `dmg/heal/ene±/stam±`, `party`, `undo`, `multi`, `order`, `victory`.", inline=False)
    # World systems
    e.add_field(name="📜 Quest", value="Tambah, show, detail, assign, reward, reveal, complete, fail.", inline=False)
    e.add_field(name="👤 NPC", value="Tambah/show/detail, `--hidden`, reveal/remove.", inline=False)
    e.add_field(name="🧰 Item", value="Item library & inventory: add/show/detail/remove, `use` item.", inline=False)
    e.add_field(name="🎁 Loot", value="Kelola loot musuh: list/take/takeall/drop.", inline=False)
    e.add_field(name="🪙 Favor", value="Reputasi fraksi: add/set/show/detail/remove.", inline=False)
    e.add_field(name="📍 Scene", value="Pin & tampilkan lokasi/scene aktif kanal.", inline=False)
    e.add_field(name="⏳ Timeline", value="Catat & cari event kronologis.", inline=False)
    e.add_field(name="📚 Wiki", value="Entri lore dunia, add/show/detail/remove.", inline=False)
    e.add_field(name="🧑‍🎓 Class & Race", value="Info class/ras, `setclass`, `setrace`.", inline=False)
    # Misc
    e.add_field(name="📊 Polling", value="Voting cepat dengan reaction angka.", inline=False)
    e.add_field(name="🧠 GPT", value="Define, summarize, dan story (narasi).", inline=False)
    e.set_footer(text=f"Contoh: {prefix}help quest • {prefix}help loot • {prefix}help wiki")
    return e

def embed_init(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Bantuan: Initiative",
        description="Kelola urutan giliran (turn order) untuk encounter.",
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
            f"- `{prefix}init addmany` *(tambah banyak sekaligus)*\n"
            f"- `{prefix}init setptr <index>` • `{prefix}init next`\n"
            f"- `{prefix}init round [n]` *(lihat/set ronde)* • `{prefix}init shuffle` *(acak urutan)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Utility",
        value=(
            f"- `!order` → tampilkan urutan\n"
            f"- `!victory` → akhiri encounter"
        ),
        inline=False
    )
    return e

def embed_status(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧍 Bantuan: Status",
        description="Kelola karakter: HP, Energy, Stamina, core stat, buff/debuff, equipment.",
        color=COLOR_STATUS,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}status set <Nama> <HP> <Energy> <Stamina>`\n"
            f"- `{prefix}status show [Nama]` • `{prefix}status remove <Nama>`\n"
            f"- `!party` *(ringkasan party)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Efek",
        value=(
            f"- `{prefix}status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            f"- `{prefix}status buff|debuff <Nama> <efek> [durasi|perm]`\n"
            f"- `{prefix}status unbuff|undebuff <Nama> <efek>`\n"
            f"- `{prefix}status clearbuff|cleardebuff <Nama>` • `{prefix}status tick` *(kurangi durasi efek)*"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Level & Progression",
        value=(
            f"- `{prefix}status setlevel <Nama> <Level>`\n"
            f"- `{prefix}status addxp <Nama> <jumlah>`\n"
            f"- `{prefix}status addgold <Nama> <jumlah>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Combat",
        value=(
            f"- `{prefix}status setac <Nama> <AC>`\n"
            f"- `{prefix}status dmg <Nama> <jumlah>`\n"
            f"- `{prefix}status heal <Nama> <jumlah>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Equipment",
        value=(
            f"- `{prefix}status equip <Nama> <slot> <item>`\n"
            f"Slot: main_hand, off_hand, armor_inner, armor_outer, accessory1, accessory2"
        ),
        inline=False
    )
    return e

def embed_enemy(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👾 Bantuan: Enemy",
        description="Kelola musuh: tambah, core, buff/debuff, AoE.",
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
            f"- `{prefix}enemy addmany Goblin 15 0 10 x2, Archer 10 3 10 x1`\n"
            f"- Atau multiline: satu baris per enemy"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Core & Efek",
        value=(
            f"- `{prefix}enemy setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            f"- `{prefix}enemy buff|debuff <Nama> <efek> [durasi|perm]`\n"
            f"- `{prefix}enemy unbuff|undebuff <Nama> <efek>`\n"
            f"- `{prefix}enemy clearbuff|cleardebuff <Nama>`\n"
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
        description="Alias cepat untuk aksi status/enemy & utilitas.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Alias",
        value=(
            f"- `!dmg <Nama> <jumlah> [all]` • `!heal <Nama> <jumlah> [all]`\n"
            f"- `!ene- <Nama> <jumlah>` • `!ene+ <Nama> <jumlah>`\n"
            f"- `!stam- <Nama> <jumlah>` • `!stam+ <Nama> <jumlah>`\n"
            f"- `!party` • `!undo` • `!multi` • `!order` • `!victory`"
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
        value=f"- `{prefix}poll \"Makan apa?\" Nasi Mie Roti`",
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
            f"- `{prefix}ask <prompt>` → tanya GPT\n"
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
        description="Kelola quest dengan status, assignment, dan reward.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Dasar",
        value=(
            f"- `{prefix}quest add Nama | Deskripsi | [--hidden]`\n"
            f"- `{prefix}quest show [active|hidden|all|complete|failed]`\n"
            f"- `{prefix}quest detail <Nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Lanjutan",
        value=(
            f"- `{prefix}quest assign <Quest> <Char1,Char2,...>`\n"
            f"- `{prefix}quest reward <Quest> xp=100 gold=50 items=\"Potion x2\" favor=Faction:+10`\n"
            f"- `{prefix}quest reveal <Quest>` → ubah status ke active\n"
            f"- `{prefix}quest complete <Quest> [to=Aima,Zarek]`\n"
            f"- `{prefix}quest fail <Quest>`"
        ),
        inline=False
    )
    return e

def embed_item(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧰 Bantuan: Item",
        description="Kelola item library & inventory.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Library",
        value=(
            f"- `{prefix}item add <nama> | <type> | <efek> | [rarity]`\n"
            f"- `{prefix}item show`\n"
            f"- `{prefix}item detail <nama>`\n"
            f"- `{prefix}item remove <nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Inventory & Use",
        value=(
            f"- `{prefix}inv show <Char>`\n"
            f"- `{prefix}inv add <Char> | <Item> xN`\n"
            f"- `{prefix}inv remove <Char> | <Item>`\n"
            f"- `{prefix}use <Char> <Item>`"
        ),
        inline=False
    )
    return e

def embed_loot(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🎁 Bantuan: Loot",
        description="Kelola loot dari musuh setelah combat.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}loot list <Enemy>`\n"
            f"- `{prefix}loot take <Enemy> <Item> <Char>`\n"
            f"- `{prefix}loot takeall <Enemy> <Char>`\n"
            f"- `{prefix}loot drop <Enemy>`"
        ),
        inline=False
    )
    return e

def embed_npc(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="👤 Bantuan: NPC",
        description="Kelola NPC dunia (ally, enemy, neutral).",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}npc add <nama> | <peran> | [sikap] | [catatan] [--hidden]`\n"
            f"- `{prefix}npc show`\n"
            f"- `{prefix}npc detail <nama>`\n"
            f"- `{prefix}npc reveal <nama>`\n"
            f"- `{prefix}npc remove <nama>`"
        ),
        inline=False
    )
    return e

def embed_favor(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🪙 Bantuan: Favor",
        description="Kelola reputasi & hubungan dengan fraksi.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}favor add|set <faksi> | <nilai> | [catatan]`\n"
            f"- `{prefix}favor show`\n"
            f"- `{prefix}favor detail <faksi>`\n"
            f"- `{prefix}favor remove <faksi>`"
        ),
        inline=False
    )
    return e

def embed_scene(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📍 Bantuan: Scene",
        description="Pin & tampilkan scene/lokasi aktif di kanal.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}scene pin` → pin scene terakhir\n"
            f"- `{prefix}scene unpin`\n"
            f"- `{prefix}scene show`\n"
            f"- `{prefix}scene now` *(alias cepat)*"
        ),
        inline=False
    )
    return e

def embed_timeline(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⏳ Bantuan: Timeline",
        description="Catat event kronologis di kanal.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}timeline [N]` → tampilkan N event terakhir\n"
            f"- `{prefix}timeline add CODE | Judul | detail`\n"
            f"- `{prefix}timeline full`\n"
            f"- `{prefix}timeline search <keyword>`"
        ),
        inline=False
    )
    return e

def embed_wiki(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="📚 Bantuan: Wiki",
        description="Kelola entri lore/world di wiki.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}wiki list <Category>`\n"
            f"- `{prefix}wiki get <Category> <Name>`\n"
            f"- `{prefix}wiki add <Category> <Name> | <Content>`\n"
            f"- `{prefix}wiki remove <id>`"
        ),
        inline=False
    )
    return e

def embed_classrace(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="🧑‍🎓 Bantuan: Class & Race",
        description="Kelola class & race karakter.",
        color=COLOR_WORLD,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Command",
        value=(
            f"- `{prefix}classinfo <Nama>` → lihat detail class\n"
            f"- `{prefix}setclass <Char> <ClassName>`\n"
            f"- `{prefix}raceinfo <Nama>` → lihat detail ras\n"
            f"- `{prefix}setrace <Char> <RaceName>`"
        ),
        inline=False
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
        elif key in ("gpt", "ai", "ask"):
            embed = embed_gpt(prefix)
        elif key in ("quest",):
            embed = embed_quest(prefix)
        elif key in ("item", "inventory", "inv", "use"):
            embed = embed_item(prefix)
        elif key in ("loot",):
            embed = embed_loot(prefix)
        elif key in ("npc",):
            embed = embed_npc(prefix)
        elif key in ("favor", "rep", "reputation"):
            embed = embed_favor(prefix)
        elif key in ("scene", "zone"):
            embed = embed_scene(prefix)
        elif key in ("timeline", "log"):
            embed = embed_timeline(prefix)
        elif key in ("wiki", "lore"):
            embed = embed_wiki(prefix)
        elif key in ("class", "race"):
            embed = embed_classrace(prefix)
        else:
            embed = embed_overview(prefix)

        await ctx.send(embed=embed)

async def setup(bot):
    bot.help_command = None
    try:
        bot.remove_command("help")
    except Exception:
        pass
    await bot.add_cog(HelpCog(bot))
