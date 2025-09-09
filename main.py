import os
import discord
from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@bot.event
async def on_ready():
    print(f"🤖 Bot aktif sebagai {bot.user}")

@bot.command()
async def tanya(ctx, *, prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        await ctx.send(reply)
    except Exception as e:
        await ctx.send(f"❌ Terjadi error:\n{str(e)}")

bot.run(os.getenv("DISCORD_TOKEN"))
