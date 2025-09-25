# cogs/utility/help_ui.py
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
    "init": "⏱️",
    "tick": "⏳",

    "world": "🌍",
    "quest": "📜",
    "npc": "🧑‍🤝‍🧑",
    "favor": "🪙",
    "scene": "📍",
    "item": "📦",
    "inventory": "🎒",
    "equipment": "🛡️",

    "utility": "🧰",
    "roll": "🎲",
    "poll": "📊",
    "multi": "🗂️",
    "ask": "🤖",
}

CATEGORIES = [
    ("home", "Overview"),
    ("core", "Core (Ringkasan)"),
    ("status", "Status (Karakter)"),
    ("enemy", "Enemy"),
    ("init", "Initiative"),
    ("tick", "Tick Effects"),

    ("world", "World (Ringkasan)"),
    ("quest", "Quest"),
    ("npc", "NPC"),
    ("favor", "Favor / Faction"),
    ("scene", "Scene / Zone"),
    ("item", "Items"),
    ("inventory", "Inventory"),
    ("equipment", "Equipment"),

    ("utility", "Utility"),
    ("roll", "Roll"),
    ("poll", "Poll"),
    ("multi", "Multi-Command"),
    ("ask", "GPT Ask"),
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
        "Selamat datang! Pilih kategori lewat **dropdown** di bawah.\n"
        "Ikon di kiri memudahkan kamu mengingat fungsinya 😸\n\n"
        "**Kategori Utama:**\n"
        "• ⚔️ Core: Status, Enemy, Initiative, Tick\n"
        "• 🌍 World: Quest, NPC, Favor, Scene, Items, Inventory, Equipment\n"
        "• 🧰 Utility: Roll, Poll, Multi, Ask (GPT)\n"
    )
    e.add_field(
        name=_title("core", "Core (Ringkasan)"),
        value=(
            "`!status ...` • `!enemy ...` • `!init ...` • `!tick`\n"
            "`!dmg|!heal|!ene±|!stam±` (alias cepat)\n"
        ),
        inline=False
    )
    e.add_field(
        name=_title("world", "World (Ringkasan)"),
        value=(
            "`!quest ...` • `!npc ...` • `!favor ...`\n"
            "`!scene ...` • `!item ...` • `!inv ...` • `!status equip ...`\n"
        ),
        inline=False
    )
    e.add_field(
        name=_title("utility", "Utility"),
        value="`!roll` • `!poll` • `!multi` • `!ask`",
        inline=False
    )
    e.set_footer(text="Tip: ketik !help <kategori> untuk bantuan spesifik, misal: !help quest")
    return e

def embed_core() -> discord.Embed:
    e = _embed_base(_title("core", "Core Commands"), color=discord.Color.from_rgb(255, 99, 132))
    e.add_field(
        name=_title("status", "Karakter"),
        value=(
            "**Set & Info**\n"
            "`!status` → Tampilkan semua\n"
            "`!status set <Nama> <HP> <EN> <ST>`\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>`\n"
            "`!status setcarry <Nama> <Capacity>`\n"
            "`!status addxp <Nama> <Jumlah>` • `!status addgold <Nama> <Jumlah>`\n"
            "`!status remove <Nama>`\n\n"
            "**HP/Heal**\n"
            "`!status dmg <Nama> <Jumlah>` • `!status heal <Nama> <Jumlah>`\n"
            "`!party` → Ringkasan party\n"
        ),
        inline=False
    )
    e.add_field(
        name=_title("enemy", "Enemy"),
        value=(
            "`!enemy add <Nama> <HP> [--xp X] [--gold G] [--loot \"item|type|effect|rarity; ...\"]`\n"
            "`!enemy show [Nama]` (player view)\n"
            "`!enemy gmshow [Nama]` (GM view, HP detail)\n"
            "`!enemy dmg <Nama> <Jumlah>` • `!enemy heal <Nama> <Jumlah>`\n"
            "`!enemy loot <Nama>` • `!enemy buff <Nama> <Teks>` • `!enemy debuff ...`\n"
            "`!enemy clearbuff <Nama>` • `!enemy cleardebuff <Nama>`\n"
        ),
        inline=False
    )
    e.add_field(
        name=_title("init", "Initiative"),
        value=(
            "`!init add <Nama> <Skor>`\n"
            "`!init addmany \"Alice 18, Goblin 12\"`\n"
            "`!init show` (alias: `!order`)\n"
            "`!init next` (alias: `!next` / `!n`)\n"
            "`!init setptr <index>` • `!init remove <Nama>` • `!init clear`\n"
            "`!init shuffle` • `!init round [angka]`\n"
            "`!engage` • `!victory [keep] [force]`\n"
        ),
        inline=False
    )
    e.add_field(
        name=_title("tick", "Tick Effects"),
        value="`!tick` → Kurangi durasi buff/debuff semua karakter & musuh.",
        inline=False
    )
    e.add_field(
        name="💡 Alias Cepat",
        value="`!dmg` • `!heal` • `!ene-` • `!ene+` • `!stam-` • `!stam+`",
        inline=False
    )
    return e

