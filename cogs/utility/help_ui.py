import discord
from discord.ext import commands

# ===============================
#  HELP UI – Cute & Useful
# ===============================

CATEGORY_EMOJI = {
    "home": "📚",
    "core": "⚔️",
    "status": "🧍",
    "enemy": "👹",
    "ally": "🤝",
    "init": "⏱️",
    "tick": "⏳",

    "world": "🌍",
    "quest": "📜",
    "npc": "🧑‍🤝‍🧑",
    "shop": "🏪",
    "favor": "💠",
    "faction": "🏷️",
    "scene": "📍",
    "item": "📦",
    "inventory": "🎒",
    "equipment": "🛡️",
    "timeline": "⏳",
    "wiki": "📚",
    "classrace": "🧑‍🎓",

    "utility": "🧰",
    "roll": "🎲",
    "poll": "📊",
    "multi": "🗂️",
    "ask": "🤖",

    "gm": "🎭",
}

CATEGORIES = [
    ("home", "Overview"),
    ("core", "Core (Ringkasan)"),
    ("status", "Status (Karakter)"),
    ("enemy", "Enemy"),
    ("ally", "Ally"),
    ("init", "Initiative"),
    ("tick", "Tick Effects"),

    ("world", "World (Ringkasan)"),
    ("quest", "Quest"),
    ("npc", "NPC"),
    ("shop", "Shop / Merchant"),
    ("favor", "Favor"),
    ("faction", "Faction"),
    ("scene", "Scene / Zone"),
    ("item", "Items"),
    ("inventory", "Inventory"),
    ("equipment", "Equipment"),
    ("timeline", "Timeline"),
    ("wiki", "Wiki"),
    ("classrace", "Class & Race"),

    ("utility", "Utility"),
    ("gm", "GM Only"),
]

def _title(icon_key: str, label: str) -> str:
    return f"{CATEGORY_EMOJI.get(icon_key,'📦')}  {label}"

def _embed_base(title: str, desc: str = "", color: discord.Color = discord.Color.blurple()):
    return discord.Embed(title=title, description=desc, color=color)

# ===============================
#  EMBED BUILDERS
# ===============================

def embed_home(guild: discord.Guild) -> discord.Embed:
    e = _embed_base(
        _title("home", "Narator Help – Ringkasan"),
        "Selamat datang di **Narator Bot**! 🎭\n\n"
        "Gunakan **dropdown** di bawah untuk memilih kategori bantuan.\n"
        "Ikon di kiri bikin gampang diingat 😸\n\n"
        "**Kategori Utama:**\n"
        "• ⚔️ Core: Status, Enemy, Ally, Initiative, Tick\n"
        "• 🌍 World: Quest, NPC, Shop, Favor, Faction, Scene, Items, Inventory, Equipment, Timeline, Wiki, Class/Race\n"
        "• 🧰 Utility: Roll, Poll, Multi, Ask (GPT)\n"
        "• 🎭 GM Only: Command rahasia GM"
    )
    e.set_footer(text="Tip: ketik !help <kategori> untuk detail, contoh: !help quest")
    return e

