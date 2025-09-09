import discord
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import math

# ============ LOAD ENV & API KEY ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

# ============ GOOGLE SHEETS SETUP ============
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credential JSON dari ENV variable (Railway friendly)
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gs_client = gspread.authorize(creds)

sheet_url = "https://docs.google.com/spreadsheets/d/1oWjMfSLm-L_3bgpop7YtUVTCgnTrdKYcmIivq-uXMzg/edit#gid=0"
spreadsheet = gs_client.open_by_url(sheet_url)
sheet = spreadsheet.sheet1

# ============ DISCORD SETUP ============
intents = discord.Intents.default()
intents.message_content = True  # 🔥 WAJIB agar bisa baca pesan dari user
client = discord.Client(intents=intents)

# ============ HELPERS ============
DISCORD_LIMIT = 2000

def split_for_discord(text: str, limit: int = DISCORD_LIMIT):
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        parts.append(text[:limit])
        text = text[limit:]
    return parts

def get_worksheet_by_name_or_default(name: str = None):
    try:
        if name:
            return spreadsheet.worksheet(name)
        return spreadsheet.sheet1
    except Exception:
        return spreadsheet.sheet1

def read_rows_as_json(ws, max_rows: int = 300):
    try:
        rows = ws.get_all_records()
        if max_rows and len(rows) > max_rows:
            rows = rows[:max_rows]
        return rows
    except Exception as e:
        return {"error": str(e)}

def build_grounded_messages(question: str, rows_json):
    system_msg = (
        "Kamu adalah asisten yang menjawab BERDASARKAN DATA SHEET yang diberikan.\n"
        "- Jika jawaban tidak dapat ditemukan di data, katakan persis: 'Maaf, datanya tidak ada di sheet.'\n"
        "- Jika ada beberapa kemungkinan, sebutkan temuan yang relevan dan alasan singkat.\n"
        "- Jangan mengada-ada; jangan gunakan pengetahuan umum di luar data."
    )
    user_msg = (
        f"Pertanyaan: {question}\n\n"
        f"DataSheet(JSON):\n{json.dumps(rows_json, ensure_ascii=False)}"
    )
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]

async def reply_long(message, text: str):
    for part in split_for_discord(text):
        await message.channel.send(part)

# ============ EVENTS ============
@client.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"📨 Pesan diterima: {message.content}")

    if message.content.startswith("!tanya "):
        prompt = message.content[7:].strip()
        try:
            await message.channel.send("Check...")
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            await reply_long(message, response['choices'][0]['message']['content'])
        except Exception as e:
            await message.channel.send(f"⚠️ Error OpenAI: {str(e)}")

    elif message.content.startswith("!tanya data "):
        raw = message.content[len("!tanya data "):].strip()
        if "|" in raw:
            sheet_name, question = [x.strip() for x in raw.split("|", 1)]
        else:
            sheet_name, question = None, raw

        try:
            ws = get_worksheet_by_name_or_default(sheet_name)
            rows_json = read_rows_as_json(ws, max_rows=300)
            if isinstance(rows_json, dict) and rows_json.get("error"):
                await message.channel.send(f"⚠️ Gagal baca sheet: {rows_json['error']}")
                return

            await message.channel.send("🔄 Sedang memproses data sheet...")
            messages = build_grounded_messages(question, rows_json)
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                temperature=0
            )
            answer = response['choices'][0]['message']['content']
            header = f"**🧾 Jawaban berbasis data** (sheet: `{ws.title}`):\n"
            await reply_long(message, header + answer)
        except Exception as e:
            await message.channel.send(f"⚠️ Gagal proses pertanyaan data: {str(e)}")

    elif message.content.startswith("!sheet lihat"):
        try:
            rows = sheet.get_all_records()
            if not rows:
                await message.channel.send("📄 Sheet kosong.")
                return
            response = "**📋 Isi Sheet1:**\n"
            for i, row in enumerate(rows, 1):
                response += f"{i}. {row}\n"
            await reply_long(message, response)
        except Exception as e:
            await message.channel.send(f"⚠️ Gagal lihat sheet: {str(e)}")

    elif message.content.startswith("!sheet tambah "):
        nama_sheet = message.content[len("!sheet tambah "):].strip()
        try:
            spreadsheet.add_worksheet(title=nama_sheet, rows="100", cols="20")
            await message.channel.send(f"✅ Sheet baru '{nama_sheet}' berhasil dibuat.")
        except Exception as e:
            await message.channel.send(f"⚠️ Gagal tambah sheet: {str(e)}")

# ============ JALANKAN BOT ============
client.run(DISCORD_TOKEN)
