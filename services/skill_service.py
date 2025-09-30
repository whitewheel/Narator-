from utils.db import execute, fetchall, fetchone

# ==================================================
# SKILL LIBRARY (GM)
# ==================================================
def add_library(guild_id: int, category: str, name: str, effect: str, drawback: str, cost: str) -> str:
    execute(
        guild_id,
        "INSERT INTO skill_library (guild_id, name, category, effect, drawback, cost) VALUES (?,?,?,?,?,?)",
        (guild_id, name.title(), category.title(), effect, drawback, cost),
    )
    return f"📚 Skill **{name.title()}** ditambahkan ke library kategori {category.title()}."

def list_library(guild_id: int):
    return fetchall(guild_id, "SELECT id, name, category FROM skill_library WHERE guild_id=?", (guild_id,))

def get_library_info(guild_id: int, skill_id: int):
    return fetchone(guild_id, "SELECT * FROM skill_library WHERE guild_id=? AND id=?", (guild_id, skill_id))

def remove_library(guild_id: int, skill_id: int) -> str:
    execute(guild_id, "DELETE FROM skill_library WHERE guild_id=? AND id=?", (guild_id, skill_id))
    return f"🗑️ Skill library dengan ID {skill_id} dihapus."

def update_library(guild_id: int, skill_id: int, effect: str, drawback: str, cost: str) -> str:
    execute(
        guild_id,
        "UPDATE skill_library SET effect=?, drawback=?, cost=? WHERE guild_id=? AND id=?",
        (effect, drawback, cost, guild_id, skill_id),
    )
    return f"✏️ Skill library ID {skill_id} berhasil diupdate."


# ==================================================
# SKILL KARAKTER (PLAYER)
# ==================================================
def add_skill(guild_id: int, char_name: str, skill_id: int, level: int) -> str:
    row = fetchone(guild_id, "SELECT * FROM skill_library WHERE guild_id=? AND id=?", (guild_id, skill_id))
    if not row:
        return f"❌ Skill dengan ID {skill_id} tidak ada di library."

    execute(
        guild_id,
        "INSERT INTO skills (guild_id, char_name, skill_id, category, name, level) VALUES (?,?,?,?,?,?)",
        (guild_id, char_name, skill_id, row["category"], row["name"], level),
    )
    return f"✅ Skill **{row['name']}** (Lv {level}) ditambahkan ke {char_name}."

def edit_skill(guild_id: int, char_name: str, skill_name: str, level: int) -> str:
    execute(
        guild_id,
        "UPDATE skills SET level=? WHERE guild_id=? AND char_name=? AND name=?",
        (level, guild_id, char_name, skill_name.title()),
    )
    return f"⚡ Level skill **{skill_name.title()}** milik {char_name} diubah jadi {level}."

def remove_skill(guild_id: int, char_name: str, skill_name: str) -> str:
    execute(
        guild_id,
        "DELETE FROM skills WHERE guild_id=? AND char_name=? AND name=?",
        (guild_id, char_name, skill_name.title()),
    )
    return f"🗑️ Skill **{skill_name.title()}** dihapus dari {char_name}."

def reset_skills(guild_id: int, char_name: str) -> str:
    execute(guild_id, "DELETE FROM skills WHERE guild_id=? AND char_name=?", (guild_id, char_name))
    return f"♻️ Semua skill {char_name} direset."

def get_char_skills(guild_id: int, char_name: str):
    return fetchall(
        guild_id,
        "SELECT s.category, s.name, s.level FROM skills s WHERE s.guild_id=? AND s.char_name=? ORDER BY s.category",
        (guild_id, char_name),
    )

def get_all_skills(guild_id: int):
    return fetchall(
        guild_id,
        "SELECT char_name, category, name, level FROM skills WHERE guild_id=? ORDER BY char_name, category",
        (guild_id,),
    )

def use_skill(guild_id: int, char_name: str, skill_name: str):
    row = fetchone(
        guild_id,
        "SELECT s.category, s.name, s.level, l.effect, l.drawback, l.cost "
        "FROM skills s "
        "JOIN skill_library l ON s.skill_id = l.id "
        "WHERE s.guild_id=? AND s.char_name=? AND s.name=?",
        (guild_id, char_name, skill_name.title()),
    )
    return row
