import os
import json
import base64
import logging
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# ============ ENV ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SHEET_URL = os.getenv("SHEET_URL")
GS_CREDS_JSON = os.getenv("GS_CREDS_JSON")  # isi ENV dengan JSON / BASE64 dari credentials.json

if not DISCORD_TOKEN:
    raise RuntimeError("ENV DISCORD_TOKEN kosong.")
if not GS_CREDS_JSON:
    raise RuntimeError("ENV GS_CREDS_JSON kosong (isi dengan JSON/BASE64 credential).")
if not SHEET_URL:
    logger.warning("ENV SHEET_URL kosong. Bot tetap jalan, tapi fitur sheet tidak aktif.")

# ============ GOOGLE SHEETS AUTH (kebal Invalid \escape) ============
def load_service_account_from_env(var_name="GS_CREDS_JSON"):
    raw = os.getenv(var_name)
    if not raw:
        raise RuntimeError(f"ENV {var_name} kosong.")

    # 1) Coba langsung JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 2) Coba BASE64 -> JSON
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            data = json.loads(decoded)
        except Exception:
            # 3) Jika ENV terbungkus kutip tunggal/ganda, coba kupas
            t = raw.strip()
            if (t.startswith("'") and t.endswith("'")) or (t.startswith('"') and t.endswith('"')):
                data = json.loads(t[1:-1])
            else:
                raise RuntimeError(
                    f"{var_name} bukan JSON/BASE64 valid. "
                    "Pastikan kamu paste seluruh isi credentials.json atau paste versi base64."
                )

    # Normalisasi private_key jika masih berisi literal '\\n'
    if isinstance(data.get("private_key"), str) and "\\n" in data["private_key"]:
        data["private_key"] = data["private_key"].replace("\\n", "\n")
    return data

try:
    creds_dict = load_service_account_from_env("GS_CREDS_JSON")
except Exception as e:
    raise RuntimeError(f"Gagal memuat kredensial Google: {e}")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gs_client = gspread.authorize(creds)
logger.info(f"Google SA email: {creds_dict.get('client_email')}")

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
