import os
import discord
from discord.ext import commands
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="img")
    async def generate_image(self, ctx, *, prompt: str):
        """Generate gambar dari prompt. Contoh: !img cyberpunk dragon"""
        await ctx.send("🎨 Sedang membuat gambar...")

        try:
            r = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="512x512"
            )
            url = r.data[0].url
            await ctx.send(f"🖼️ {prompt}\n{url}")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(ImageGen(bot))
