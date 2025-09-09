import discord
import openai
import os

# WAJIB! Aktifkan intent agar bot bisa baca pesan
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Ambil API Key dari environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@client.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!tanya "):
        prompt = message.content[7:]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response['choices'][0]['message']['content']
            await message.channel.send(reply)

        except Exception as e:
            await message.channel.send(f"❌ Error: {str(e)}")

client.run(os.getenv("DISCORD_TOKEN"))