def embed_status() -> discord.Embed:
    e = _embed_base(_title("status", "Status (Karakter)"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Setup & Profil",
        value=(
            "`!status set <Nama> <HP> <EN> <ST>`\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>`\n"
            "`!status setcarry <Nama> <Capacity>`"
        ),
        inline=False
    )
    e.add_field(
        name="Perang & Progress",
        value=(
            "`!status dmg <Nama> <Jumlah>` • `!status heal <Nama> <Jumlah>`\n"
            "`!status addxp <Nama> <Jumlah>` • `!status addgold <Nama> <Jumlah>`\n"
            "`!status equip <Nama> <Slot> <Item>`\n"
            "`!party`"
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
            "`!enemy add <Nama> <HP> [--xp X] [--gold G] [--loot \"item|type|effect|rarity; ...\"]`\n"
            "`!enemy show [Nama]` • `!enemy gmshow [Nama]`"
        ),
        inline=False
    )
    e.add_field(
        name="Perang & Efek",
        value=(
            "`!enemy dmg <Nama> <Jumlah>` • `!enemy heal <Nama> <Jumlah>`\n"
            "`!enemy buff <Nama> <Teks>` • `!enemy debuff <Nama> <Teks>`\n"
            "`!enemy clearbuff <Nama>` • `!enemy cleardebuff <Nama>`\n"
            "`!enemy loot <Nama>`"
        ),
        inline=False
    )
    e.set_footer(text="Player hanya melihat kondisi (sehat/luka) – GM punya detail HP.")
    return e

def embed_init() -> discord.Embed:
    e = _embed_base(_title("init", "Initiative Commands"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Urutan & Kontrol",
        value=(
            "`!init add <Nama> <Skor>` • `!init addmany \"A 18, B 12\"`\n"
            "`!init show` • `!init next` • `!init setptr <index>`\n"
            "`!init remove <Nama>` • `!init clear` • `!init shuffle` • `!init round [angka]`\n"
            "`!engage` • `!victory [keep] [force]`"
        ),
        inline=False
    )
    return e

def embed_tick() -> discord.Embed:
    e = _embed_base(_title("tick", "Tick Effects"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Kurangi Durasi Buff/Debuff",
        value="`!tick` → apply ke semua karakter & musuh. Embed akan menampilkan expired & sisa durasi.",
        inline=False
    )
    return e

def embed_world() -> discord.Embed:
    e = _embed_base(_title("world", "World Commands"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Quest",
        value="`!quest add|list|complete|fail|archive|detail`",
        inline=False
    )
    e.add_field(
        name="NPC",
        value="`!npc add|list|favor|reveal|detail|sync|remove`",
        inline=False
    )
    e.add_field(
        name="Favor",
        value="`!favor add|set|show|detail|remove`",
        inline=False
    )
    e.add_field(
        name="Scene",
        value="`!scene create|edit|pin|unpin|show|now`",
        inline=False
    )
    e.add_field(
        name="Item & Inventory & Equipment",
        value="`!item ...` • `!inv ...` • `!status equip ...`",
        inline=False
    )
    return e

def embed_quest() -> discord.Embed:
    e = _embed_base(_title("quest", "Quest Commands"), color=discord.Color.from_rgb(255, 205, 86))
    e.add_field(
        name="Kelola Quest",
        value=(
            "`!quest add <Judul> | <Deskripsi>`\n"
            "`!quest list` • `!quest detail <Nama>`\n"
            "`!quest complete <NamaQuest>` → reward XP/Gold/Loot/Favor\n"
            "`!quest fail <NamaQuest>` • `!quest archive <NamaQuest>`"
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
        name="Favor Kisi",
        value=(
            "`!favor add <Faction> <value> [notes]` (alias: `!favor set ...`)\n"
            "`!favor show` • `!favor detail <Faction>` • `!favor remove <Faction>`"
        ),
        inline=False
    )
    return e

def embed_scene() -> discord.Embed:
    e = _embed_base(_title("scene", "Scene / Zone"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Kelola Scene",
        value=(
            "`!scene create <Nama> | <Deskripsi> | [Factions] | [Danger]`\n"
            "`!scene edit <Nama> | field=value` (multi field pakai `|`)\n"
            "`!scene pin` • `!scene unpin` • `!scene show` • `!scene now`"
        ),
        inline=False
    )
    e.set_footer(text="GM bisa pin scene aktif agar party dapat konteks lokasi & suasana.")
    return e

def embed_item() -> discord.Embed:
    e = _embed_base(_title("item", "Items"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Item Master",
        value=(
            "`!item add <Nama> | <Slot> | <Type> | <Deskripsi>`\n"
            "`!item list` • `!item detail <Nama>`"
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
    e.set_footer(text="Sistem carry: kapasitas & total bobot tampil di status karakter.")
    return e

def embed_equipment() -> discord.Embed:
    e = _embed_base(_title("equipment", "Equipment"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Equip / Unequip (via Status)",
        value=(
            "`!status equip <Nama> <Slot> <Item>`\n"
            "Slot: `main_hand, off_hand, armor_inner, armor_outer, accessory1-3, augment1-3`"
        ),
        inline=False
    )
    return e

def embed_utility() -> discord.Embed:
    e = _embed_base(_title("utility", "Utility"), color=discord.Color.from_rgb(100, 100, 100))
    e.add_field(
        name=_title("roll", "Roll"),
        value="`!roll d20+5` • `!roll 4d6kh3` • `!roll d100`",
        inline=False
    )
    e.add_field(
        name=_title("poll", "Poll"),
        value="`!poll \"Judul\" | Opsi A | Opsi B | Opsi C`",
        inline=False
    )
    e.add_field(
        name=_title("multi", "Multi-Command"),
        value="`!multi \"!dmg Goblin 3; !heal Alice 4; !inv add Alice Potion 2\"`",
        inline=False
    )
    e.add_field(
        name=_title("ask", "GPT Ask"),
        value="`!ask Kenapa goblin benci matahari?`",
        inline=False
    )
    return e

def embed_roll() -> discord.Embed:
    return _embed_base(_title("roll", "Roll"), "Contoh: `!roll 2d20kh1+3` • `!roll 5d8`", color=discord.Color.dark_grey())

def embed_poll() -> discord.Embed:
    return _embed_base(_title("poll", "Poll"), "Contoh: `!poll \"Pilih rute\" | Utara | Timur | Selatan`", color=discord.Color.dark_grey())

def embed_multi() -> discord.Embed:
    return _embed_base(_title("multi", "Multi-Command"), "Contoh: `!multi \"!dmg Goblin 3; !heal Alice 4\"`", color=discord.Color.dark_grey())

def embed_ask() -> discord.Embed:
    return _embed_base(_title("ask", "Ask (GPT)"), "Contoh: `!ask Tulis deskripsi kota pelabuhan berkabut.`", color=discord.Color.dark_grey())

# Map kategori → builder
EMBED_BUILDERS = {
    "home": embed_home,
    "core": embed_core,
    "status": embed_status,
    "enemy": embed_enemy,
    "init": embed_init,
    "tick": embed_tick,

    "world": embed_world,
    "quest": embed_quest,
    "npc": embed_npc,
    "favor": embed_favor,
    "scene": embed_scene,
    "item": embed_item,
    "inventory": embed_inventory,
    "equipment": embed_equipment,

    "utility": embed_utility,
    "roll": embed_roll,
    "poll": embed_poll,
    "multi": embed_multi,
    "ask": embed_ask,
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
        # Batasi yang bisa klik: si pengirim (biar gak rebutan)
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
        """Tampilkan help interaktif atau detail kategori tertentu."""
        if category:
            key = category.strip().lower()
            embed = self._embed_for_key(key, ctx.guild)
            return await ctx.send(embed=embed)

        view = HelpNav(ctx.author.id)
        embed = embed_home(ctx.guild)
        await ctx.send(embed=embed, view=view)

    # alias singkat
    @help_group.command(name="ui")
    async def help_ui(self, ctx):
        """Buka help interaktif (UI)."""
        view = HelpNav(ctx.author.id)
        await ctx.send(embed=embed_home(ctx.guild), view=view)

    @commands.command(name="commands")
    async def list_all_commands(self, ctx):
        """Daftar nama command (ringkas)."""
        names = sorted(c.qualified_name for c in self.bot.commands)
        chunks = []
        current = ""
        for n in names:
            if len(current) + len(n) + 2 > 1900:  # jaga panjang
                chunks.append(current)
                current = ""
            current += (n + ", ")
        if current:
            chunks.append(current)

        for i, ch in enumerate(chunks, 1):
            e = discord.Embed(
                title=f"🧰 Daftar Commands ({i}/{len(chunks)})",
                description=ch.rstrip(", "),
                color=discord.Color.dark_teal(),
            )
            await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(HelpUI(bot))
