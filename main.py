import os
import io
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from openai import OpenAI

# === DB (SQLite) ===
# pastikan file memory.py sudah ada (yang tadi kita buat)
from memory import init_db, DB_PATH  # NEW

# ====== LOGGING ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bot")

# ====== LOAD ENV ======
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ ENV DISCORD_TOKEN kosong.")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ ENV OPENAI_API_KEY kosong.")

# Inisialisasi DB (akan membuat / membuka memory.db di volume)
init_db()  # NEW
logger.info(f"📦 SQLite DB path: {DB_PATH}")  # NEW

# ====== GPT CLIENT ======
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD BOT ======
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        exts = [
            "cogs.roll",
            "cogs.poll",
            "cogs.gpt",
            "cogs.initmem",
            "cogs.karakter_status",
            "cogs.enemy_status",
            "cogs.multi",
            "cogs.history",
            "cogs.image",
            "cogs.quest",     # ✅ BARU
            "cogs.item",      # ✅ BARU
            "cogs.npc",       # ✅ BARU
            "cogs.favor",     # ✅ BARU
            "cogs.scene",     # ✅ BARU
            "cogs.status_alias",   # QoL alias: !dmg, !heal, !ene±, !stam±
            "cogs.help",           # Custom help
            "cogs.gm_cog",         # NEW: GM/Narrator mode
        ]
        for ext in exts:
            try:
                await self.load_extension(ext)
                logger.info(f"✅ Loaded {ext}")
            except Exception as e:
                logger.error(f"❌ Gagal load {ext}: {e}")

# ✅ Matikan help bawaan supaya tidak bentrok dengan cogs.help
bot = MyBot(command_prefix="!", intents=intents, help_command=None)
try:
    bot.remove_command("help")
except Exception:
    pass

DISCORD_LIMIT = 2000
FALLBACK_FILE_LIMIT = 10000

def split_message(text, limit=DISCORD_LIMIT):
    if len(text) <= limit:
        return [text]
    return [text[i:i+limit] for i in range(0, len(text), limit)]

async def send_long(ctx, content: str):
    if len(content) <= DISCORD_LIMIT:
        await ctx.send(f"```{content}```")
        return
    if len(content) <= FALLBACK_FILE_LIMIT:
        parts = split_message(content, DISCORD_LIMIT)
        for idx, part in enumerate(parts, start=1):
            await ctx.send(f"**Bagian {idx}/{len(parts)}**\n```{part}```")
        return
    data = io.StringIO(content)
    await ctx.send(
        "📄 Jawaban panjang banget, aku kirim dalam file ya 👇",
        file=discord.File(fp=data, filename="jawaban.txt"),
    )

@bot.event
async def on_ready():
    cmds = ", ".join(sorted(c.name for c in bot.commands))
    logger.info(f"🤖 Bot login sebagai {bot.user} | Commands: [{cmds}]")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command tidak dikenal. Coba `!help`.")
    else:
        await ctx.send("⚠️ Terjadi error, coba lagi nanti.")
        logger.error(f"Error di command {getattr(ctx, 'command', None)}: {error}")

@bot.command(name="ask")
async def ask(ctx, *, prompt: str = None):
    if not prompt:
        await send_long(ctx, "⚠️ Tolong kasih pertanyaan setelah `!ask`")
        return
    msg = await ctx.send("🤖...")
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Kamu adalah asisten yang ramah."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
        )
        answer = response.choices[0].message.content
        await send_long(ctx, answer)
    except Exception as e:
        logging.getLogger("bot").error(f"❌ Error GPT: {e}")
        await send_long(ctx, f"❌ Error: {str(e)}")
    finally:
        try: await msg.delete()
        except Exception: pass

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
