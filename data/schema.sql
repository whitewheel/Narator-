-- ===============================
-- CHARACTERS
-- ===============================
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    name TEXT NOT NULL,
    player_id TEXT DEFAULT NULL,
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

    -- Carry system
    carry_capacity INTEGER DEFAULT 0,
    carry_used REAL DEFAULT 0,

    -- JSON fields
    buffs TEXT DEFAULT '[]',
    debuffs TEXT DEFAULT '[]',
    equipment TEXT DEFAULT '{}',
    companions TEXT DEFAULT '[]',
    inventory TEXT DEFAULT '[]',

    notes TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- ENEMIES
-- ===============================
CREATE TABLE IF NOT EXISTS enemies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hp INTEGER DEFAULT 0,
    hp_max INTEGER DEFAULT 0,
    ac INTEGER DEFAULT 10,
    init_mod INTEGER DEFAULT 0,
    xp_reward INTEGER DEFAULT 0,
    gold_reward INTEGER DEFAULT 0,
    loot TEXT DEFAULT '[]',
    effects TEXT DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- QUESTS
-- ===============================
CREATE TABLE IF NOT EXISTS quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    name TEXT UNIQUE,
    desc TEXT,
    status TEXT DEFAULT 'open',
    assigned_to TEXT DEFAULT '[]',
    rewards TEXT DEFAULT '{}',
    favor TEXT DEFAULT '{}',
    tags TEXT DEFAULT '{}',
    created_by TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INVENTORY
-- ===============================
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    owner TEXT DEFAULT 'party',
    item TEXT NOT NULL,
    qty INTEGER DEFAULT 1,
    metadata TEXT DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- NPC
-- ===============================
CREATE TABLE IF NOT EXISTS npc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    favor INTEGER DEFAULT 0,
    traits TEXT DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- FAVORS
-- ===============================
CREATE TABLE IF NOT EXISTS favors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT,
    faction TEXT NOT NULL,
    favor INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, faction)
);

-- ===============================
-- ENCOUNTERS & INITIATIVE
-- ===============================
CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
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
    label TEXT NOT NULL,
    initiative INTEGER DEFAULT 0,
    tied INTEGER DEFAULT 0,
    type TEXT DEFAULT 'char',
    state_json TEXT DEFAULT '{}',
    FOREIGN KEY(encounter_id) REFERENCES encounters(id)
);

-- ===============================
-- HISTORY (Undo/Log of Changes)
-- ===============================
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    action TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- TIMELINE (Narrative Log)
-- ===============================
CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    event TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- NOTES
-- ===============================
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    text TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- WIKI (Lore / Reference)
-- ===============================
CREATE TABLE IF NOT EXISTS wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INITIATIVE (Legacy/simple tracker)
-- ===============================
CREATE TABLE IF NOT EXISTS initiative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    order_json TEXT,
    ptr INTEGER,
    round INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INDEXES
-- ===============================
CREATE UNIQUE INDEX IF NOT EXISTS idx_char_guild_name ON characters(guild_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_enemy_guild_name ON enemies(guild_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_guild_name ON quests(guild_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_npc_guild_name ON npc(guild_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_favor_guild_faction ON favors(guild_id, faction);
CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(guild_id, owner);
