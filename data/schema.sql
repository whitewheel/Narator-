-- Characters
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    hp INTEGER DEFAULT 0,
    hp_max INTEGER DEFAULT 0,
    mp INTEGER DEFAULT 0,
    mp_max INTEGER DEFAULT 0,
    ac INTEGER DEFAULT 10,
    init_mod INTEGER DEFAULT 0,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quests
CREATE TABLE IF NOT EXISTS quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    detail TEXT DEFAULT '',
    status TEXT DEFAULT 'open',  -- open/done
    created_by TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    qty INTEGER DEFAULT 1,
    owner TEXT DEFAULT NULL,  -- kalau NULL = item party
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Encounters
CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT 'Encounter',
    active INTEGER DEFAULT 1,
    turn_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS encounter_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id INTEGER NOT NULL,
    label TEXT NOT NULL,         -- nama char/npc/enemy
    initiative INTEGER DEFAULT 0,
    tied INTEGER DEFAULT 0,
    FOREIGN KEY(encounter_id) REFERENCES encounters(id)
);

-- Notes
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wiki (Lore / Reference)
CREATE TABLE IF NOT EXISTS wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,  -- contoh: race, class, npc, timeline
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
