import discord
from discord.ext import commands
from memory import save_memory, get_recent, category_icon, template_for

import json
import re

class Quest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _key(self, ctx):
        return (str(ctx.guild.id), str(ctx.channel.id))

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 3:
            return None
        data = template_for("quest")
        data["title"] = parts[0]
        data["objective"] = parts[1]
        data["reward"] = parts[2]
        if len(parts) > 3:
            data["deadline"] = parts[3]
        data["hidden"] = "--hidden" in raw.lower()
        return data

    @commands.group(name="quest", invoke_without_command=True)
    async def quest(self, ctx):
        await ctx.send("Gunakan: `!quest add`, `!quest show`, `!quest done`, `!quest fail`, `!quest remove`, `!quest reveal`, `!quest detail`")

    @quest.command(name="add")
    async def quest_add(self, ctx, *, entry: str):
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format salah. Gunakan: `!quest add Judul | Objective | Reward | [Deadline] [--hidden]`")
        key = self._key(ctx)
        save_memory(key[0], key[1], ctx.author.id, "quest", json.dumps(data), {"title": data["title"]})
        await ctx.send(f"📜 Quest **{data['title']}** ditambahkan.")

    @quest.command(name="show")
    async def quest_show(self, ctx, filter: str = None):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "quest", 50)
        out = []
        for (_id, cat, content, meta, ts) in rows:
            try:
                q = json.loads(content)
                if filter == "done" and q["status"] != "complete":
                    continue
                elif filter == "failed" and q["status"] != "failed":
                    continue
                elif filter == "hidden" and not q.get("hidden", False):
                    continue
                elif filter not in ("all", "done", "failed", "hidden", None) and q["status"] != "pending":
                    continue
                if q.get("hidden", False) and not ctx.author.guild_permissions.manage_guild:
                    continue
                line = f"📌 **{q['title']}** → `{q['status']}`"
                out.append(line)
            except:
                continue
        if not out:
            return await ctx.send("Tidak ada quest.")
        await ctx.send("\n".join(out[:10]))

    @quest.command(name="done")
    async def quest_done(self, ctx, *, title: str):
        await self._update_status(ctx, title, "complete")

    @quest.command(name="fail")
    async def quest_fail(self, ctx, *, title: str):
        await self._update_status(ctx, title, "failed")

    @quest.command(name="remove")
    async def quest_remove(self, ctx, *, title: str):
        await self._update_status(ctx, title, "removed")

    @quest.command(name="reveal")
    async def quest_reveal(self, ctx, *, title: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "quest", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                q = json.loads(content)
                if q["title"].lower() == title.lower():
                    q["hidden"] = False
                    save_memory(key[0], key[1], ctx.author.id, "quest", json.dumps(q), {"title": q["title"]})
                    return await ctx.send(f"🔍 Quest **{q['title']}** kini terlihat.")
            except:
                continue
        await ctx.send("❌ Quest tidak ditemukan.")

    @quest.command(name="detail")
    async def quest_detail(self, ctx, *, title: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "quest", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                q = json.loads(content)
                if q["title"].lower() == title.lower():
                    embed = discord.Embed(
                        title=f"📜 {q['title']}",
                        description=f"🎯 {q['objective']}",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="🎁 Reward", value=q["reward"], inline=False)
                    if q.get("deadline"): embed.add_field(name="⏳ Deadline", value=q["deadline"], inline=True)
                    embed.add_field(name="📌 Status", value=q["status"], inline=True)
                    await ctx.send(embed=embed)
                    return
            except:
                continue
        await ctx.send("❌ Quest tidak ditemukan.")

    async def _update_status(self, ctx, title: str, new_status: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "quest", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                q = json.loads(content)
                if q["title"].lower() == title.lower():
                    q["status"] = new_status
                    save_memory(key[0], key[1], ctx.author.id, "quest", json.dumps(q), {"title": q["title"]})
                    return await ctx.send(f"✅ Status quest **{q['title']}** diset ke `{new_status}`.")
            except:
                continue
        await ctx.send("❌ Quest tidak ditemukan.")

async def setup(bot):
    await bot.add_cog(Quest(bot))