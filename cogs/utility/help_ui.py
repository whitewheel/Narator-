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
    "effect": "💫",
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
    "timeline": "🕓",
    "wiki": "📖",
    "classrace": "🧑‍🎓",
    "skill": "💡",

    "utility": "🧰",
    "gm": "🎭",
}

CATEGORIES = [
    ("home", "Overview"),
    ("core", "Core (Ringkasan Cepat)"),
    ("status", "Status (Karakter)"),
    ("enemy", "Enemy"),
    ("ally", "Ally"),
    ("effect", "Effect / Buff-Debuff"),
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
    ("skill", "Skill"),

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
        "Selamat datang di **Narator Bot** 🎭\n\n"
        "Pakai **dropdown** di bawah untuk memilih kategori bantuan. "
        "Ikon bikin kamu cepat paham tiap fitur 😸\n\n"
        "**Kategori Utama:**\n"
        "• ⚔️ Core: Status, Enemy, Ally, Effect, Initiative, Tick\n"
        "• 🌍 World: Quest, NPC, Shop, Favor, Faction, Scene, Items, Inventory, Equipment, Timeline, Wiki, Class/Race, Skill\n"
        "• 🧰 Utility: Roll, Poll, Multi, Ask\n"
        "• 🎭 GM Only: Kontrol & shortcut untuk GM"
    )
    e.set_footer(text="Tip: ketik !help <kategori> untuk detail — contoh: !help quest")
    return e

# =====================================
#           CORE / COMBAT
# =====================================

