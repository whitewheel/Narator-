import io
import json
from datetime import datetime
import discord
from discord.ext import commands
from memory import save_memory, get_recent

TIMELINE_CATEGORY = "timeline"
DEFAULT_LIMIT = 15
DISCORD_LIMIT = 2000

# ===== Utils =====
def _split_blocks(text: str, limit: int = DISCORD_LIMIT):
    if len(text) <= limit: return [text]
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def _fmt_ts(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z",""))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts_str

def _fmt_event_row(row, ctx: commands.Context | None = None) -> str:
    _id, _cat, content, meta, ts = row
    try:
        data = json.loads(content) if isinstance(content, str) else (content or {})
        m = meta or {}
    except Exception:
        data, m = {}, (meta or {})

    code = data.get("code") or m.get("code") or "-"
    title = data.get("title") or m.get("title") or "Event"
    details = (data.get("details") or "").strip()
    etype = data.get("type") or m.get("type") or "-"
    scene = data.get("scene") or m.get("scene")
    quest = data.get("quest") or m.get("quest")
    actors = data.get("actors") or m.get("actors") or []
    tags = data.get("tags") or m.get("tags") or []
    author_id = (m.get("author_id") or data.get("author_id"))
    author_mention = f"<@{author_id}>" if author_id else "-"

    bits = [f"[{_fmt_ts(ts)}] {etype.upper()} — {title} (code: {code})"]
    if scene: bits.append(f"(scene: {scene})")
    if quest: bits.append(f"(quest: {quest})")
    if actors: bits.append(f"(actors: {', '.join(actors)})")
    if tags: bits.append(f"(tags: {', '.join(tags)})")
    bits.append(f"(by {author_mention})")
    line_head = " ".join(bits)

    if details:
        return f"{line_head}\n  {details}"
    return line_head

# ===== Public Helper =====
def log_event(guild_id: str, channel_id: str, user_id: int, *,
              code: str | None = None,
              title: str, details: str = "", etype: str = "note",
              scene: str | None = None, quest: str | None = None,
              actors: list[str] | None = None, tags: list[str] | None = None):
    """Helper agar cog lain bisa mencatat timeline dengan kode unik."""
    payload = {
        "code": code,
        "title": title,
        "details": details,
        "type": etype,
        "scene": scene,
        "quest": quest,
        "actors": actors or [],
        "tags": tags or [],
        "author_id": user_id,
    }
    save_memory(
        guild_id, channel_id, user_id,
        TIMELINE_CATEGORY, json.dumps(payload),
        {"title": title, "type": etype, "code": code}
    )

# ===== Cog =====
class Timeline(commands.Cog):
    """Jurnal kampanye dengan kode unik untuk setiap event."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="timeline", invoke_without_command=True)
    async def timeline(self, ctx: commands.Context, limit: int = DEFAULT_LIMIT):
        """Tampilkan N event timeline terakhir (default 15)."""
        rows = get_recent(str(ctx.guild.id), str(ctx.channel.id), TIMELINE_CATEGORY, limit)
        if not rows:
            return await ctx.send("ℹ️ Timeline kosong.")

        lines = [ _fmt_event_row(r, ctx) for r in rows ]
        text = "\n\n".join(reversed(lines))
        for i, part in enumerate(_split_blocks(text), 1):
            prefix = f"**Timeline (bagian {i}/{len(_split_blocks(text))})**\n" if len(_split_blocks(text)) > 1 else "**Timeline**\n"
            await ctx.send(prefix + "```" + part + "```")

    @timeline.command(name="add")
    async def timeline_add(self, ctx: commands.Context, *, payload: str):
        """Tambah event manual ke timeline."""
        parts = [s.strip() for s in payload.split("|")]
        if len(parts) == 3:
            code, title, details = parts
        elif len(parts) == 2:
            code, title = parts; details = ""
        else:
            return await ctx.send("❌ Format salah. Pakai: CODE | Judul | detail")

        log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                  code=code, title=title, details=details, etype="note")
        await ctx.send(f"✅ Ditambahkan ke timeline: **{title}** (code: {code})")

    @timeline.command(name="full")
    async def timeline_full(self, ctx: commands.Context):
        """Tampilkan semua event timeline (hati-hati kalau ribuan)."""
        rows = get_recent(str(ctx.guild.id), str(ctx.channel.id), TIMELINE_CATEGORY, 5000)
        if not rows:
            return await ctx.send("ℹ️ Timeline kosong.")

        lines = [_fmt_event_row(r, ctx) for r in rows]
        text = "\n\n".join(reversed(lines))

        if len(text) < DISCORD_LIMIT:
            await ctx.send("**Timeline Lengkap**\n```" + text + "```")
        else:
            data = io.StringIO(text)
            await ctx.send("📜 Timeline lengkap terlalu panjang, dikirim sebagai file:", file=discord.File(data, "timeline_full.txt"))

    @timeline.command(name="search")
    async def timeline_search(self, ctx: commands.Context, *, keyword: str):
        """Cari event di timeline berdasarkan kata kunci."""
        rows = get_recent(str(ctx.guild.id), str(ctx.channel.id), TIMELINE_CATEGORY, 5000)
        if not rows:
            return await ctx.send("ℹ️ Timeline kosong.")

        matches = [r for r in rows if keyword.lower() in json.dumps(r).lower()]
        if not matches:
            return await ctx.send(f"🔎 Tidak ada event mengandung: `{keyword}`")

        lines = [_fmt_event_row(r, ctx) for r in matches]
        text = "\n\n".join(reversed(lines))

        if len(text) < DISCORD_LIMIT:
            await ctx.send(f"**Hasil Pencarian '{keyword}'**\n```" + text + "```")
        else:
            data = io.StringIO(text)
            await ctx.send(f"📜 Hasil pencarian '{keyword}' terlalu panjang, dikirim sebagai file:", file=discord.File(data, f"timeline_search_{keyword}.txt"))

async def setup(bot):
    await bot.add_cog(Timeline(bot))
