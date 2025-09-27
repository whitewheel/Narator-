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
    "favor": "💠",
    "faction": "🏷️",
    "scene": "📍",
    "item": "📦",
    "inventory": "🎒",
    "equipment": "🛡️",
    "loot": "🎁",
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
    ("favor", "Favor"),
    ("faction", "Faction"),
    ("scene", "Scene / Zone"),
    ("item", "Items"),
    ("inventory", "Inventory"),
    ("equipment", "Equipment"),
    ("loot", "Loot"),
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
        "• 🌍 World: Quest, NPC, Favor, Faction, Scene, Items, Inventory, Equipment, Loot, Timeline, Wiki, Class/Race\n"
        "• 🧰 Utility: Roll, Poll, Multi, Ask (GPT)\n"
        "• 🎭 GM Only: Command rahasia GM"
    )
    e.set_footer(text="Tip: ketik !help <kategori> untuk detail, contoh: !help quest")
    return e

def embed_core() -> discord.Embed:
    e = _embed_base(_title("core", "Core Commands"), color=discord.Color.from_rgb(255, 99, 132))
    e.add_field(
        name=_title("status", "Karakter"),
        value=(
            "`!status set <Nama> <HP> <EN> <ST>` • `!status show [Nama]`\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>`\n"
            "`!status setcarry <Nama> <Capacity>`\n"
            "`!status dmg|heal <Nama> <Jumlah>` • `!party`\n"
            "`!status equip <Nama> <Slot> <Item>` • `!status unequip <Nama> <Slot>`\n"
            "Alias: `!hp <Nama>` • `!ene <Nama>` • `!stam <Nama>`"
        ),
        inline=False
    )
    return e

