# cogs/core/initmem.py
import asyncio
import json
import random
import re
import discord
from discord.ext import commands

from utils.db import execute, fetchone, fetchall
from cogs.world.timeline import log_event  # tetap dipakai untuk narasi/log

# ===============================
# DB Helpers & Setup
# ===============================

def _ensure_tables():
    # Tabel penyimpanan initiative per (guild_id, channel_id)
    execute("""
    CREATE TABLE IF NOT EXISTS initiative (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        channel_id TEXT,
        order_json TEXT DEFAULT '[]',  -- list of [name, score]
        ptr INTEGER DEFAULT 0,
        round INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Unique agar bisa UPSERT
    execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_initiative_gc
    ON initiative(guild_id, channel_id);
    """)

def _load_initiative(gid: str, cid: str):
    row = fetchone("SELECT * FROM initiative WHERE guild_id=? AND channel_id=?", (gid, cid))
    if not row:
        return {"order": [], "ptr": 0, "round": 1}
    try:
        order = json.loads(row.get("order_json") or "[]")
    except Exception:
        order = []
    return {"order": [(n, int(s)) for (n, s) in order], "ptr": int(row["ptr"] or 0), "round": int(row["round"] or 1)}

def _save_initiative(gid: str, cid: str, state: dict):
    order_json = json.dumps(state.get("order", []))
    ptr = int(state.get("ptr", 0))
    rnd = int(state.get("round", 1))
    # UPSERT (SQLite 3.24+)
    execute("""
    INSERT INTO initiative (guild_id, channel_id, order_json, ptr, round)
    VALUES (?,?,?,?,?)
    ON CONFLICT(guild_id, channel_id)
    DO UPDATE SET order_json=excluded.order_json, ptr=excluded.ptr, round=excluded.round, updated_at=CURRENT_TIMESTAMP;
    """, (gid, cid, order_json, ptr, rnd))

def _clear_initiative(gid: str, cid: str):
    execute("DELETE FROM initiative WHERE guild_id=? AND channel_id=?", (gid, cid))

# ===============================
# Utils
# ===============================

def _key(ctx):
    return (str(ctx.guild.id) if ctx.guild else "0", str(ctx.channel.id))

def _sorted_order(arr):
    # Sort: skor desc, nama asc
    return sorted(arr, key=lambda x: (-int(x[1]), x[0].lower()))

def _make_embed(ctx, title: str, s: dict, highlight: bool = True):
    order = s.get("order", [])
    ptr = s.get("ptr", 0)
    rnd = s.get("round", 1)

    embed = discord.Embed(
        title=title,
        description=f"📜 Round **{rnd}** • Channel: **{ctx.channel.name}**",
        color=discord.Color.red()
    )

    if not order:
        embed.add_field(name="⚔️ Initiative Order", value="(kosong)", inline=False)
        embed.set_footer(text="Tambahkan peserta dengan !init add <Nama> <Skor>")
        return embed

    lines = []
    for i, (name, score) in enumerate(order):
        marker = "👉" if highlight and i == ptr else "  "
        lines.append(f"{marker} {i+1}. **{name}** ({score})")

    embed.add_field(name="⚔️ Initiative Order", value="\n".join(lines), inline=False)
    embed.set_footer(text="Gunakan !init next / !next untuk lanjut giliran.")
    return embed

# ===============================
# Cog
# ===============================

