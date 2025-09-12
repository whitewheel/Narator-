# cogs/gm_cog.py
import os, random
import discord
from discord.ext import commands
from memory import init_db, save_memory, get_recent, get_latest_summary, write_summary, mark_archived

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
try:
    from openai import OpenAI
    oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    oai = None

GM_HINT = ("Kamu adalah Game Master (GM) dunia cyberpunk Technonesia. "
           "Gaya sinematik, padat, responsif. Balas sebagai narator; boleh menjadi NPC bila relevan. "
           "Jangan langsung men-drop quest resmi—biarkan lahir dari percakapan.")

def _fmt(rows):
    # rows datang newest-first → balikan oldest→newest singkat
    return "\n".join(f"[{cat}] {content}" for (_id,cat,content,meta,ts) in reversed(rows[-10:]))

class GM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.gm_channels = set()  # {(guild_id, channel_id)}

    @commands.group(name="gm", invoke_without_command=True)
    async def gm(self, ctx):
        await ctx.send("Gunakan: `!gm on`, `!gm off`, `!gm next`, `!backup`")

    @gm.command(name="on")
    async def gm_on(self, ctx):
        key = (str(ctx.guild.id), str(ctx.channel.id))
        self.gm_channels.add(key)
        save_memory(ctx.guild.id, ctx.channel.id, ctx.author.id, "system", "GM ON", {})
        await ctx.send("✅ GM mode **ON** untuk channel ini. Tulis natural tanpa `!`.")

    @gm.command(name="off")
    async def gm_off(self, ctx):
        key = (str(ctx.guild.id), str(ctx.channel.id))
        self.gm_channels.discard(key)
        save_memory(ctx.guild.id, ctx.channel.id, ctx.author.id, "system", "GM OFF", {})
        await ctx.send("🛑 GM mode **OFF** untuk channel ini.")

    @gm.command(name="next")
    async def gm_next(self, ctx):
        await self._narrate(ctx.channel, None)

    @gm.command(name="backup")
    async def gm_backup(self, ctx):
        from memory import export_all_json
        path = export_all_json("/data/memory_export.json")
        await ctx.send(f"📦 Backup selesai: `{path}` (tersimpan di volume)")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or msg.content.strip().startswith("!") or not msg.guild:
            return
        key = (str(msg.guild.id), str(msg.channel.id))
        if key not in self.gm_channels:
            return
        # simpan ucapan pemain ke history
        save_memory(msg.guild.id, msg.channel.id, msg.author.id, "history", msg.content,
                    {"author": msg.author.display_name})
        await self._narrate(msg.channel, msg.content)

    async def _narrate(self, channel: discord.TextChannel, player_text: str | None):
        g, ch = channel.guild.id, channel.id
        summary = get_latest_summary(g, ch) or "(Belum ada rekap.)"
        recent = get_recent(g, ch, None, 10)
        ctx_text = _fmt(recent)

        d20 = random.randint(1, 20)
        twist = ("Encounter kecil mungkin muncul" if d20<=5 else
                 "NPC relevan dapat muncul" if d20<=10 else
                 "Benih quest boleh disulut" if d20<=15 else
                 "Tambahkan ambient dunia (neon, drone, cuaca toksik)")

        prompt = f"""{GM_HINT}

# REKAP
{summary}

# RIWAYAT (lama→baru, ringkas)
{ctx_text}

# D20={d20}: {twist}

# ARAHAN
- Balas 3–6 kalimat narasi; jika pemain baru bicara, tanggapi niatnya.
- Boleh menjadi NPC singkat.
- Jangan langsung men-drop quest resmi; pancing lewat dialog dulu.
- Tawarkan opsi aksi berikutnya.

# INPUT PEMAIN (opsional)
{player_text or "(tidak ada)"}
"""

        text = await self._ask(prompt)
        text = text.strip() if text else "(Suasana neon berpendar; GM mengamati...)"
        await channel.send(text)
        save_memory(g, ch, "gm", "history", text, {"role": "gm", "d20": d20})

    async def _ask(self, prompt: str) -> str | None:
        if not oai:
            return "Lampu neon memantul di genangan, drone patroli melintas—kota terasa waspada malam ini."
        try:
            r = oai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"Kamu adalah GM/Narator."},
                          {"role":"user","content":prompt}],
                temperature=0.8, max_tokens=350
            )
            return r.choices[0].message.content
        except Exception as e:
            return f"(Gagal meminta narasi AI: {e})"

async def setup(bot):
    await bot.add_cog(GM(bot))
