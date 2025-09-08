
import discord
import openai
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)

openai.api_key = os.getenv("OPENAI_API_KEY")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!tanya "):
        prompt = message.content[7:]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        await message.channel.send(response['choices'][0]['message']['content'])

client.run(os.getenv("DISCORD_TOKEN"))
