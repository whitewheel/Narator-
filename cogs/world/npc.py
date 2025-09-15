import discord
from discord.ext import commands
from services import npc_service

class NPC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="npc", invoke_without_command=True)
    async def npc(self, ctx):
        await ctx.send("Gunakan: `!npc add`, `!npc list`, `!npc remove`, `!npc favor`, `!npc reveal`, `!npc detail`, `!npc sync`")

    # === Tambah NPC ===
    @npc.command(name="add")
    async def npc_add(self, ctx, name: str, *, role: str = ""):
        await npc_service.add_npc(ctx.guild.id, ctx.channel.id, name, role)
        await ctx.send(f"🧑‍🤝‍🧑 NPC **{name}** ditambahkan dengan role: {role}")

    # === List NPC ===
    @npc.command(name="list")
    async def npc_list(self, ctx):
        msg = await npc_service.list_npc(ctx.guild.id, ctx.channel.id)
        await ctx.send(msg)

    # === Update Favor ===
    @npc.command(name="favor")
    async def npc_favor(self, ctx, name: str, amount: int):
        msg = await npc_service.update_favor(ctx.guild.id, ctx.channel.id, name, amount)
        await ctx.send(msg)

    # === Reveal Trait ===
    @npc.command(name="reveal")
    async def npc_reveal(self, ctx, name: str, trait_key: str):
        msg = await npc_service.reveal_trait(ctx.guild.id, ctx.channel.id, name, trait_key)
        await ctx.send(msg)

    # === Detail NPC (embed cantik) ===
    @npc.command(name="detail")
    async def npc_detail(self, ctx, *, name: str):
        guild_id, channel_id = ctx.guild.id, ctx.channel.id
        from utils.db import fetchone
        npc = fetchone("SELECT * FROM npc WHERE guild_id=? AND channel_id=? AND name=?",
                       (guild_id, channel_id, name))
        if not npc:
            return await ctx.send("❌ NPC tidak ditemukan.")

        embed = discord.Embed(
            title=f"👤 {npc['name']}",
            description=f"Peran: **{npc['role']}**",
            color=discord.Color.greyple()
        )
        embed.add_field(name="💠 Favor", value=str(npc["favor"]), inline=True)

        traits = npc.get("traits")
        if traits:
            traits = json.loads(traits)
            visible = [f"- {k}: {v}" for k, v in traits.items()]
            embed.add_field(name="👁️ Traits", value="\n".join(visible) or "-", inline=False)
        else:
            embed.add_field(name="👁️ Traits", value="-", inline=False)

        await ctx.send(embed=embed)

    # === Sinkronkan NPC dari lore (wiki kategori npc) ===
    @npc.command(name="sync")
    async def npc_sync(self, ctx):
        msg = await npc_service.sync_from_wiki(ctx.guild.id, ctx.channel.id)
        await ctx.send(msg)

    # === Hapus NPC (soft delete) ===
    @npc.command(name="remove")
    async def npc_remove(self, ctx, *, name: str):
        from utils.db import execute
        guild_id, channel_id = ctx.guild.id, ctx.channel.id
        execute("DELETE FROM npc WHERE guild_id=? AND channel_id=? AND name=?",
                (guild_id, channel_id, name))
        await ctx.send(f"🗑️ NPC **{name}** dihapus.")

async def setup(bot):
    await bot.add_cog(NPC(bot))
