import discord  # Untuk bot Discord
import openai   # Untuk akses OpenAI GPT
import os
import gspread  # Untuk koneksi Google Sheet
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------------------------
# INISIALISASI API OPENAI & GOOGLE SHEET
# -----------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# #INI# Autentikasi Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gs_client = gspread.authorize(creds)

# #INI# URL Sheet kamu
sheet_url = "https://docs.google.com/spreadsheets/d/1oWjMfSLm-L_3bgpop7YtUVTCgnTrdKYcmIivq-uXMzg/edit?usp=sharing"
spreadsheet = gs_client.open_by_url(sheet_url)

# -----------------------------------------------
# DISCORD BOT
# -----------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot is ready as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # #INI# Tanya ke OpenAI
    if message.content.startswith('!tanya '):
        prompt = message.content[7:]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        await message.channel.send(response['choices'][0]['message']['content'])

    # #INI# Baca isi Google Sheet
    elif message.content.startswith('!log'):
        sheet = spreadsheet.sheet1
        rows = sheet.get_all_values()
        response_text = ""
        for row in rows[:5]:  # Hanya 5 baris pertama
            response_text += ", ".join(row) + "\n"
        await message.channel.send(f"📄 Isi Sheet:\n{response_text}")

    # #INI# Tambah Sheet Baru
    elif message.content.startswith('!tambahsheet '):
        nama = message.content[14:].strip()
        try:
            spreadsheet.add_worksheet(title=nama, rows="100", cols="20")
            await message.channel.send(f"✅ Sheet baru `{nama}` berhasil dibuat.")
        except Exception as e:
            await message.channel.send(f"❌ Gagal buat sheet: {e}")

# #INI# Token Discord
client.run(os.getenv("DISCORD_TOKEN"))
