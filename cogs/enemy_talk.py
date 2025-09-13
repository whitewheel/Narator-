import discord
from discord.ext import commands
from openai import OpenAI
from talk_memory import append_chat, load_chat_history
from memory import get_recent, save_memory

client = OpenAI()

def _key(ctx):
    return (str(ctx.guild.id), str(ctx.channel.id))

STYLE_MONSTER = (
    "Kamu adalah suara musuh MONSTER. Kalimat singkat, agresif, primal. Tidak sopan. Tidak perlu panjang."
)
STYLE_BOSS = (
    "Kamu adalah BOSS/ELITE musuh. Bicaralah karismatik, sinis, dan percaya diri. Ingat interaksi sebelumnya."
)
STYLE_HUMAN = (
    "Kamu adalah musuh HUMANOID/Manusia. Berakal, bisa negosiasi, bisa berbohong. Tetap konsisten pada riwayat."
)

def classify_enemy(guild_id: str, channel_id: str, name: str) -> str:
    \"\"\"Try to classify from enemy records; return 'monster' | 'boss' | 'human'\"\"\"
    rows = get_recent(guild_id, channel_id, "enemy", 100)
    name_l = name.lower()
    for (_id, cat, content, meta, ts) in rows:
        nm = (meta or {}).get("name", "").lower()
        if nm == name_l or name_l in (content or "").lower():
            # heuristics from content/meta
            role = (meta or {}).get("role", "").lower()
            if (meta or {}).get("boss", False) or "boss" in role or "elite" in role:
                return "boss"
            if any(k in (content or "").lower() for k in ["human","bandit","hunter","mercenary","soldier","guard"]):
                return "human"
            return "monster"
    return "monster"

class EnemyTalk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="enemy", invoke_without_command=True)
    async def enemy(self, ctx):
        await ctx.send("Gunakan: `!enemy talk <Nama> <pesan>`, `!enemy recall <Nama>`, `!enemy promote <Nama> <NPCName>`")


    @enemy.command(name="talk")
    async def enemy_talk(self, ctx, name: str, *, message: str):
        g, c = _key(ctx)
        kind = classify_enemy(g, c, name)
        append_chat(g, c, ctx.author.id, "enemy_chat", "enemy", name, "user", message)

        # choose style
        system_style = STYLE_MONSTER if kind=="monster" else STYLE_BOSS if kind=="boss" else STYLE_HUMAN
        history = load_chat_history(g, c, "enemy_chat", "enemy", name, limit=20)

        messages = [{"role":"system","content": system_style}]
        for (role, text) in history[-10:]:
            mapped = "assistant" if role in ("enemy","assistant") else "user" if role=="user" else "system"
            messages.append({"role": mapped, "content": text})
        messages.append({"role":"user","content": message})

        reply = "(musuh menggeram pelan...)"
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=120,
                temperature=0.8
            )
            reply = resp.choices[0].message.content.strip()
        except Exception as e:
            reply = reply

        append_chat(g, c, ctx.author.id, "enemy_chat", "enemy", name, "enemy", reply)
        color = discord.Color.red() if kind!="human" else discord.Color.dark_orange()
        title = f"☠️ {name}" if kind!="human" else f"🗡️ {name}"
        await ctx.send(embed=discord.Embed(title=title, description=reply, color=color))


    @enemy.command(name="recall")
    async def enemy_recall(self, ctx, *, name: str):
        g, c = _key(ctx)
        history = load_chat_history(g, c, "enemy_chat", "enemy", name, limit=20)
        if not history:
            return await ctx.send("(belum ada percakapan)" )
        text = "\n".join([f"- {r}: {t}" for (r,t) in history[-10:]])
        await ctx.send(f"**Riwayat {name} (10 terbaru):**\n{text}")

    @enemy.command(name="promote")
    async def enemy_promote(self, ctx, name: str, *, npc_name: str):
        \"\"\"Promote enemy jadi NPC dengan nama baru (atau sama).\"\"\"
        g, c = _key(ctx)
        # Create a marker in memory
        save_memory(g, c, ctx.author.id, "npc", f"Promoted from enemy: {name}", {"name": npc_name})
        append_chat(g, c, ctx.author.id, "enemy_chat", "enemy", name, "system", f"-- promoted to NPC {npc_name} --")
        await ctx.send(f"Enemy **{name}** dipromosikan jadi NPC **{npc_name}**.")

async def setup(bot):
    await bot.add_cog(EnemyTalk(bot))
