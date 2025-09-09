import os
import io
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

DISCORD_LIMIT = 2000
FALLBACK_FILE_LIMIT = 10000  # kalau jawaban > 10k char, kirim file txt

def split_message(text, limit=DISCORD_LIMIT):
    """
    Pecah text panjang jadi potongan <= limit karakter.
    """
    if len(text) <= limit:
        return [text]
    return [text[i:i+limit] for i in range(0, len(text), limit)]

async def send_long(message, content: str):
    """
    Kirim jawaban panjang:
    - <=2000 → kirim biasa
    - <=10k → pecah jadi beberapa pesan
    - >10k → kirim sebagai file .txt
    """
    if len(content) <= DISCORD_LIMIT:
        await message.channel.send(content)
        return

    if len(content) <= FALLBACK_FILE_LIMIT:
        parts = split_message(content, DISCORD_LIMIT)
        for idx, part in enumerate(parts, start=1):
            await message.channel.send(f"**Bagian {idx}/{len(parts)}**\n{part}")
        return

    # kalau sangat panjang → file txt
    data = io.StringIO(content)
    await message.channel.send(
        "📄 Jawaban panjang banget, aku kirim dalam file ya 👇",
        file=discord.File(fp=data, filename="jawaban.txt"),
    )

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

        await message.channel.send("🤖...")

        try:
            response = client_gpt.chat.completions.create(
                model="gpt-4o",  # ✅ pakai GPT-4o
                messages=[
                    {"role": "system", "content": "Kamu adalah asisten yang ramah."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
            )
            answer = response.choices[0].message.content

            # gunakan helper untuk kirim jawaban
            await send_long(message, answer)

        except Exception as e:
            logger.error(f"❌ Error GPT: {e}")
            await message.channel.send(f"❌ Error: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
