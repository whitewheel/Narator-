import os
from discord.ext import commands
from openai import OpenAI

client_gpt = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TRIPLE = "```"

class GPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="define")
    async def define(self, ctx, *, word: str):
        """Definisi singkat dari GPT. Contoh: !define entropi"""
        r = client_gpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"Jelaskan definisi singkat, jelas, beri contoh jika perlu."},
                {"role":"user","content":f"Definisikan: {word}"}
            ],
            max_tokens=300
        )
        await ctx.send(f"{TRIPLE}{r.choices[0].message.content}{TRIPLE}")

    @commands.command(name="summarize")
    async def summarize(self, ctx, *, text: str):
        """Ringkas teks panjang. Contoh: !summarize <teks>"""
        r = client_gpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"Ringkas padat, tampilkan poin penting."},
                {"role":"user","content":text}
            ],
            max_tokens=500
        )
        await ctx.send(f"{TRIPLE}{r.choices[0].message.content}{TRIPLE}")

    @commands.command(name="story")
    async def story(self, ctx, *, prompt: str):
        """Buat cerita pendek. Contoh: !story ksatria cyberpunk lawan naga neon"""
        r = client_gpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"Tulis cerita pendek imersif, 6–10 paragraf, bahasa Indonesia."},
                {"role":"user","content":prompt}
            ],
            max_tokens=900
        )
        await ctx.send(f"{TRIPLE}{r.choices[0].message.content}{TRIPLE}")

async def setup(bot):
    await bot.add_cog(GPT(bot))
