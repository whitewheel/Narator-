-- ===============================
-- CHARACTERS
-- ===============================
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,                -- server id
    channel_id TEXT,              -- channel id
    name TEXT NOT NULL,           -- nama karakter
    player_id TEXT DEFAULT NULL,  -- optional: discord user id
    class TEXT DEFAULT NULL,
    race TEXT DEFAULT NULL,
    hp INTEGER DEFAULT 0,
    hp_max INTEGER DEFAULT 0,
    mp INTEGER DEFAULT 0,
    mp_max INTEGER DEFAULT 0,
    ac INTEGER DEFAULT 10,
    init_mod INTEGER DEFAULT 0,
    str INTEGER DEFAULT 0,
    dex INTEGER DEFAULT 0,
    int INTEGER DEFAULT 0,
    wit INTEGER DEFAULT 0,
    cha INTEGER DEFAULT 0,
    effects TEXT DEFAULT '[]',    -- JSON list buff/debuff
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
    items_required TEXT DEFAULT '[]', -- JSON list item requirement
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
