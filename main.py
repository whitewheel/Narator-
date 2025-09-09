import discord
import openai
import os
import gspread
from google.oauth2.service_account import Credentials

intents = discord.Intents.default()
client = discord.Client(intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
gs_client = gspread.authorize(creds)

sheet_url = "https://docs.google.com/spreadsheets/d/1oWjMfSLm-L_3bgpop7YtUVTCgnTrdKYcmIivq-uXMzg/edit?usp=sharing"
sheet = gs_client.open_by_url(sheet_url)
worksheet = sheet.sheet1

@client.event
async def on_ready():
    print(f'✅ Bot Online sebagai {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!g "):
        prompt = message.content[7:]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response['choices'][0]['message']['content']

        await message.channel.send(reply)

        worksheet.append_row([str(message.author), prompt, reply])

client.run(os.getenv("DISCORD_TOKEN"))
