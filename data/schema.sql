-- ==============================
-- CHARACTERS
-- ===============================
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
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
    name TEXT NOT NULL UNIQUE,
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
    name TEXT NOT NULL UNIQUE,
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
-- NPC
-- ===============================
CREATE TABLE IF NOT EXISTS npc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
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
    faction TEXT NOT NULL UNIQUE,
    favor INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INITIATIVE (simple tracker)
-- ===============================
CREATE TABLE IF NOT EXISTS initiative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_json TEXT,
    ptr INTEGER,
    round INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- HISTORY
-- ===============================
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- TIMELINE
-- ===============================
CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- WIKI
-- ===============================
CREATE TABLE IF NOT EXISTS wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- INDEXES
-- ===============================
CREATE UNIQUE INDEX IF NOT EXISTS idx_char_name ON characters(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_enemy_name ON enemies(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_name ON quests(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_npc_name ON npc(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_favor_faction ON favors(faction);
