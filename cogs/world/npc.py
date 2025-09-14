import discord
from discord.ext import commands
from memory import save_memory, get_recent, category_icon, template_for

import json

class NPC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _key(self, ctx):
        return (str(ctx.guild.id), str(ctx.channel.id))

    def _parse_entry(self, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 2:
            return None
        data = template_for("npc")
        data["name"] = parts[0]
        data["role"] = parts[1]
        if len(parts) > 2:
            data["attitude"] = parts[2].lower()
        if len(parts) > 3:
            data["notes"] = parts[3]
        data["hidden"] = "--hidden" in raw.lower()
        return data

    @commands.group(name="npc", invoke_without_command=True)
    async def npc(self, ctx):
        await ctx.send("Gunakan: `!npc add`, `!npc show`, `!npc remove`, `!npc reveal`, `!npc detail`")

    @npc.command(name="add")
    async def npc_add(self, ctx, *, entry: str):
        data = self._parse_entry(entry)
        if not data:
            return await ctx.send("⚠️ Format: `!npc add Nama | Peran | [Sikap] | [Catatan] [--hidden]`")
        key = self._key(ctx)
        save_memory(key[0], key[1], ctx.author.id, "npc", json.dumps(data), {"name": data["name"]})
        await ctx.send(f"👤 NPC **{data['name']}** ditambahkan.")

    @npc.command(name="show")
    async def npc_show(self, ctx, filter: str = None):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "npc", 50)
        out = []
        for (_id, cat, content, meta, ts) in rows:
            try:
                n = json.loads(content)
                if n.get("hidden", False) and not ctx.author.guild_permissions.manage_guild:
                    continue
                line = f"👤 **{n['name']}** ({n['role']})"
                if n.get("attitude"): line += f" • {n['attitude']}"
                out.append(line)
            except:
                continue
        if not out:
            return await ctx.send("Tidak ada NPC.")
        await ctx.send("\n".join(out[:10]))

    @npc.command(name="reveal")
    async def npc_reveal(self, ctx, *, name: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "npc", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                n = json.loads(content)
                if n["name"].lower() == name.lower():
                    n["hidden"] = False
                    save_memory(key[0], key[1], ctx.author.id, "npc", json.dumps(n), {"name": n["name"]})
                    return await ctx.send(f"🔍 NPC **{n['name']}** kini terlihat.")
            except:
                continue
        await ctx.send("❌ NPC tidak ditemukan.")

    @npc.command(name="remove")
    async def npc_remove(self, ctx, *, name: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "npc", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                n = json.loads(content)
                if n["name"].lower() == name.lower():
                    n["notes"] = "(deleted)"
                    save_memory(key[0], key[1], ctx.author.id, "npc", json.dumps(n), {"name": n["name"]})
                    return await ctx.send(f"🗑️ NPC **{n['name']}** dihapus.")
            except:
                continue
        await ctx.send("❌ NPC tidak ditemukan.")

    @npc.command(name="detail")
    async def npc_detail(self, ctx, *, name: str):
        key = self._key(ctx)
        rows = get_recent(key[0], key[1], "npc", 50)
        for (_id, cat, content, meta, ts) in rows:
            try:
                n = json.loads(content)
                if n["name"].lower() == name.lower():
                    embed = discord.Embed(
                        title=f"👤 {n['name']}",
                        description=f"Peran: **{n['role']}**",
                        color=discord.Color.greyple()
                    )
                    embed.add_field(name="🤝 Sikap", value=n.get("attitude","neutral"), inline=True)
                    embed.add_field(name="📝 Catatan", value=n.get("notes","-"), inline=False)
                    await ctx.send(embed=embed)
                    return
            except:
                continue
        await ctx.send("❌ NPC tidak ditemukan.")

async def setup(bot):
    await bot.add_cog(NPC(bot))
