import discord
from discord.ext import commands
from openai import OpenAI
from talk_memory import append_chat, load_chat_history
from memory import get_recent

client = OpenAI()

def _key(ctx):
    return (str(ctx.guild.id), str(ctx.channel.id))

STYLE_SYSTEM = (
    "Kamu adalah NPC Voice Engine. Jawab sebagai NPC tersebut, konsisten, ringkas, dan relevan dengan konteks. "
    "Gunakan sudut pandang orang pertama jika cocok. Jangan membuat keputusan mengikat dunia tanpa GM. "
    "Nada menyesuaikan personality NPC bila ada di konteks."
)

class NPCTalk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name=\"npc\", invoke_without_command=True)
    async def npc(self, ctx):
        await ctx.send(\"Gunakan: `!npc talk <NamaNPC> <pesan>`, `!npc recall <NamaNPC>`, `!npc wipe <NamaNPC>`\")


    @npc.command(name=\"talk\")
    async def npc_talk(self, ctx, name: str, *, message: str):
        g, c = _key(ctx)
        # append user turn
        append_chat(g, c, ctx.author.id, \"npc_chat\", \"npc\", name, \"user\", message)

        # build context (recent npc info if any)
        history = load_chat_history(g, c, \"npc_chat\", \"npc\", name, limit=25)
        recent_npc_notes = []
        rows = get_recent(g, c, \"npc\", 50)
        for (_id, cat, content, meta, ts) in rows:
            if (meta or {}).get(\"name\", \"\").lower() == name.lower():
                recent_npc_notes.append(content[:200])

        messages = [{\"role\":\"system\",\"content\": STYLE_SYSTEM}]
        # inject short profile snippet if exists
        if recent_npc_notes:
            messages.append({\"role\":\"system\",\"content\": f\"Profil singkat NPC {name}: \" + \" | \".join(recent_npc_notes[-2:])})
        # add history
        for (role, text) in history[-12:]:  # last 12 turns
            mapped = \"assistant\" if role in (\"npc\",\"assistant\") else \"user\" if role==\"user\" else \"system\"
            messages.append({\"role\": mapped, \"content\": text})
        messages.append({\"role\":\"user\",\"content\": message})

        reply = \"(npc diam sebentar...)\"
        try:
            resp = client.chat.completions.create(
                model=\"gpt-4o-mini\",
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            reply = resp.choices[0].message.content.strip()
        except Exception as e:
            reply = f\"(NPC {name} terlihat bingung.)\"

        # append npc turn
        append_chat(g, c, ctx.author.id, \"npc_chat\", \"npc\", name, \"npc\", reply)
        embed = discord.Embed(title=f\"🗣️ {name}\", description=reply, color=discord.Color.blurple())
        await ctx.send(embed=embed)


    @npc.command(name=\"recall\")
    async def npc_recall(self, ctx, *, name: str):
        g, c = _key(ctx)
        history = load_chat_history(g, c, \"npc_chat\", \"npc\", name, limit=20)
        if not history:
            return await ctx.send(\"(belum ada percakapan)\" )
        text = \"\\n\".join([f\"- {r}: {t}\" for (r,t) in history[-10:]])
        await ctx.send(f\"**Riwayat {name} (10 terbaru):**\\n{text}\")


    @npc.command(name=\"wipe\")
    async def npc_wipe(self, ctx, *, name: str):
        # Soft-wipe by appending a system marker; full purge could be implemented in memory tool later.
        g, c = _key(ctx)
        append_chat(g, c, ctx.author.id, \"npc_chat\", \"npc\", name, \"system\", \"-- reset context --\")
        await ctx.send(f\"Riwayat percakapan NPC **{name}** ditandai reset.\")

async def setup(bot):
    await bot.add_cog(NPCTalk(bot))
