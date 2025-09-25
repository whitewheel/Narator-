import discord
from discord.ext import commands
from services import npc_service
import json
from utils.db import fetchone, execute

class NPC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="npc", invoke_without_command=True)
    async def npc(self, ctx):
        await ctx.send(
            "Gunakan: `!npc add`, `!npc list`, `!npc remove`, "
            "`!npc favor`, `!npc reveal`, `!npc detail`, `!npc sync`"
        )

    # === Tambah NPC ===
    @npc.command(name="add")
    async def npc_add(self, ctx, name: str, *, role: str = ""):
        guild_id = ctx.guild.id
        exists = fetchone(guild_id, "SELECT id FROM npc WHERE name=?", (name,))
        if exists:
            return await ctx.send(f"⚠️ NPC **{name}** sudah ada.")
        msg = await npc_service.add_npc(guild_id, ctx.author.id, name, role)
        await ctx.send(f"🧑‍🤝‍🧑 NPC **{name}** ditambahkan dengan role: {role}\n{msg or ''}")

    # === List NPC ===
    @npc.command(name="list")
    async def npc_list(self, ctx):
        guild_id = ctx.guild.id
        msg = await npc_service.list_npc(guild_id)
        await ctx.send(msg)

    # === Update Favor ===
    @npc.command(name="favor")
    async def npc_favor(self, ctx, name: str, amount: int):
        guild_id = ctx.guild.id
        exists = fetchone(guild_id, "SELECT id FROM npc WHERE name=?", (name,))
        if not exists:
            return await ctx.send(f"❌ NPC **{name}** tidak ditemukan.")
        msg = await npc_service.update_favor(guild_id, name, amount, ctx.author.id)
        await ctx.send(msg)

    # === Reveal Trait ===
    @npc.command(name="reveal")
    async def npc_reveal(self, ctx, name: str, trait_key: str):
        guild_id = ctx.guild.id
        exists = fetchone(guild_id, "SELECT id, traits FROM npc WHERE name=?", (name,))
        if not exists:
            return await ctx.send(f"❌ NPC **{name}** tidak ditemukan.")
        msg = await npc_service.reveal_trait(guild_id, name, trait_key, ctx.author.id)
        await ctx.send(msg)

    # === Detail NPC (embed cantik) ===
    @npc.command(name="detail")
    async def npc_detail(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        npc = fetchone(guild_id, "SELECT * FROM npc WHERE name=?", (name,))
        if not npc:
            return await ctx.send("❌ NPC tidak ditemukan.")

        embed = discord.Embed(
            title=f"👤 {npc['name']}",
            description=f"Peran: **{npc.get('role','-')}**",
            color=discord.Color.greyple()
        )
        embed.add_field(name="💠 Favor", value=str(npc.get("favor", 0)), inline=True)

        traits = npc.get("traits")
        if traits:
            try:
                traits = json.loads(traits)
                visible = [f"- {k}: {v}" for k, v in traits.items()]
                embed.add_field(name="👁️ Traits", value="\n".join(visible) or "-", inline=False)
            except Exception:
                embed.add_field(name="👁️ Traits", value="-", inline=False)
        else:
            embed.add_field(name="👁️ Traits", value="-", inline=False)

        await ctx.send(embed=embed)

    # === Sinkronkan NPC dari lore (wiki kategori npc) ===
    @npc.command(name="sync")
    async def npc_sync(self, ctx):
        guild_id = ctx.guild.id
        msg = await npc_service.sync_from_wiki(guild_id, ctx.author.id)
        await ctx.send(msg)

    # === Hapus NPC ===
    @npc.command(name="remove")
    async def npc_remove(self, ctx, *, name: str):
        guild_id = ctx.guild.id
        exists = fetchone(guild_id, "SELECT id FROM npc WHERE name=?", (name,))
        if not exists:
            return await ctx.send(f"❌ NPC **{name}** tidak ditemukan.")
        execute(guild_id, "DELETE FROM npc WHERE name=?", (name,))
        await ctx.send(f"🗑️ NPC **{name}** dihapus.")

async def setup(bot):
    await bot.add_cog(NPC(bot))