def embed_core() -> discord.Embed:
    e = _embed_base(_title("core", "Core (Ringkasan Cepat)"), color=discord.Color.from_rgb(60, 160, 255))
    e.add_field(
        name="Status",
        value=(
            "`!status set Udab 20 10 15` • set basic HP/EN/ST\n"
            "`!status setcore Udab 14 12 13 10 8 9` • set STR–CHA\n"
            "`!status dmg Udab 5` • damage | `!status heal Udab 3` • heal\n"
            "`!addstm Udab 5` | `!usestm Udab 3` • stamina±\n"
            "`!addene Udab 4` | `!useene Udab 2` • energy±\n"
            "`!party` • ringkasan party"
        ),
        inline=False
    )
    e.add_field(
        name="Enemy & Ally",
        value=(
            "`!enemy add Necrohusk 200 50 50 --xp 150 --gold 30` • tambah musuh\n"
            "`!enemy show` | `!enemy gmshow` • lihat musuh\n"
            "`!ally add Nyx 18 10 12` • tambah ally | `!ally show`\n"
            "`!enemy buff <Nama> <Effect>` | `!ally debuff <Nama> <Effect>`"
        ),
        inline=False
    )
    e.add_field(
        name="Effect & Tick",
        value=(
            "`!effect add Rage buff STR +2 3 stack 'Naikkan STR' 3` • add lib\n"
            "`!apply Udab Rage` • apply efek\n"
            "`!effect active Udab` • lihat efek aktif\n"
            "`!tick` • kurangi durasi semua efek engage"
        ),
        inline=False
    )
    e.add_field(
        name="Initiative",
        value=(
            "`!init add Udab 15` | `!init addmany \"Udab 15, Rain 12, Husk 9\"`\n"
            "`!init show` | `!init next` | `!init setptr 2` | `!init round 3`\n"
            "`!init remove Husk` | `!init clear` | `!init engage` | `!init victory`"
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
            "• `!status set Udab 20 10 15`\n\n"
            "`!status setcore <Nama> <STR> <DEX> <CON> <INT> <WIS> <CHA>`\n"
            "• `!status setcore Udab 14 12 13 10 8 9`\n\n"
            "`!status setclass <Nama> <Class>` • `!status setrace <Nama> <Race>`\n"
            "• `!status setclass Udab Warrior` • `!status setrace Udab Human`\n\n"
            "`!status setlevel <Nama> <Lv>` • `!status setac <Nama> <AC>`\n"
            "• `!status setlevel Udab 3` • `!status setac Udab 14`\n\n"
            "`!status setcarry <Nama> <Capacity>`\n"
            "• `!status setcarry Udab 25`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat, Resource & Progress",
        value=(
            "`!status dmg <Nama> <N>` • `!status heal <Nama> <N>`\n"
            "• `!status dmg Udab 5` • `!status heal Udab 3`\n\n"
            "`!status addxp <Nama> <N>` • `!status subxp <Nama> <N>`\n"
            "• `!status addxp Udab 120` • `!status subxp Udab 40`\n\n"
            "`!status addgold <Nama> <N>` • `!status subgold <Nama> <N>`\n"
            "• `!status addgold Udab 50` • `!status subgold Udab 20`\n\n"
            "`!addstm <Nama> <N>` • `!usestm <Nama> <N>`\n"
            "• `!addstm Udab 5` • `!usestm Udab 2`\n\n"
            "`!addene <Nama> <N>` • `!useene <Nama> <N>`\n"
            "• `!addene Udab 4` • `!useene Udab 2`\n\n"
            "`!buff <Nama> <Teks>` • `!debuff <Nama> <Teks>`\n"
            "• `!buff Udab Bless +2 STR` • `!debuff Udab Poison -2 CON`\n\n"
            "`!clearbuff <Nama>` • `!cleardebuff <Nama>`\n"
            "• `!clearbuff Udab` • `!cleardebuff Udab`\n\n"
            "`!party` → ringkasan party"
        ),
        inline=False
    )
    e.add_field(
        name="Tampilan",
        value=(
            "`!status all` • semua karakter\n"
            "`!status show <Nama>` • tampilkan 2 halaman (Status & Equipment+Inventory)\n"
            "• `!status show Udab`"
        ),
        inline=False
    )
    e.add_field(
        name="Remove",
        value="`!status remove <Nama>` • `!status remove Udab`",
        inline=False
    )
    return e

def embed_enemy() -> discord.Embed:
    e = _embed_base(_title("enemy", "Enemy Commands"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!enemy add <Nama> <HP> [EN] [ST] [--xp N] [--gold N] [--loot ...]`\n"
            "• `!enemy add Necrohusk 200 50 50 --xp 150 --gold 30`\n"
            "• `--loot` format: `Nama|Type|Effect|Rarity; Nama2|Type2|...`\n\n"
            "`!enemy show [Nama]` → status player (tanpa angka persis)\n"
            "`!enemy gmshow [Nama]` → status GM (angka detail)\n"
            "`!enemy remove <Nama>`"
        ),
        inline=False
    )
    e.add_field(
        name="Buff / Debuff",
        value=(
            "`!enemy buff <Nama> <EffectName> [dur]`\n"
            "`!enemy debuff <Nama> <EffectName> [dur]`\n"
            "`!enemy clearbuff <Nama>` • `!enemy cleardebuff <Nama>`\n"
            "• `!enemy buff Necrohusk Rage 3`"
        ),
        inline=False
    )
    e.add_field(
        name="Resource",
        value=(
            "`!enemy stam- <Nama> <N>` • `!enemy stam+ <Nama> <N>`\n"
            "`!enemy ene- <Nama> <N>` • `!enemy ene+ <Nama> <N>`\n"
            "• `!enemy stam- Necrohusk 5` • `!enemy ene+ Necrohusk 10`"
        ),
        inline=False
    )
    return e

def embed_ally() -> discord.Embed:
    e = _embed_base(_title("ally", "Ally Commands"), color=discord.Color.from_rgb(100, 200, 100))
    e.add_field(
        name="Tambah & Lihat",
        value=(
            "`!ally add <Nama> <HP> <EN> <ST>`\n"
            "• `!ally add Nyx 18 10 12`\n"
            "`!ally show [Nama]` • `!ally gmshow [Nama]`"
        ),
        inline=False
    )
    e.add_field(
        name="Combat & Efek",
        value=(
            "`!ally dmg <Nama> <N>` • `!ally heal <Nama> <N>`\n"
            "`!ally buff <Nama> <EffectName> [dur]` • `!ally debuff <Nama> <EffectName> [dur]`\n"
            "• `!ally dmg Nyx 3` • `!ally buff Nyx Haste 2`"
        ),
        inline=False
    )
    e.add_field(
        name="Kelola",
        value="`!ally clear` • hapus semua ally | `!ally remove <Nama>`",
        inline=False
    )
    return e

def embed_effect() -> discord.Embed:
    e = _embed_base(_title("effect", "Effect / Buff-Debuff"), color=discord.Color.from_rgb(200, 120, 255))
    e.add_field(
        name="Library (GM)",
        value=(
            "`!effect add <name> <type> <target_stat> <formula> <duration> <stack_mode> \"<desc>\" [max_stack]`\n"
            "• `type`: buff/debuff | `target_stat`: STR/DEX/CON/INT/WIS/CHA/AC/dll\n"
            "• `formula`: misal `+2`, `-1d4`, `+10%`, atau teks custom\n"
            "• `stack_mode`: none/add/replace\n"
            "• Contoh: `!effect add Rage buff STR +2 3 add \"Naikkan STR sementara\" 3`\n\n"
            "`!effect list` • `!effect info <name>` • `!effect remove <name>`"
        ),
        inline=False
    )
    e.add_field(
        name="Apply & Active",
        value=(
            "`!apply <TargetName> <EffectName> [duration_override]` → apply dari library\n"
            "• `!apply Udab Rage` | `!apply Necrohusk Poison 2`\n\n"
            "`!effect active <TargetName>` → daftar efek aktif\n"
            "• `!effect active Udab`\n\n"
            "`!effect clear <TargetName>` • hapus semua efek\n"
            "`!effect clearbuff <TargetName>` • hanya buff\n"
            "`!effect cleardebuff <TargetName>` • hanya debuff"
        ),
        inline=False
    )
    e.add_field(
        name="Tick",
        value=(
            "`!tick` → kurangi durasi semua efek (hanya peserta engage di initiative). "
            "Efek durasi 0 akan otomatis kedaluwarsa dan dilaporkan."
        ),
        inline=False
    )
    return e

def embed_init() -> discord.Embed:
    e = _embed_base(_title("init", "Initiative"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Urutan & Kontrol",
        value=(
            "`!init add <Nama> <Skor>` • `!init add Udab 15`\n"
            "`!init addmany \"Udab 15, Rain 12, Necrohusk 9\"`\n"
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
        value="`!tick` → kurangi durasi semua efek dan tampilkan expired. (terkait dengan peserta di initiative).",
        inline=False
    )
    return e

# =====================================
#           WORLD SYSTEM
# =====================================

def embed_quest() -> discord.Embed:
    e = _embed_base(_title("quest", "Quest Commands"), color=discord.Color.from_rgb(255, 205, 86))
    e.add_field(
        name="Kelola Quest",
        value=(
            "`!quest add <Nama> | <Deskripsi>`\n"
            "• `!quest add Cari Antibiotik | Bantu Ka'ruun mencari antibiotik.`\n\n"
            "`!quest show` • `!quest gmshow` • `!quest showarchived`\n"
            "`!quest detail <Nama>` • `!quest reveal <Nama>`\n"
            "• `!quest detail Cari Antibiotik`\n\n"
            "`!quest assign <Quest> <Char1,Char2>`\n"
            "• `!quest assign Cari Antibiotik Udab,Rain`\n\n"
            "`!quest reward <Quest> xp=100 gold=50 items=\"Potion x2; Key x1\" favor=\"Mutaris:+2\"`\n"
            "• `!quest reward Cari Antibiotik xp=200 gold=100 items=\"Antibiotik x1\" favor=\"Mutaris:+2\"`\n\n"
            "`!quest rewardvisible <Quest> on/off`\n"
            "`!quest complete <Quest>` • `!quest fail <Quest>` • `!quest archive <Quest>`"
        ),
        inline=False
    )
    return e

def embed_npc() -> discord.Embed:
    e = _embed_base(_title("npc", "NPC Commands"), color=discord.Color.from_rgb(255, 99, 132))
    e.add_field(
        name="Kelola NPC",
        value=(
            "`!npc add <Nama> | [Role]`\n"
            "• `!npc add Ka'ruun | Pemimpin Mutaris`\n\n"
            "`!npc list`\n"
            "`!npc detail <Nama>` • `!npc remove <Nama>` • `!npc sync`\n\n"
            "**Traits & Info**\n"
            "`!npc trait_add <Nama> key=value` • `!npc trait_remove <Nama> <key>`\n"
            "• `!npc trait_add Ka'ruun Bijak`\n"
            "`!npc reveal <Nama> <Trait>` • `!npc allreveal <Nama>`\n"
            "`!npc info <Nama> <Teks>`"
        ),
        inline=False
    )
    return e

def embed_shop() -> discord.Embed:
    e = _embed_base(_title("shop", "Shop / Merchant"), color=discord.Color.from_rgb(240, 180, 50))
    e.add_field(
        name="Lihat Dagangan",
        value=(
            "`!shop list <NPC> [Char]` → daftar item versi player\n"
            "• `!shop list Ka'ruun Udab`\n"
            "`!shop gmlist <NPC>` → versi lengkap (GM)\n"
        ),
        inline=False
    )
    e.add_field(
        name="Kelola Dagangan",
        value=(
            "`!shop add <NPC> <Item> <Harga> [Stock]`\n"
            "• `!shop add Ka'ruun Antibiotik 50 3`\n"
            "`!shop remove <NPC> <Item>` • `!shop clear <NPC>`"
        ),
        inline=False
    )
    e.add_field(
        name="Belanja",
        value=(
            "`!shop buy <NPC> <Char> <Item> [Qty]`\n"
            "• `!shop buy Ka'ruun Udab Antibiotik 1`\n\n"
            "💡 Otomatis cek gold & carry. Gagal bila tak cukup."
        ),
        inline=False
    )
    e.add_field(
        name="Lock / Unlock",
        value=(
            "`!shop unlock <NPC> <Item> [favor=<Faction>:<Val>] [quest=<Quest>]`\n"
            "• `!shop unlock Ka'ruun Antibiotik favor=Mutaris:2 quest=Cari Antibiotik`"
        ),
        inline=False
    )
    return e

def embed_favor() -> discord.Embed:
    e = _embed_base(_title("favor", "Favor / Faction"), color=discord.Color.from_rgb(54, 162, 235))
    e.add_field(
        name="Favor Commands",
        value=(
            "`!favor add <Char> <Faction> <Value>` • `!favor set <Char> <Faction> <Value>`\n"
            "`!favor mod <Char> <Faction> +/-N` • `!favor show <Char>` • `!favor gmshow`\n"
            "• `!favor add Udab Mutaris 3` • `!favor mod Udab Mutaris +2`"
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
            "• `!faction add ArthaDyne | Korporasi biotek elit | corp`\n\n"
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
            "`!scene create <Nama> | <Deskripsi>`\n"
            "• `!scene create Sewer01 | Lorong bawah tanah berbau menyengat`\n\n"
            "`!scene edit <Nama> | field=value`\n"
            "• `!scene edit Sewer01 | danger=high`\n\n"
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
            "`!item add Nama | Type | Effect | Rarity | Value | Weight | [Slot] | [Notes] | [Rules] | [Requirement]`\n"
            "• `!item add Rust Shiv | Weapon | Pisau karatan | Common | 0 | 1.0 | main_hand | Senjata awal | +1 dmg | DEX+3`\n\n"
            "`!item show all` • `!item show weapon`\n"
            "`!item detail <Nama>` • `!item remove <Nama>`\n"
            "`!item edit <Nama> | key=value` • `!item info <Nama>`\n"
            "• `!item edit Rust Shiv | weight=1.2 rarity=Uncommon`"
        ),
        inline=False
    )
    return e

def embed_inventory() -> discord.Embed:
    e = _embed_base(_title("inventory", "Inventory"), color=discord.Color.from_rgb(255, 159, 64))
    e.add_field(
        name="Inventory Commands",
        value=(
            "`!inv add <Char> <Item> [Qty]` • `!inv remove <Char> <Item> [Qty]`\n"
            "`!inv drop <Char> <Item> [Qty]` • `!inv clear <Char>`\n"
            "`!inv show <Char>`\n"
            "`!inv transfer <Char1> <Char2> <Item> [Qty]`\n"
            "`!inv meta <Char> <Item> key=value`\n"
            "`!inv use <Char> <Item>` • `!inv recalc_all`\n\n"
            "• `!inv add Udab Rust Shiv 1`\n"
            "• `!inv transfer Udab Nyx Rust Shiv 1`\n"
            "• `!inv meta Udab Rust Shiv weight=1.0 rarity=Common`"
        ),
        inline=False
    )
    return e

def embed_equipment() -> discord.Embed:
    e = _embed_base(_title("equipment", "Equipment"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Equip / Unequip",
        value=(
            "`!equip set <Char> <Slot> <Item>` • `!equip remove <Char> <Slot>` • `!equip show <Char>`\n"
            "Slot: `main_hand, off_hand, armor_inner, armor_outer, accessory1-3, augment1-3`\n\n"
            "• `!equip set Udab main_hand Rust Shiv`\n"
            "• `!equip remove Udab main_hand`"
        ),
        inline=False
    )
    return e

def embed_timeline() -> discord.Embed:
    e = _embed_base(_title("timeline", "Timeline"), color=discord.Color.from_rgb(201, 203, 207))
    e.add_field(
        name="Timeline Commands",
        value=(
            "`!timeline add <Teks>` • catat kejadian\n"
            "`!timeline search <keyword>` • cari\n"
            "`!timeline full` • tampilkan semua\n\n"
            "• `!timeline add Udab bertemu Ka'ruun di Khaj`"
        ),
        inline=False
    )
    return e

def embed_wiki() -> discord.Embed:
    e = _embed_base(_title("wiki", "Wiki Commands"), color=discord.Color.from_rgb(153, 102, 255))
    e.add_field(
        name="Wiki Commands",
        value=(
            "`!wiki list` • daftar wiki\n"
            "`!wiki get <Nama>` • ambil konten\n"
            "`!wiki add <Nama> | <Konten>` • tambah/replace\n"
            "`!wiki remove <Nama>`\n\n"
            "• `!wiki add Khaj | Wilayah bawah tanah Mutaris.`\n"
            "• `!wiki get Khaj`"
        ),
        inline=False
    )
    return e

def embed_classrace() -> discord.Embed:
    e = _embed_base(_title("classrace", "Class & Race"), color=discord.Color.from_rgb(75, 192, 192))
    e.add_field(
        name="Class & Race",
        value=(
            "`!classinfo <Name>` • info class\n"
            "`!raceinfo <Name>` • info race\n"
            "`!setclass <Char> <ClassName>` • atur class cepat\n"
            "`!setrace <Char> <RaceName>` • atur race cepat\n\n"
            "• `!classinfo Rustborn` • `!raceinfo Exoform`\n"
            "• `!setclass Udab Warrior` • `!setrace Udab Human`"
        ),
        inline=False
    )
    return e

def embed_skill() -> discord.Embed:
    e = _embed_base(_title("skill", "Skill Commands"), color=discord.Color.from_rgb(0, 200, 200))
    e.add_field(
        name="Player",
        value=(
            "`!skill show <Char>` → semua skill karakter\n"
            "`!skill show <Char> <Kategori>` → filter (Basic/Learning/Racial/Augment/Item)\n"
            "`!skill use <Char> <Skill>` → gunakan skill (efek/cost/drawback)\n\n"
            "• `!skill show Udab`\n"
            "• `!skill show Udab Basic`\n"
            "• `!skill use Udab Athletics`"
        ),
        inline=False
    )
    e.add_field(
        name="GM",
        value=(
            "`!skill add <Char> <SkillName/ID> [Lv]`\n"
            "`!skill remove <Char> <SkillName>`\n"
            "`!skill reset <Char>`\n"
            "`!skill gmglobal` → lihat semua skill di server\n\n"
            "• `!skill add Udab Athletics 2`"
        ),
        inline=False
    )
    e.add_field(
        name="Library",
        value=(
            "`!skill library add <Kategori> <Nama> <Efek> <Drawback> <Cost>`\n"
            "`!skill library list [Kategori]` • pagination\n"
            "`!skill library info <Nama/ID>`\n"
            "`!skill library remove <Nama/ID>`\n"
            "`!skill library update <Nama/ID> <Efek> <Drawback> <Cost>`\n\n"
            "• `!skill library add Basic Athletics \"Fisik dasar\" \"Capek kalau lama\" \"ST 1\"`"
        ),
        inline=False
    )
    return e

# =====================================
#           UTILITY & GM
# =====================================

def embed_utility() -> discord.Embed:
    e = _embed_base(_title("utility", "Utility"), color=discord.Color.from_rgb(100, 100, 100))
    e.add_field(name="🎲 Roll", value="`!roll 1d20+3` • `!roll 2d6+4`", inline=False)
    e.add_field(name="📊 Poll", value="`!poll \"Judul\" opsi1 opsi2` • `!poll \"Pilih jalan\" kiri kanan`", inline=False)
    e.add_field(name="🗂️ Multi-Command", value="`!multi !dmg Goblin 3 x3`", inline=False)
    e.add_field(name="🤖 Ask (GPT)", value="`!ask Ceritakan tentang Technonesia`", inline=False)
    return e

def embed_gm() -> discord.Embed:
    e = _embed_base(_title("gm", "Game Master Commands"), color=discord.Color.from_rgb(200, 50, 200))
    e.add_field(
        name="History & Shortcuts",
        value=(
            "`!undo` → batalkan aksi terakhir\n\n"
            "**Enemy Shortcuts**: `!edmg <Enemy> <N>`, `!eheal <Enemy> <N>`, `!ebuff <Enemy> <Text>`, `!edebuff <Enemy> <Text>`\n"
            "**Ally Shortcuts**: `!admg <Ally> <N>`, `!aheal <Ally> <N>`, `!abuff <Ally> <Text>`, `!adebuff <Ally> <Text>`"
        ),
        inline=False
    )
    return e

# ===============================
#  CATEGORY MAPPER
# ===============================

EMBED_BUILDERS = {
    "home": lambda g=None: embed_home(g),
    "core": embed_core,
    "status": embed_status,
    "enemy": embed_enemy,
    "ally": embed_ally,
    "effect": embed_effect,
    "init": embed_init,
    "tick": embed_tick,
    "quest": embed_quest,
    "npc": embed_npc,
    "shop": embed_shop,
    "favor": embed_favor,
    "faction": embed_faction,
    "scene": embed_scene,
    "item": embed_item,
    "inventory": embed_inventory,
    "equipment": embed_equipment,
    "timeline": embed_timeline,
    "wiki": embed_wiki,
    "classrace": embed_classrace,
    "skill": embed_skill,
    "utility": embed_utility,
    "gm": embed_gm,
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
        await ctx.send(embed=embed_home(ctx.guild), view=view)

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
