-- ===============================
-- CHARACTERS
-- ===============================
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,                -- server id
    channel_id TEXT,              -- channel id
    name TEXT NOT NULL,           -- nama karakter
    player_id TEXT DEFAULT NULL,  -- optional: discord user id
    class TEXT DEFAULT '',
    race TEXT DEFAULT '',
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,

    -- Vitals
    hp INTEGER DEFAULT 0,
    hp_max INTEGER DEFAULT 0,
    energy INTEGER DEFAULT 0,
    energy_max INTEGER DEFAULT 0,
    stamina INTEGER DEFAULT 0,
    stamina_max INTEGER DEFAULT 0,

    -- Core stats
    str INTEGER DEFAULT 1,
    dex INTEGER DEFAULT 1,
    con INTEGER DEFAULT 1,
    int INTEGER DEFAULT 1,
    wis INTEGER DEFAULT 1,
    cha INTEGER DEFAULT 1,

    -- Combat
    ac INTEGER DEFAULT 10,
    init_mod INTEGER DEFAULT 0,
    speed INTEGER DEFAULT 30,

    -- JSON fields
    buffs TEXT DEFAULT '[]',       -- JSON list
    debuffs TEXT DEFAULT '[]',     -- JSON list
    equipment TEXT DEFAULT '{}',   -- JSON {weapon, armor, accessory}
    companions TEXT DEFAULT '[]',  -- JSON list

    notes TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- ENEMIES
-- ===============================
CREATE TABLE IF NOT EXISTS enemies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    name TEXT NOT NULL,
    hp INTEGER DEFAULT 0,
    hp_max INTEGER DEFAULT 0,
    ac INTEGER DEFAULT 10,
    init_mod INTEGER DEFAULT 0,
    xp_reward INTEGER DEFAULT 0,
    loot TEXT DEFAULT '[]',       -- JSON list item drops
    effects TEXT DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- QUESTS
-- ===============================
CREATE TABLE IF NOT EXISTS quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    title TEXT NOT NULL,
    detail TEXT DEFAULT '',
    status TEXT DEFAULT 'open', -- open/completed/failed
    items_required TEXT DEFAULT '[]', -- JSON list
    rewards TEXT DEFAULT '{}',        -- JSON {loot, favor, xp}
    created_by TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INVENTORY
-- ===============================
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    owner TEXT DEFAULT 'party',  -- karakter atau 'party'
    item TEXT NOT NULL,
    qty INTEGER DEFAULT 1,
    metadata TEXT DEFAULT '{}',  -- JSON {rarity, type, notes}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- NPC
-- ===============================
CREATE TABLE IF NOT EXISTS npc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    favor INTEGER DEFAULT 0,
    traits TEXT DEFAULT '{}', -- JSON: {"hidden1": "rahasia"}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- ENCOUNTERS & INITIATIVE
-- ===============================
CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    name TEXT DEFAULT 'Encounter',
    round INTEGER DEFAULT 1,
    turn_index INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS encounter_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id INTEGER NOT NULL,
    label TEXT NOT NULL,         -- nama char/npc/enemy
    initiative INTEGER DEFAULT 0,
    tied INTEGER DEFAULT 0,
    type TEXT DEFAULT 'char',    -- char/enemy/npc
    FOREIGN KEY(encounter_id) REFERENCES encounters(id)
);

-- ===============================
-- HISTORY (Undo/Log of Changes)
-- ===============================
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    action TEXT NOT NULL,         -- contoh: dmg, heal, loot_add
    data TEXT NOT NULL,           -- JSON detail perubahan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- TIMELINE (Narrative Log)
-- ===============================
CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    event TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- NOTES
-- ===============================
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- WIKI (Lore / Reference)
-- ===============================
CREATE TABLE IF NOT EXISTS wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    channel_id TEXT,
    category TEXT NOT NULL,  -- race, class, npc, timeline
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
