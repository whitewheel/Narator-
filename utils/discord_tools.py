import io
import discord

DISCORD_LIMIT = 2000
FALLBACK_FILE_LIMIT = 10000

def split_message(text, limit=DISCORD_LIMIT):
    return [text[i:i+limit] for i in range(0, len(text), limit)] or [""]

async def send_long(ctx, content: str):
    if len(content) <= DISCORD_LIMIT:
        await ctx.send(f"```{content}```")
        return
    if len(content) <= FALLBACK_FILE_LIMIT:
        parts = split_message(content, DISCORD_LIMIT)
        for idx, part in enumerate(parts, start=1):
            await ctx.send(f"**Bagian {idx}/{len(parts)}**\n```{part}```")
        return
    data = io.StringIO(content)
    await ctx.send(
        "📄 Jawaban panjang banget, aku kirim dalam file ya 👇",
        file=discord.File(fp=data, filename="jawaban.txt"),
    )