def embed_status() -> discord.Embed:
    e = _embed_base(_title("status", "Status (Karakter)"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Profil & Setup",
        value=(
            "`!status set <Nama> <HP> <EN> <ST>`\n"
            "Contoh: `!status set Udab 20 10 15`\n\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "Contoh: `!status setcore Udab 14 12 13 10 8 9`\n\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "Contoh: `!status setclass Udab Warrior`\n"
            "Contoh: `!status setrace Udab Human`\n\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>`\n"
            "Contoh: `!status setlevel Udab 3`\n"
            "Contoh: `!status setac Udab 14`\n\n"
            "`!status setcarry <Nama> <Capacity>`\n"
            "Contoh: `!status setcarry Udab 25`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Progress",
        value=(
            "`!status dmg <Nama> <Jumlah>` • `!status heal <Nama> <Jumlah>`\n"
            "Contoh: `!status dmg Udab 5`\n"
            "Contoh: `!status heal Udab 3`\n\n"
            "`!status addxp <Nama> <Jumlah>` • `!status subxp <Nama> <Jumlah>`\n"
            "Contoh: `!status addxp Udab 100`\n"
            "Contoh: `!status subxp Udab 50`\n\n"
            "`!status addgold <Nama> <Jumlah>` • `!status subgold <Nama> <Jumlah>`\n"
            "Contoh: `!status addgold Udab 50`\n"
            "Contoh: `!status subgold Udab 20`\n\n"
            "`!status addstm <Nama> <Jumlah>` • `!status usestm <Nama> <Jumlah>`\n"
            "Contoh: `!status addstm Udab 5`\n"
            "Contoh: `!status usestm Udab 3`\n\n"
            "`!status addene <Nama> <Jumlah>` • `!status useene <Nama> <Jumlah>`\n"
            "Contoh: `!status addene Udab 4`\n"
            "Contoh: `!status useene Udab 2`\n\n"
            "`!buff <Nama> <Teks>` • `!debuff <Nama> <Teks>`\n"
            "Contoh: `!buff Udab Bless +2 STR`\n"
            "Contoh: `!debuff Udab Poison -2 CON`\n\n"
            "`!party` → ringkasan party"
        ),
        inline=False
    )
    e.add_field(
        name="Remove",
        value="`!status remove <Nama>`\nContoh: `!status remove Udab`",
        inline=False
    )
    return e

def embed_enemy() -> discord.Embed:
    e = _embed_base(_title("enemy", "Enemy Commands"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!enemy add <Nama>`\n"
            "Contoh: `!enemy add Rustborn`\n\n"
            "`!enemy show [Nama]` • `!enemy gmshow [Nama]`\n"
            "`!enemy remove <Nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Efek",
        value=(
            "`!edmg <Nama> <Jumlah>` • `!eheal <Nama> <Jumlah>`\n"
            "Contoh: `!edmg Rustborn 7`\n\n"
            "`!ebuff <Nama> <Teks>` • `!edebuff <Nama> <Teks>`\n"
            "Contoh: `!ebuff Rustborn Rage +2 STR`"
        ),
        inline=False
    )
    e.add_field(
        name="Loot & Reward",
        value=(
            "`!enemy loot <Nama>`\n"
            "`!enemy reward <Nama>`\n"
            "Contoh: `!enemy reward Rustborn`"
        ),
        inline=False
    )
    return e

def embed_ally() -> discord.Embed:
    e = _embed_base(_title("ally", "Ally Commands"), color=discord.Color.from_rgb(100, 200, 100))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!ally add <Nama>`\n"
            "Contoh: `!ally add Nyx`\n\n"
            "`!ally show [Nama]` • `!ally gmshow [Nama]`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Efek",
        value=(
            "`!admg <Nama> <Jumlah>` • `!aheal <Nama> <Jumlah>`\n"
            "Contoh: `!admg Nyx 3`\n\n"
            "`!abuff <Nama> <Teks>` • `!adebuff <Nama> <Teks>`\n"
            "Contoh: `!abuff Nyx Haste +2 DEX`"
        ),
        inline=False
    )
    e.add_field(
        name="Kelola",
        value="`!ally remove <Nama>` • `!ally clear`",
        inline=False
    )
    return e

def embed_shop() -> discord.Embed:
    e = _embed_base(_title("shop", "Shop / Merchant"), color=discord.Color.from_rgb(240, 180, 50))
    e.add_field(
        name="Lihat Dagangan",
        value=(
            "`!shop list <NPC> [Char]` → lihat daftar item untuk player\n"
            "Contoh: `!shop list Ka'ruun Udab`\n\n"
            "`!shop gmlist <NPC>` → lihat versi lengkap (GM only)"
        ),
        inline=False
    )
    e.add_field(
        name="Kelola Dagangan",
        value=(
            "`!shop add <NPC> <Item> <Harga> [Stock]`\n"
            "Contoh: `!shop add Ka'ruun Antibiotik 50 3`\n\n"
            "`!shop remove <NPC> <Item>`\n"
            "Contoh: `!shop remove Ka'ruun Antibiotik`\n\n"
            "`!shop clear <NPC>` → hapus semua dagangan NPC"
        ),
        inline=False
    )
    e.add_field(
        name="Belanja",
        value=(
            "`!shop buy <NPC> <Char> <Item> [Qty]`\n"
            "Contoh: `!shop buy Ka'ruun Udab Antibiotik 1`\n\n"
            "💡 Item otomatis masuk ke inventory karakter.\n"
            "❌ Jika gold tidak cukup / carry overload → transaksi gagal."
        ),
        inline=False
    )
    e.add_field(
        name="Lock / Unlock",
        value=(
            "`!shop unlock <NPC> <Item> [favor=<Faction>:<Val>] [quest=<Quest>]`\n"
            "Contoh: `!shop unlock Ka'ruun Antibiotik favor=Mutaris:2 quest=Antibiotik`\n\n"
            "Item akan tampil sebagai terkunci (💰 - | Stock -) sampai syarat tercapai."
        ),
        inline=False
    )
    return e

def embed_gm() -> discord.Embed:
    e = _embed_base(_title("gm", "GM Commands"), color=discord.Color.from_rgb(200, 50, 200))
    e.add_field(
        name="History",
        value="`!undo` → batalkan aksi terakhir",
        inline=False
    )
    e.add_field(
        name="Enemy Shortcuts",
        value=(
            "`!edmg <Enemy> <N>`\n"
            "`!eheal <Enemy> <N>`\n"
            "`!ebuff <Enemy> <Text>`\n"
            "`!edebuff <Enemy> <Text>`"
        ),
        inline=False
    )
    e.add_field(
        name="Ally Shortcuts",
        value=(
            "`!admg <Ally> <N>`\n"
            "`!aheal <Ally> <N>`\n"
            "`!abuff <Ally> <Text>`\n"
            "`!adebuff <Ally> <Text>`"
        ),
        inline=False
    )
    return e

def embed_init() -> discord.Embed:
    e = _embed_base(_title("init", "Initiative Commands"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Urutan & Kontrol",
        value=(
            "`!init add <Nama> <Skor>`\n"
            "Contoh: `!init add Udab 15`\n\n"
            "`!init addmany \"Alice 18, Goblin 12\"`\n"
            "`!init show` • `!init next` • `!init setptr <index>`\n"
            "`!init remove <Nama>` • `!init clear` • `!init shuffle`\n"
            "`!init round [n]` • `!init engage` • `!init victory`"
        ),
        inline=False
    )
    return e

def embed_tick() -> discord.Embed:
    e = _embed_base(_title("tick", "Tick Effects"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Kurangi Durasi Buff/Debuff",
        value="`!tick` → kurangi durasi semua efek dan tampilkan expired.",
        inline=False
    )
    return e

def embed_quest() -> discord.Embed:
    e = _embed_base(_title("quest", "Quest Commands"), color=discord.Color.from_rgb(255, 205, 86))
    e.add_field(
        name="Kelola Quest",
        value=( 
            "`!quest add <Nama> | <Deskripsi>`\n"
            "Contoh: `!quest add Cari Antibiotik | Bantu Ka'ruun mencari antibiotik.`\n\n"
            "`!quest show` • `!quest gmshow` • `!quest showarchived`\n"
            "`!quest detail <Nama>`\n"
            "Contoh: `!quest detail Cari Antibiotik`\n\n"
            "`!quest assign <Quest> <Char1,Char2>`\n"
            "Contoh: `!quest assign Cari Antibiotik Udab,Nyx`\n\n"
            "`!quest reward <Quest> xp=100 gold=50 items=\"Potion x2; Key x1\" favor=\"Mutaris:+2\"`\n"
            "Contoh: `!quest reward Cari Antibiotik xp=200 gold=100 items=\"Antibiotik x1\" favor=\"Mutaris:+2\"`\n\n"
            "`!quest rewardvisible <Quest> on/off`\n"
            "`!quest reveal <Quest>` • `!quest complete <Quest>`\n"
            "`!quest fail <Quest>` • `!quest archive <Quest>`"
        ),
        inline=False
    )
    return e

def embed_npc() -> discord.Embed:
    e = _embed_base(_title("npc", "NPC Commands"), color=discord.Color.from_rgb(255, 99, 132))
    e.add_field(
        name="Kelola NPC",
        value=(
            "`!npc add <Nama> [Role]`\n"
            "Contoh: `!npc add Ka'ruun | Pemimpin Mutaris`\n\n"
            "`!npc list`\n"
            "`!npc detail <Nama>` • `!npc remove <Nama>` • `!npc sync`\n\n"
            "**Traits & Info:**\n"
            "`!npc trait_add <Nama> key=value`\n"
            "Contoh: `!npc trait_add Ka'ruun Bijak`\n\n"
            "`!npc trait_remove <Nama> <key>`\n"
            "`!npc reveal <Nama> <Trait>` • `!npc allreveal <Nama>`\n"
            "`!npc info <Nama> <Teks>`"
        ),
        inline=False
    )
    return e

def embed_favor() -> discord.Embed:
    e = _embed_base(_title("favor", "Favor / Faction"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Favor Commands",
        value=(
            "`!favor add <Char> <Faction> <Value>`\n"
            "Contoh: `!favor add Udab Mutaris 3`\n\n"
            "`!favor set <Char> <Faction> <Value>`\n"
            "`!favor mod <Char> <Faction> +/-N`\n"
            "Contoh: `!favor mod Udab Mutaris +2`\n\n"
            "`!favor show <Char>` • `!favor detail <Faction>`\n"
            "`!favor factions` • `!favor gmshow`"
        ),
        inline=False
    )
    return e

def embed_faction() -> discord.Embed:
    e = _embed_base(_title("faction", "Faction Commands"), color=discord.Color.from_rgb(255, 140, 0))
    e.add_field(
        name="Faction Master",
        value=(
            "`!faction add <Nama> | <Deskripsi> | [Type]`\n"
            "Contoh: `!faction add ArthaDyne | Korporasi biotek elit | corporate`\n\n"
            "`!faction list` • `!faction gmshow`\n"
            "`!faction detail <Nama>` • `!faction remove <Nama>`\n"
            "`!faction hide <Nama> on/off`\n"
            "`!faction type <Nama> <Type>`"
        ),
        inline=False
    )
    return e

def embed_scene() -> discord.Embed:
    e = _embed_base(_title("scene", "Scene / Zone"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Scene Commands",
        value=(
            "`!scene create <Nama> | <Deskripsi>`\n"
            "Contoh: `!scene create Sewer01 | Lorong bawah tanah berbau menyengat`\n\n"
            "`!scene edit <Nama> | field=value`\n"
            "Contoh: `!scene edit Sewer01 | danger=high`\n\n"
            "`!scene list` • `!scene recall <Nama>`\n"
            "`!scene pin <Nama>` • `!scene unpin`\n"
            "`!scene show <Nama>` • `!scene now`"
        ),
        inline=False
    )
    return e

def embed_item() -> discord.Embed:
    e = _embed_base(_title("item", "Items"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Item Master",
        value=(
            "`!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules]`\n"
            "Contoh: `!item add Rust Shiv | Weapon | Pisau karatan | Common | 0 | 1.0 | main_hand | Senjata awal | +1 dmg`\n\n"
            "`!item show all`\n"
            "`!item show weapon`\n\n"
            "`!item remove <Nama>`\n"
            "`!item detail <Nama>`\n"
            "`!item edit <Nama> | key=value`\n"
            "Contoh: `!item edit Rust Shiv | weight=1.2 rarity=Uncommon`\n\n"
            "`!item info <Nama>`\n"
            "`!use <Char> <Item>`\n"
            "Contoh: `!use Udab Rust Shiv`"
        ),
        inline=False
    )
    return e

def embed_inventory() -> discord.Embed:
    e = _embed_base(_title("inventory", "Inventory"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Inventory Commands",
        value=(
            "`!inv add <Char> <Item> [qty]`\n"
            "Contoh: `!inv add Udab Rust Shiv 1`\n\n"
            "`!inv remove <Char> <Item> [qty]`\n"
            "Contoh: `!inv remove Udab Rust Shiv 1`\n\n"
            "`!inv drop <Char> <Item> [qty]`\n"
            "`!inv clear <Char>`\n"
            "`!inv show <Char>`\n\n"
            "`!inv transfer <Char1> <Char2> <Item> [qty]`\n"
            "Contoh: `!inv transfer Udab Nyx Rust Shiv 1`\n\n"
            "`!inv meta <Char> <Item> key=value`\n"
            "Contoh: `!inv meta Udab Rust Shiv weight=1.0 rarity=Common`\n\n"
            "`!inv use <Char> <Item>`\n"
            "Contoh: `!inv use Udab Sample Antibiotik`\n\n"
            "`!inv recalc_all`"
        ),
        inline=False
    )
    return e

def embed_equipment() -> discord.Embed:
    e = _embed_base(_title("equipment", "Equipment"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Equip / Unequip",
        value=(
            "`!equip set <Char> <Slot> <Item>`\n"
            "Contoh: `!equip set Udab main_hand Rust Shiv`\n\n"
            "`!equip remove <Char> <Slot>`\n"
            "Contoh: `!equip remove Udab main_hand`\n\n"
            "`!equip show <Char>`\n"
            "Slot: `main_hand, off_hand, armor_inner, armor_outer, accessory1-3, augment1-3`"
        ),
        inline=False
    )
    return e

def embed_timeline() -> discord.Embed:
    e = _embed_base(_title("timeline", "Timeline"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Timeline Commands",
        value=(
            "`!timeline add <Teks>`\n"
            "Contoh: `!timeline add Udab bertemu Ka'ruun di Khaj`\n\n"
            "`!timeline search <keyword>`\n"
            "Contoh: `!timeline search Udab`\n\n"
            "`!timeline full`"
        ),
        inline=False
    )
    return e

def embed_wiki() -> discord.Embed:
    e = _embed_base(_title("wiki", "Wiki Commands"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Wiki Commands",
        value=(
            "`!wiki list`\n"
            "`!wiki get <Nama>`\n"
            "Contoh: `!wiki get Khaj`\n\n"
            "`!wiki add <Nama> | <Konten>`\n"
            "Contoh: `!wiki add Khaj | Wilayah bawah tanah Mutaris.`\n\n"
            "`!wiki remove <Nama>`\n"
            "Contoh: `!wiki remove Khaj`"
        ),
        inline=False
    )
    return e

def embed_classrace() -> discord.Embed:
    e = _embed_base(_title("classrace", "Class & Race"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Class & Race",
        value=(
            "`!classinfo <Name>`\n"
            "Contoh: `!classinfo Rustborn`\n\n"
            "`!setclass <Char> <ClassName>`\n"
            "Contoh: `!setclass Udab Warrior`\n\n"
            "`!raceinfo <Name>`\n"
            "Contoh: `!raceinfo Exoform`\n\n"
            "`!setrace <Char> <RaceName>`\n"
            "Contoh: `!setrace Udab Human`"
        ),
        inline=False
    )
    return e

def embed_utility() -> discord.Embed:
    e = _embed_base(_title("utility", "Utility"), color=discord.Color.from_rgb(100, 100, 100))
    e.add_field(name=_title("roll", "Roll"), value="`!roll 1d20+3`\nContoh: `!roll 2d6+4`", inline=False)
    e.add_field(name=_title("poll", "Poll"), value="`!poll \"Judul\" opsi1 opsi2`\nContoh: `!poll \"Pilih jalan\" kiri kanan`", inline=False)
    e.add_field(name=_title("multi", "Multi-Command"), value="`!multi !dmg Goblin 3 x3`", inline=False)
    e.add_field(name=_title("ask", "GPT Ask"), value="`!ask Ceritakan tentang Technonesia`", inline=False)
    return e

# Map kategori → builder
EMBED_BUILDERS = {
    "home": lambda g=None: embed_home(g),
    "status": embed_status,
    "enemy": embed_enemy,
    "ally": embed_ally,
    "shop": embed_shop,
    "gm": embed_gm,
    "init": embed_init,
    "tick": embed_tick,
    "quest": embed_quest,
    "npc": embed_npc,
    "favor": embed_favor,
    "faction": embed_faction,
    "scene": embed_scene,
    "item": embed_item,
    "inventory": embed_inventory,
    "equipment": embed_equipment,
    "timeline": embed_timeline,
    "wiki": embed_wiki,
    "classrace": embed_classrace,
    "utility": embed_utility,
}

# ===============================
#  INTERACTIVE VIEW
# ===============================

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=key, emoji=CATEGORY_EMOJI.get(key, "📦"))
            for key, label in CATEGORIES
        ]
        super().__init__(placeholder="Pilih kategori bantuan…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        builder = EMBED_BUILDERS.get(key, embed_home)
        embed = builder(interaction.guild) if key == "home" else builder()
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpNav(discord.ui.View):
    def __init__(self, author_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.add_item(HelpSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

# ===============================
#  COG
# ===============================

class HelpUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _embed_for_key(self, key: str, guild: discord.Guild):
        builder = EMBED_BUILDERS.get(key, embed_home)
        return builder(guild) if key == "home" else builder()

    @commands.group(name="help", invoke_without_command=True)
    async def help_group(self, ctx, *, category: str = None):
        if category:
            key = category.strip().lower()
            embed = self._embed_for_key(key, ctx.guild)
            return await ctx.send(embed=embed)

        view = HelpNav(ctx.author.id)
        embed = embed_home(ctx.guild)
        await ctx.send(embed=embed, view=view)

    @help_group.command(name="ui")
    async def help_ui(self, ctx):
        view = HelpNav(ctx.author.id)
        await ctx.send(embed=embed_home(ctx.guild), view=view)

    @commands.command(name="commands")
    async def list_all_commands(self, ctx):
        names = sorted(c.qualified_name for c in self.bot.commands)
        chunks, current = [], ""
        for n in names:
            if len(current) + len(n) + 2 > 1900:
                chunks.append(current)
                current = ""
            current += (n + ", ")
        if current: chunks.append(current)

        for i, ch in enumerate(chunks, 1):
            e = discord.Embed(
                title=f"🧰 Daftar Commands ({i}/{len(chunks)})",
                description=ch.rstrip(", "),
                color=discord.Color.dark_teal(),
            )
            await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(HelpUI(bot))
