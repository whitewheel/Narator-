import os
import json
import logging
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# ============ ENV ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SHEET_URL = os.getenv("SHEET_URL")
# Simpan JSON service account ke ENV dengan nama GS_CREDS_JSON
GS_CREDS_JSON = os.getenv("GS_CREDS_JSON")

if not DISCORD_TOKEN:
    raise RuntimeError("ENV DISCORD_TOKEN kosong.")
if not GS_CREDS_JSON:
    raise RuntimeError("ENV GS_CREDS_JSON kosong (isi dengan string JSON credential).")
if not SHEET_URL:
    logger.warning("ENV SHEET_URL kosong. Bot tetap jalan, tapi fitur sheet tidak aktif.")

# ============ GOOGLE SHEETS AUTH ============
# Railway tidak punya file lokal credentials.json by default.
# Jadi kita parse dari ENV yang berisi JSON string.
try:
    creds_dict = json.loads(GS_CREDS_JSON)
except json.JSONDecodeError as e:
    raise RuntimeError(f"GS_CREDS_JSON bukan JSON valid: {e}")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gs_client = gspread.authorize(creds)

# Opsional: tes koneksi ke sheet saat startup
def test_sheet():
    if not SHEET_URL:
        return None
    sh = gs_client.open_by_url(SHEET_URL)
    ws = sh.sheet1
    val = ws.acell("A1").value
    logger.info(f"Google Sheets OK. A1='{val}'")
    return ws

# ============ DISCORD BOT ============
intents = discord.Intents.default()
intents.message_content = True  # WAJIB: aktifkan juga di Discord Developer Portal
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    try:
        test_sheet()
    except Exception as e:
        logger.error(f"Gagal tes Google Sheet: {e}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Contoh command sederhana
    if message.content.strip().lower().startswith("!ping"):
        await message.channel.send("Pong!")

    if message.content.strip().lower().startswith("!sheet"):
        if not SHEET_URL:
            await message.channel.send("Sheet belum diset. Set ENV SHEET_URL dulu.")
            return
        try:
            sh = gs_client.open_by_url(SHEET_URL)
            ws = sh.sheet1
            # Tulis timestamp ke baris baru
            ws.append_row(["Hello from Railway", str(message.author), str(message.created_at)])
            await message.channel.send("✅ Tersimpan ke Google Sheet.")
        except Exception as e:
            logger.exception("Error akses sheet:")
            await message.channel.send(f"❌ Gagal akses sheet: {e}")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