def embed_status() -> discord.Embed:
    e = _embed_base(_title("status", "Status (Karakter)"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Profil & Setup",
        value=(
            "`!status set <Nama> <HP> <EN> <ST>`\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>` • `!status setcarry <Nama> <Capacity>`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Progress",
        value=(
            "`!status dmg|heal <Nama> <Jumlah>`\n"
            "`!status addxp <Nama> <Jumlah>` • `!status addgold <Nama> <Jumlah>`\n"
            "`!status equip <Nama> <Slot> <Item>` • `!status unequip <Nama> <Slot>`\n"
            "Alias: `!hp <Nama>` • `!ene <Nama>` • `!stam <Nama>`\n"
            "`!party` (ringkasan party)"
        ),
        inline=False
    )
    e.add_field(
        name="Slot Equipment",
        value="`main_hand, off_hand, armor_inner, armor_outer, accessory1-3, augment1-3`",
        inline=False
    )
    return e

def embed_enemy() -> discord.Embed:
    e = _embed_base(_title("enemy", "Enemy Commands"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!enemy add <Nama> <HP> <EN> <ST> [--xp X] [--gold G] [--loot ...]`\n"
            "`!enemy show [Nama]` • `!enemy gmshow [Nama]`\n"
            "`!enemy reveal <OldName> <NewName>`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Efek",
        value=(
            "`!enemy dmg|heal <Nama> <Jumlah>`\n"
            "`!enemy buff|debuff <Nama> <Teks>`\n"
            "`!enemy clearbuff <Nama>` • `!enemy cleardebuff <Nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="Loot & Reward",
        value=(
            "`!enemy loot <Enemy> <Char>` → drop loot ke karakter\n"
            "`!enemy reward <Enemy> <Char>` → berikan XP/Gold ke karakter"
        ),
        inline=False
    )
    e.set_footer(text="Player hanya melihat kondisi musuh, GM punya detail HP/EN/ST.")
    return e

def embed_ally() -> discord.Embed:
    e = _embed_base(_title("ally", "Ally Commands"), color=discord.Color.from_rgb(100, 200, 100))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!ally add <Nama> <HP> <EN> <ST> [AC]`\n"
            "`!ally show [Nama]` (player view)\n"
            "`!ally gmshow [Nama]` (GM view detail)"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Efek",
        value=(
            "`!ally dmg|heal <Nama> <Jumlah>`\n"
            "`!ally buff|debuff <Nama> <Teks>`\n"
            "`!ally clearbuff <Nama>` • `!ally cleardebuff <Nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="Kelola",
        value="`!ally remove <Nama>` • `!ally clear`",
        inline=False
    )
    return e

def embed_gm() -> discord.Embed:
    e = _embed_base(_title("gm", "GM Commands"), color=discord.Color.from_rgb(200, 50, 200))
    e.add_field(
        name="Enemy Shortcuts",
        value="`!edmg <Enemy> <N>` • `!eheal <Enemy> <N>`\n"
              "`!ebuff <Enemy> <Text>` • `!edebuff <Enemy> <Text>`",
        inline=False
    )
    e.add_field(
        name="Ally Shortcuts",
        value="`!admg <Ally> <N>` • `!aheal <Ally> <N>`\n"
              "`!abuff <Ally> <Text>` • `!adebuff <Ally> <Text>`",
        inline=False
    )
    e.add_field(
        name="Utility GM",
        value="`!enemy reward <Enemy> <Char>` • `!enemy reveal <Old> <New>`\n"
              "`!ally clear` • `!enemy clear`",
        inline=False
    )
    e.set_footer(text="⚠️ Command ini hanya untuk GM, jangan dishare ke player.")
    return e

def embed_init() -> discord.Embed:
    e = _embed_base(_title("init", "Initiative Commands"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Urutan & Kontrol",
        value=(
            "`!init add <Nama> <Skor>` • `!init addmany \"Alice 18, Goblin 12\"`\n"
            "`!init show` • `!init next` • `!init setptr <index>`\n"
            "`!init remove <Nama>` • `!init clear` • `!init shuffle`\n"
            "`!init round [n]` • `!engage` • `!victory [keep] [force]`"
        ),
        inline=False
    )
    return e

def embed_tick() -> discord.Embed:
    e = _embed_base(_title("tick", "Tick Effects"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Kurangi Durasi Buff/Debuff",
        value="`!tick` → tampilkan expired & sisa durasi semua efek.",
        inline=False
    )
    return e

def embed_world() -> discord.Embed:
    e = _embed_base(_title("world", "World Commands"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="📜 Quest",
        value="`!quest add|show|gmshow|showarchived|detail|assign|reward|rewardvisible|reveal|complete|fail|archive`",
        inline=False
    )
    e.add_field(name="👤 NPC", value="`!npc add|list|favor|reveal|detail|sync|remove`", inline=False)
    e.add_field(
        name="💠 Favor",
        value="`!favor add|set|mod|show|detail|remove|player|factions|gmshow`",
        inline=False
    )
    e.add_field(
        name="🏷️ Faction",
        value="`!faction add|list|gmshow|detail|remove|hide|type`",
        inline=False
    )
    e.add_field(name="📍 Scene", value="`!scene create|edit|pin|unpin|show|now`", inline=False)
    e.add_field(name="🧰 Items & Inventory", value="`!item ...` • `!inv ...` • `!status equip ...`", inline=False)
    e.add_field(name="🎁 Loot", value="`!loot list|take|takeall|drop`", inline=False)
    e.add_field(name="⏳ Timeline", value="`!timeline add|search|full`", inline=False)
    e.add_field(name="📚 Wiki", value="`!wiki list|get|add|remove`", inline=False)
    e.add_field(name="🧑‍🎓 Class & Race", value="`!classinfo|!setclass` • `!raceinfo|!setrace`", inline=False)
    return e

def embed_quest() -> discord.Embed:
    e = _embed_base(_title("quest", "Quest Commands"), color=discord.Color.from_rgb(255, 205, 86))
    e.add_field(
        name="Kelola Quest",
        value=(
            "`!quest add <Nama> | <Deskripsi> [--hidden]`\n"
            "`!quest show [Nama]` • `!quest gmshow` • `!quest showarchived`\n"
            "`!quest detail <Nama>` • `!quest assign <Quest> <Char1,Char2>`\n"
            "`!quest reward <Quest> xp=100 gold=50 items=\"Potion x2; Key x1\" favor=\"Khaj:+2\"`\n"
            "`!quest rewardvisible <Quest> on/off`\n"
            "`!quest reveal <Quest>` • `!quest complete <Quest>` • `!quest fail <Quest>` • `!quest archive <Quest>`"
        ),
        inline=False
    )
    return e

def embed_npc() -> discord.Embed:
    e = _embed_base(_title("npc", "NPC Commands"), color=discord.Color.from_rgb(255, 99, 132))
    e.add_field(
        name="Kelola NPC",
        value=( 
            "`!npc add <Nama> [Role]` • `!npc list`\n"
            "`!npc favor <Nama> <delta>` • `!npc reveal <Nama> <trait>`\n"
            "`!npc detail <Nama>` • `!npc sync` • `!npc remove <Nama>`"
        ),
        inline=False
    )
    return e

def embed_favor() -> discord.Embed:
    e = _embed_base(_title("favor", "Favor / Faction"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Favor Commands",
        value=(
            "`!favor add|set <Faction> <value> [notes]`\n"
            "`!favor mod <Faction> <+/-N> [notes]`\n"
            "`!favor show` • `!favor detail <Faction>` • `!favor remove <Faction>`\n"
            "`!favor player <Nama>` • `!favor factions [Nama]`\n"
            "`!favor gmshow` (admin only)"
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
            "`!faction list` • `!faction gmshow`\n"
            "`!faction detail <Nama>` • `!faction remove <Nama>`\n"
            "`!faction hide <Nama> on/off` • `!faction type <Nama> <Type>`"
        ),
        inline=False
    )
    return e

def embed_scene() -> discord.Embed:
    e = _embed_base(_title("scene", "Scene / Zone"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Scene Commands",
        value=( 
            "`!scene create <Nama> | <Deskripsi> | [Factions] | [Danger]`\n"
            "`!scene edit <Nama> | field=value`\n"
            "`!scene pin` • `!scene unpin` • `!scene show` • `!scene now`"
        ),
        inline=False
    )
    return e

def embed_item() -> discord.Embed:
    e = _embed_base(_title("item", "Items"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Item Master",
        value=( 
            "`!item add <Nama> | <Slot> | <Type> | <Deskripsi>`\n"
            "`!item list` • `!item detail <Nama>` • `!item remove <Nama>`"
        ),
        inline=False
    )
    return e

def embed_inventory() -> discord.Embed:
    e = _embed_base(_title("inventory", "Inventory"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Per-Character Inventory",
        value=( 
            "`!inv add <Char> <Item> [qty]`\n"
            "`!inv remove <Char> <Item> [qty]`\n"
            "`!inv show <Char>` • `!inv party`"
        ),
        inline=False
    )
    return e

def embed_equipment() -> discord.Embed:
    e = _embed_base(_title("equipment", "Equipment"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Equip / Unequip",
        value=( 
            "`!status equip <Nama> <Slot> <Item>` • `!status unequip <Nama> <Slot>`\n"
            "Slot: `main_hand, off_hand, armor_inner, armor_outer, accessory1-3, augment1-3`"
        ),
        inline=False
    )
    return e

def embed_loot() -> discord.Embed:
    e = _embed_base(_title("loot", "Loot Commands"), color=discord.Color.from_rgb(255, 206, 86))
    e.add_field(
        name="Loot Commands",
        value=( 
            "`!loot list <Enemy>` • `!loot take <Enemy> <Item> <Char>`\n"
            "`!loot takeall <Enemy> <Char>` • `!loot drop <Enemy>`"
        ),
        inline=False
    )
    return e

def embed_timeline() -> discord.Embed:
    e = _embed_base(_title("timeline", "Timeline"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Timeline Commands",
        value=( 
            "`!timeline add CODE | Judul | Detail`\n"
            "`!timeline [N]` → tampilkan N event terakhir\n"
            "`!timeline search <keyword>` • `!timeline full`"
        ),
        inline=False
    )
    return e

def embed_wiki() -> discord.Embed:
    e = _embed_base(_title("wiki", "Wiki Commands"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Wiki Commands",
        value=( 
            "`!wiki list <Category>` • `!wiki get <Category> <Name>`\n"
            "`!wiki add <Category> <Name> | <Content>` • `!wiki remove <id>`"
        ),
        inline=False
    )
    return e

def embed_classrace() -> discord.Embed:
    e = _embed_base(_title("classrace", "Class & Race"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Class & Race",
        value=( 
            "`!classinfo <Name>` • `!setclass <Char> <ClassName>`\n"
            "`!raceinfo <Name>` • `!setrace <Char> <RaceName>`"
        ),
        inline=False
    )
    return e

def embed_utility() -> discord.Embed:
    e = _embed_base(_title("utility", "Utility"), color=discord.Color.from_rgb(100, 100, 100))
    e.add_field(name=_title("roll", "Roll"), value="`!roll 2d20+5` • `!roll as <Char> d20+str vs 14`", inline=False)
    e.add_field(name=_title("poll", "Poll"), value="`!poll \"Judul\" | Opsi A | Opsi B`", inline=False)
    e.add_field(name=_title("multi", "Multi-Command"), value="`!multi \"!dmg Goblin 3; !heal Alice 4\"`", inline=False)
    e.add_field(name=_title("ask", "GPT Ask"), value="`!ask Tulis deskripsi cyberpunk Baturaja.`", inline=False)
    return e

# Map kategori → builder
EMBED_BUILDERS = {
    "home": lambda g=None: embed_home(g),
    "core": embed_core,
    "status": embed_status,
    "enemy": embed_enemy,
    "ally": embed_ally,
    "gm": embed_gm,
    "init": embed_init,
    "tick": embed_tick,

    "world": embed_world,
    "quest": embed_quest,
    "npc": embed_npc,
    "favor": embed_favor,
    "faction": embed_faction,
    "scene": embed_scene,
    "item": embed_item,
    "inventory": embed_inventory,
    "equipment": embed_equipment,
    "loot": embed_loot,
    "timeline": embed_timeline,
    "wiki": embed_wiki,
    "classrace": embed_classrace,

    "utility": embed_utility,
    "roll": lambda: embed_utility(),
    "poll": lambda: embed_utility(),
    "multi": lambda: embed_utility(),
    "ask": lambda: embed_utility(),
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
