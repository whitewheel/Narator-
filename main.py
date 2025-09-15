import os
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from openai import OpenAI

# === DB (SQLite) ===
from memory import init_db, DB_PATH

# === Utils ===
from utils.discord_tools import send_long

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

# Inisialisasi DB
init_db()
logger.info(f"📦 SQLite DB path: {DB_PATH}")

# ====== GPT CLIENT ======
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD BOT ======
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        exts = [
            # CORE SYSTEM
            "cogs.core.initmem",
            "cogs.core.karakter_status",
            "cogs.core.enemy_status",
            "cogs.core.status_alias",
            "cogs.core.history",
            "cogs.core.race_manager",
            "cogs.core.class_manager",

            # WORLD SYSTEM
            "cogs.world.quest",
            "cogs.world.npc",
            "cogs.world.favor",
            "cogs.world.scene",
            "cogs.world.item",
            "cogs.world.loot",
            "cogs.world.encyclopedia",
            "cogs.wiki",

            # UTILITY
            "cogs.utility.roll",
            "cogs.utility.poll",
            "cogs.utility.multi",
            "cogs.utility.help",
            "cogs.utility.help_ui",
        ]
        for ext in exts:
            try:
                await self.load_extension(ext)
                logger.info(f"✅ Loaded {ext}")
            except Exception as e:
                logger.error(f"❌ Gagal load {ext}: {e}")

# ✅ Matikan help bawaan supaya tidak bentrok
bot = MyBot(command_prefix=commands.when_mentioned_or("!", "/"),
            intents=intents, help_command=None)
try:
    bot.remove_command("help")
except Exception:
    pass

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
        logger.info(f"💬 GPT Prompt: {prompt}")
        logger.info(f"📝 GPT Answer (first 100 chars): {answer[:100]}...")
        await send_long(ctx, answer)
    except Exception as e:
        logger.error(f"❌ Error GPT: {e}")
        await send_long(ctx, f"❌ Error: {str(e)}")
    finally:
        try:
            await msg.delete()
        except Exception:
            pass

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