class InitiativeMemory(commands.Cog):
    """
    Initiative tracker tersimpan di DB (persist).
    State in-memory disinkronkan ke DB pada setiap perubahan.
    Struktur per-channel:
    {
      "order": [(name, score), ...],
      "ptr": int,
      "round": int
    }
    """
    def __init__(self, bot):
        self.bot = bot
        self.state = {}
        _ensure_tables()

    # ---------- internal helpers ----------
    def _ensure_state(self, ctx):
        k = _key(ctx)
        if k not in self.state:
            # lazy load dari DB
            self.state[k] = _load_initiative(*k)
        return self.state[k]

    def _persist(self, ctx):
        gid, cid = _key(ctx)
        _save_initiative(gid, cid, self.state[(gid, cid)])

    # ---------- group ----------
    @commands.group(name="init", invoke_without_command=True)
    async def init_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Initiative Commands:\n"
            "• !init add <Nama> <Skor>\n"
            "• !init addmany \"Alice 18, Goblin 12, Borin 14\"  (bisa multi-line)\n"
            "• !init show   (alias: !order)\n"
            "• !init next   (alias: !next / !n)\n"
            "• !init setptr <index>  (mulai 1)\n"
            "• !init remove <Nama>\n"
            "• !init clear\n"
            "• !init shuffle\n"
            "• !init round [angka]\n"
            "• !engage / !victory\n"
            "```"
        )

    # ---------- add ----------
    @init_group.command(name="add")
    async def init_add(self, ctx, name: str, score: int):
        s = self._ensure_state(ctx)
        existing = {n: sc for (n, sc) in s["order"]}
        existing[name] = int(score)
        s["order"] = _sorted_order(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        self._persist(ctx)
        await ctx.send(f"✅ Ditambahkan/diupdate: **{name}** = `{score}`")

    @init_group.command(name="addmany")
    async def init_addmany(self, ctx, *, entries: str = None):
        """
        Tambah banyak peserta.
        Separator: koma (,), titik koma (;), pipe (|), baris baru.
        Format item: <Nama> <Skor>
        """
        if entries is None:
            raw = ctx.message.content
            idx = raw.lower().find("addmany")
            entries = raw[idx + len("addmany"):].strip() if idx != -1 else ""

        if not entries:
            return await ctx.send("⚠️ Format: `!init addmany Alice 18, Goblin 12` atau tulis daftar di baris berikutnya.")

        s = self._ensure_state(ctx)
        existing = {n: sc for (n, sc) in s["order"]}
        chunks = [c.strip() for c in re.split(r'[,\n;|]+', entries) if c.strip()]
        added = 0
        skipped = []

        for ch in chunks:
            m = re.match(r'^(?P<name>.+?)\s+(?P<score>-?\d+)\s*$', ch)
            if not m:
                skipped.append(ch)
                continue
            name = m.group('name').strip()
            score = int(m.group('score'))
            existing[name] = score
            added += 1

        s["order"] = _sorted_order(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0

        msg = f"✅ Ditambahkan/diupdate **{added}** peserta."
        if skipped:
            preview = ", ".join(skipped[:5]) + (" ..." if len(skipped) > 5 else "")
            msg += f" (di-skip: {preview})"
        self._persist(ctx)
        await ctx.send(msg)

    # ---------- remove / clear ----------
    @init_group.command(name="remove")
    async def init_remove(self, ctx, name: str):
        s = self._ensure_state(ctx)
        before = len(s["order"])
        s["order"] = [(n, sc) for (n, sc) in s["order"] if n.lower() != name.lower()]
        if len(s["order"]) < before:
            s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
            self._persist(ctx)
            await ctx.send(f"🗑️ Hapus **{name}**")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @init_group.command(name="clear")
    async def init_clear(self, ctx):
        gid, cid = _key(ctx)
        self.state[(gid, cid)] = {"order": [], "ptr": 0, "round": 1}
        self._persist(ctx)
        await ctx.send("🧹 Initiative channel ini direset.")
        # timeline log
        try:
            log_event(gid, cid, ctx.author.id,
                      code=None,
                      title="Initiative cleared",
                      details="--",
                      etype="init_clear",
                      tags=["combat","init"])
        except Exception:
            pass

    # ---------- show / order ----------
    @init_group.command(name="show")
    async def init_show(self, ctx):
        gid, cid = _key(ctx)
        # refresh dari DB biar tampilan akurat bila ada proses lain yang menulis
        self.state[(gid, cid)] = _load_initiative(gid, cid)
        s = self._ensure_state(ctx)
        self._persist(ctx)
        embed = _make_embed(ctx, "⚔️ Initiative Order", s)
        await ctx.send(embed=embed)
        # timeline log (encounter_start jika pertama kali tampilkan)
        try:
            names = [n for (n, _sc) in s.get("order", [])]
            log_event(gid, cid, ctx.author.id,
                      code=None,
                      title="Encounter dimulai",
                      details=f"Order: {', '.join(names)}" if names else "-",
                      etype="encounter_start",
                      actors=names,
                      tags=["combat","encounter","start"])
        except Exception:
            pass

    # ---------- next / setptr / round / shuffle ----------
    @init_group.command(name="next")
    async def init_next(self, ctx):
        s = self._ensure_state(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta. Tambah dengan `!init add <Nama> <Skor>`")

        s["ptr"] = (s["ptr"] + 1) % len(s["order"])
        if s["ptr"] == 0:
            s["round"] += 1
            await ctx.send(f"🔄 **Round {s['round']} dimulai!**")

        self._persist(ctx)
        embed = _make_embed(ctx, "⏭️ Initiative Next", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran", value=f"✨ **{current}**", inline=False)
        await ctx.send(embed=embed)

        # timeline log: turn advance
        try:
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title=f"Turn: {current}",
                      details=f"Round {s.get('round',1)}",
                      etype="turn",
                      actors=[current],
                      tags=["combat","turn"])
        except Exception:
            pass

    @init_group.command(name="setptr")
    async def init_setptr(self, ctx, index: int):
        s = self._ensure_state(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        idx = max(1, min(index, len(s["order"]))) - 1
        s["ptr"] = idx
        self._persist(ctx)
        embed = _make_embed(ctx, "📌 Pointer Diset Manual", s)
        await ctx.send(embed=embed)

    @init_group.command(name="round")
    async def init_round(self, ctx, value: int = None):
        s = self._ensure_state(ctx)
        if value is None:
            return await ctx.send(f"📜 Round saat ini: **{s['round']}**")
        s["round"] = max(1, int(value))
        self._persist(ctx)
        await ctx.send(f"📜 Round diset ke **{s['round']}**")
        # timeline
        try:
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title=f"Round set: {s['round']}",
                      details="--",
                      etype="round",
                      tags=["combat","round"])
        except Exception:
            pass

    @init_group.command(name="shuffle")
    async def init_shuffle(self, ctx):
        s = self._ensure_state(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        s["ptr"] = random.randint(0, len(s["order"]) - 1)
        self._persist(ctx)
        embed = _make_embed(ctx, "🎲 Shuffle Giliran", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    # ---------- Engage / Victory ----------
    @commands.command(name="engage", aliases=["start", "begin"])
    async def engage(self, ctx):
        s = self._ensure_state(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada data initiative. Tambahkan dulu dengan `!init add <Nama> <Skor>`.")
        drum = await ctx.send("🥁 Mengocok urutan giliran...")
        await asyncio.sleep(2)
        try:
            await drum.delete()
        except Exception:
            pass

        self._persist(ctx)
        embed = _make_embed(ctx, "⚔️ Encounter Dimulai!", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="victory", aliases=["end", "finish", "win"])
    async def victory(self, ctx, *flags):
        """
        Akhiri encounter.
          keep  - akhiri tanpa hapus daftar musuh
          clear - akhiri dan hapus daftar musuh (default)
          force - paksa selesai walau masih ada musuh > 0 HP
        """
        flags = {f.lower() for f in flags}
        keep_enemies = "keep" in flags
        force_end = "force" in flags

        gid, cid = _key(ctx)
        s = self._ensure_state(ctx)
        order = s.get("order", [])
        ptr = s.get("ptr", 0)
        rnd = s.get("round", 1)
        current_turn = order[ptr][0] if order else "-"

        # Ambil data musuh dari DB (bukan state cog)
        enemies = fetchall("SELECT name, hp FROM enemies WHERE guild_id=? AND channel_id=?", (gid, cid))
        total = len(enemies)
        alive = sum(1 for e in enemies if int(e["hp"] or 0) > 0)
        defeated = total - alive

        if alive > 0 and not force_end:
            return await ctx.send(
                f"⚠️ Masih ada **{alive}** musuh hidup. "
                "Gunakan `!victory force` untuk memaksa, atau `!victory keep` bila tidak ingin menghapus musuh."
            )

        # Ringkasan
        embed = discord.Embed(
            title="🎉 Victory!",
            description=f"Channel: **{ctx.channel.name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="👹 Rangkuman Musuh", value=f"Total: {total} • Alive: {alive} • Defeated: {defeated}", inline=False)
        embed.add_field(name="📜 Round Terakhir", value=str(rnd), inline=True)
        embed.add_field(name="✨ Giliran Terakhir", value=current_turn, inline=True)

        # Reset initiative (state + DB)
        self.state[(gid, cid)] = {"order": [], "ptr": 0, "round": 1}
        self._persist(ctx)

        # Clear musuh bila tidak keep
        if not keep_enemies:
            execute("DELETE FROM enemies WHERE guild_id=? AND channel_id=?", (gid, cid))

        await ctx.send(embed=embed)
        # timeline: encounter_end
        try:
            log_event(gid, cid, ctx.author.id,
                      code=None,
                      title="Encounter berakhir",
                      details="Victory",
                      etype="encounter_end",
                      tags=["combat","encounter","end"])
        except Exception:
            pass

    # ---------- Aliases global ----------
    @commands.command(name="next", aliases=["n"])
    async def alias_next(self, ctx):
        await self.init_next(ctx)

    @commands.command(name="order")
    async def alias_order(self, ctx):
        await self.init_show(ctx)

# ===============================
# Setup
# ===============================
async def setup(bot):
    cog = InitiativeMemory(bot)
    await bot.add_cog(cog)
    # (Opsional) Muat semua channel ke state saat start — aman untuk dilewati karena lazy load sudah ada
    # rows = fetchall("SELECT guild_id, channel_id FROM initiative", ())
    # for r in rows:
    #     try:
    #         key = (r["guild_id"], r["channel_id"])
    #         cog.state[key] = _load_initiative(*key)
    #     except Exception:
    #         pass
