# services/effect_service.py
import json
import re
from typing import Dict, List, Optional, Tuple
from utils.db import execute, fetchone, fetchall

# ===============================
# Konfigurasi & Mode Efek
# ===============================
# Mode perilaku saat apply ulang efek yang sama:
# - "multi-instance": tambah instance baru, masing2 punya durasi sendiri
# - "refresh": hanya 1 efek; apply ulang me-refresh durasi (tidak dobel)
# - "stack": 1 efek; apply ulang menambah stack (Lv naik), durasi di-refresh
# - "unique": abaikan jika sudah ada
DEFAULT_STACK_MAX = 3  # untuk efek "stack" jika tidak ditentukan

# ===============================
# Bootstrap Tabel Library Efek
# ===============================
def ensure_effects_table(guild_id: int):
    execute(guild_id, """
    CREATE TABLE IF NOT EXISTS effects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,              -- 'buff' / 'debuff'
        target_stat TEXT,       -- 'hp','ac','attack','stamina','energy', atau comma: 'hp,ac'
        formula TEXT,           -- '1d4', '-1', '+1', '0', dll (informasi, TIDAK otomatis dipakai hitung)
        duration INTEGER,       -- default durasi saat apply
        stack_mode TEXT,        -- 'multi-instance'|'refresh'|'stack'|'unique'
        max_stack INTEGER DEFAULT 3,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

def add_effect_lib(
    guild_id: int,
    name: str,
    e_type: str,
    target_stat: str,
    formula: str,
    duration: int,
    stack_mode: str,
    description: str,
    max_stack: Optional[int] = None
) -> None:
    ensure_effects_table(guild_id)
    if max_stack is None:
        max_stack = DEFAULT_STACK_MAX if stack_mode == "stack" else 1
    execute(guild_id, """
    INSERT OR REPLACE INTO effects
      (name, type, target_stat, formula, duration, stack_mode, max_stack, description)
    VALUES (?,?,?,?,?,?,?,?)
    """, (name.lower(), e_type, target_stat, formula, int(duration), stack_mode, int(max_stack), description))

def get_effect_lib(guild_id: int, name: str) -> Optional[Dict]:
    ensure_effects_table(guild_id)
    return fetchone(guild_id, "SELECT * FROM effects WHERE name=?", (name.lower(),))

def list_effects_lib(guild_id: int) -> List[Dict]:
    ensure_effects_table(guild_id)
    return fetchall(guild_id, "SELECT * FROM effects ORDER BY name ASC")

def remove_effect_lib(guild_id: int, name: str) -> bool:
    ensure_effects_table(guild_id)
    row = fetchone(guild_id, "SELECT id FROM effects WHERE name=?", (name.lower(),))
    if not row:
        return False
    execute(guild_id, "DELETE FROM effects WHERE id=?", (row["id"],))
    return True

# ===============================
# Helpers Entity & Effects JSON
# ===============================
def _table_for_target(ttype: str) -> str:
    if ttype == "enemy": return "enemies"
    if ttype == "ally": return "allies"
    return "characters"

def _find_target(guild_id: int, name: str) -> Optional[Tuple[str, Dict]]:
    """Cari karakter/enemy/ally berdasarkan nama. Urutan: characters -> enemies -> allies."""
    for table in ["characters", "enemies", "allies"]:
        row = fetchone(guild_id, f"SELECT * FROM {table} WHERE name=?", (name,))
        if row:
            return table, row
    return None

def _load_effects(row: Dict) -> List[Dict]:
    try:
        return json.loads(row.get("effects") or "[]")
    except Exception:
        return []

def _save_effects(guild_id: int, table: str, row_id: int, effects: List[Dict]) -> None:
    execute(guild_id, f"UPDATE {table} SET effects=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(effects), row_id))

def _pretty_name(name: str) -> str:
    return name.replace("_", " ").title()

def _match_effect_instance(inst: Dict, lib_name: str) -> bool:
    return (inst.get("id") or "").lower() == lib_name.lower()

# ===============================
# APPLY / CLEAR / QUERY
# ===============================
async def apply_effect(guild_id: int, target_name: str, effect_name: str, override_duration: Optional[int] = None) -> Tuple[bool, str]:
    """Apply efek dari LIBRARY ke target (auto cari char/enemy/ally). TIDAK melakukan damage; hanya menempelkan status."""
    found = _find_target(guild_id, target_name)
    if not found:
        return False, f"❌ Target **{target_name}** tidak ditemukan."
    table, row = found

    lib = get_effect_lib(guild_id, effect_name)
    if not lib:
        return False, f"❌ Efek **{effect_name}** tidak ada di library. Tambahkan dengan `!effect add`."

    effects = _load_effects(row)
    mode = (lib.get("stack_mode") or "unique").lower()
    max_stack = int(lib.get("max_stack") or (DEFAULT_STACK_MAX if mode == "stack" else 1))
    base_duration = int(override_duration if override_duration is not None else lib.get("duration") or 1)

    # cari existing instance dengan id yang sama
    existing_idx = None
    for i, e in enumerate(effects):
        if _match_effect_instance(e, lib["name"]):
            existing_idx = i
            break

    display = _pretty_name(lib["name"])
    e_type = lib["type"] or "debuff"

    if mode == "multi-instance":
        new_inst = {
            "id": lib["name"],
            "text": f"{display}",
            "type": e_type,
            "duration": base_duration,
            "stack": 1,
            "mode": mode,
            "formula": lib.get("formula") or "",
            "target_stat": lib.get("target_stat") or ""
        }
        effects.append(new_inst)
        _save_effects(guild_id, table, row["id"], effects)
        return True, f"☠️ {target_name} mendapat **{display}** ({lib.get('formula','')}) {base_duration} turn."

    if mode == "refresh":
        if existing_idx is None:
            new_inst = {
                "id": lib["name"],
                "text": f"{display}",
                "type": e_type,
                "duration": base_duration,
                "stack": 1,
                "mode": mode,
                "formula": lib.get("formula") or "",
                "target_stat": lib.get("target_stat") or ""
            }
            effects.append(new_inst)
        else:
            effects[existing_idx]["duration"] = base_duration
            effects[existing_idx]["formula"] = lib.get("formula") or effects[existing_idx].get("formula","")
        _save_effects(guild_id, table, row["id"], effects)
        return True, f"🔁 {target_name}: **{display}** di-refresh ({base_duration} turn)."

    if mode == "stack":
        if existing_idx is None:
            new_inst = {
                "id": lib["name"],
                "text": f"{display} Lv 1",
                "type": e_type,
                "duration": base_duration,
                "stack": 1,
                "mode": mode,
                "formula": lib.get("formula") or "",
                "target_stat": lib.get("target_stat") or ""
            }
            effects.append(new_inst)
            msg = f"📈 {target_name} mendapat **{display} Lv1** ({base_duration} turn)."
        else:
            cur = effects[existing_idx]
            new_stack = min(int(cur.get("stack", 1)) + 1, max_stack)
            cur["stack"] = new_stack
            cur["duration"] = base_duration
            cur["text"] = f"{display} Lv {new_stack}"
            cur["formula"] = lib.get("formula") or cur.get("formula","")
            msg = f"📈 {target_name}: **{display}** naik ke **Lv{new_stack}** ({base_duration} turn)."
        _save_effects(guild_id, table, row["id"], effects)
        return True, msg

    # unique
    if existing_idx is not None:
        return True, f"ℹ️ {target_name} sudah memiliki **{display}** (unique)."
    effects.append({
        "id": lib["name"],
        "text": f"{display}",
        "type": e_type,
        "duration": base_duration,
        "stack": 1,
        "mode": mode,
        "formula": lib.get("formula") or "",
        "target_stat": lib.get("target_stat") or ""
    })
    _save_effects(guild_id, table, row["id"], effects)
    return True, f"✅ {target_name} mendapat **{display}** ({base_duration} turn)."

def _filter_effects(effects: List[Dict], *, remove_id: Optional[str] = None, is_buff: Optional[bool] = None) -> List[Dict]:
    if remove_id:
        return [e for e in effects if (e.get("id","") or "").lower() != remove_id.lower()]
    if is_buff is None:
        return []
    # clear buff/debuff by type
    t = "buff" if is_buff else "debuff"
    return [e for e in effects if (e.get("type") or "").lower() != t]

async def clear_effects(guild_id: int, target_name: str, effect_id: Optional[str] = None, is_buff: Optional[bool] = None) -> Tuple[bool,str]:
    found = _find_target(guild_id, target_name)
    if not found:
        return False, f"❌ Target **{target_name}** tidak ditemukan."
    table, row = found
    effects = _load_effects(row)

    if effect_id is None and is_buff is None:
        # clear all
        _save_effects(guild_id, table, row["id"], [])
        return True, f"🧹 Semua efek pada **{target_name}** dihapus."
    new_effects = _filter_effects(effects, remove_id=effect_id, is_buff=is_buff)
    _save_effects(guild_id, table, row["id"], new_effects)
    if effect_id:
        return True, f"🧹 Efek **{_pretty_name(effect_id)}** dihapus dari **{target_name}**."
    return True, f"🧹 Efek {'buff' if is_buff else 'debuff'} dibersihkan dari **{target_name}**."

def get_active_effects(guild_id: int, target_name: str) -> Tuple[bool, str, List[Dict]]:
    found = _find_target(guild_id, target_name)
    if not found:
        return False, f"❌ Target **{target_name}** tidak ditemukan.", []
    table, row = found
    return True, table, _load_effects(row)

# ===============================
# TICK (manual-GM mode: laporan saja)
# ===============================
def _format_eff_line(e: Dict]) -> str:
    dur = int(e.get("duration", -1))
    dur_txt = f"{dur}" if dur >= 0 else "∞"
    stack = int(e.get("stack", 1))
    stack_txt = f" Lv{stack}" if stack > 1 and "Lv" not in (e.get("text") or "") else ""
    form = e.get("formula") or ""
    if form:
        return f"{e.get('text','')} {stack_txt} — {form} [Durasi: {dur_txt}]"
    return f"{e.get('text','')} {stack_txt} [Durasi: {dur_txt}]"

async def tick_effects(guild_id: int) -> Dict:
    """Kurangi durasi semua efek >0. Laporkan active & expired. TIDAK melakukan damage/penalti apa pun."""
    results = {"char": {}, "enemy": {}, "ally": {}}

    for ttype, table in [("char","characters"), ("enemy","enemies"), ("ally","allies")]:
        rows = fetchall(guild_id, f"SELECT * FROM {table}")
        for r in rows:
            name = r["name"]
            effs = _load_effects(r)
            remaining, expired = [], []
            for e in effs:
                d = int(e.get("duration", -1))
                if d == -1:
                    remaining.append(e)
                elif d > 1:
                    e["duration"] = d - 1
                    remaining.append(e)
                elif d == 1:
                    # habis setelah tick ini
                    expired.append(e)
                else:
                    # sudah 0 atau negatif (aman dihapus)
                    expired.append(e)

            _save_effects(guild_id, table, r["id"], remaining)
            if expired:
                for e in expired:
                    execute(guild_id, "INSERT INTO timeline (event) VALUES (?)",
                            (f"⌛ {name} kehilangan efek: {e.get('text','')}",))
            results[ttype][name] = {
                "active": remaining,
                "expired": expired
            }
    return results

# ===============================
# EMBED builder (untuk Cog)
# ===============================
def build_tick_embed(discord, guild_name: str, results: Dict):
    embed = discord.Embed(
        title="⏳ Tick Round Effects",
        description=f"Server: **{guild_name}**\n(Manual GM mode — tidak ada auto damage)",
        color=discord.Color.orange()
    )

    def section_for(ttype_key: str, header_icon: str, header_name: str):
        data = results.get(ttype_key) or {}
        if not data:
            return
        sec_lines = []
        for name, info in data.items():
            active_lines = [f"• {_format_eff_line(e)}" for e in info.get("active", [])] or ["-"]
            expired_lines = [f"• {e.get('text','')}" for e in info.get("expired", [])]
            block = f"**{name}**\n" \
                    f"✨ Active:\n" + "\n".join(active_lines)
            if expired_lines:
                block += "\n⌛ Expired:\n" + "\n".join(expired_lines)
            sec_lines.append(block)
        embed.add_field(name=f"{header_icon} {header_name}", value="\n\n".join(sec_lines), inline=False)

    section_for("char", "🧍", "Characters")
    section_for("enemy", "👹", "Enemies")
    section_for("ally", "🤝", "Allies")
    return embed
