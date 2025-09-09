import os
import logging
import discord
from openai import OpenAI

# ====== LOGGING ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# ====== ENV ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ ENV DISCORD_TOKEN kosong.")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ ENV OPENAI_API_KEY kosong.")

# ====== GPT CLIENT ======
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD BOT ======
intents = discord.Intents.default()
intents.message_content = True  # wajib aktif di Developer Portal
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Trigger dengan prefix "!ask"
    if message.content.startswith("!ask"):
        prompt = message.content[len("!ask"):].strip()
        if not prompt:
            await message.channel.send("⚠️ Tolong kasih pertanyaan setelah `!ask`")
            return

        await message.channel.send("mohon tunggu...")

        try:
            response = client_gpt.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Kamu adalah asisten yang ramah."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
            )
            answer = response.choices[0].message.content
            await message.channel.send(answer)
        except Exception as e:
            logger.error(f"❌ Error GPT: {e}")
            await message.channel.send(f"❌ Error: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
