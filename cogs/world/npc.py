import discord
from discord.ext import commands
from services import npc_service
import json

class NPC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="npc", invoke_without_command=True)
    async def npc(self, ctx):
        await ctx.send(
            "Gunakan: `!npc add`, `!npc list`, `!npc remove`, "
            "`!npc trait_add`, `!npc trait_remove`, "
            "`!npc reveal`, `!npc allreveal`, "
            "`!npc info`, `!npc detail`, `!npc sync`"
        )

    @npc.command(name="list")
    async def npc_list(self, ctx):
        data = await npc_service.list_npc(ctx.guild.id)
        if not data:
            return await ctx.send("❌ Tidak ada NPC yang terdaftar di server ini.")

        # Pastikan jadi list
        if isinstance(data, str):
            lines = [x.strip("• ").strip() for x in data.split("\n") if x.strip()]
        elif isinstance(data, list):
            lines = data
        else:
            return await ctx.send("⚠️ Format data NPC tidak valid.")

        per_page = 20
        total_pages = math.ceil(len(lines) / per_page)

        def get_page(page):
            start = (page - 1) * per_page
            end = start + per_page
            chunk = lines[start:end]
            embed = discord.Embed(
                title=f"📜 Daftar NPC — Halaman {page}/{total_pages}",
                description="\n".join(f"• {x}" for x in chunk),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Total: {len(lines)} NPC")
            return embed

        class NPCListView(View):
            def __init__(self):
                super().__init__(timeout=90)
                self.page = 1

            async def update_message(self, interaction):
                embed = get_page(self.page)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
            async def prev(self, interaction: discord.Interaction, button: Button):
                if self.page > 1:
                    self.page -= 1
                    await self.update_message(interaction)
                else:
                    await interaction.response.defer()

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
            async def next(self, interaction: discord.Interaction, button: Button):
                if self.page < total_pages:
                    self.page += 1
                    await self.update_message(interaction)
                else:
                    await interaction.response.defer()

        view = NPCListView()
        await ctx.send(embed=get_page(1), view=view)
    
    # === Tambah NPC ===
    @npc.command(name="add")
    async def npc_add(self, ctx, name: str, *, role: str = ""):
        msg = await npc_service.add_npc(ctx.guild.id, ctx.author.id, name, role)
        await ctx.send(msg)

    # === List NPC ===
    @npc.command(name="list")
    async def npc_list(self, ctx):
        msg = await npc_service.list_npc(ctx.guild.id)
        await ctx.send(msg)

    # === Tambah Trait ===
    @npc.command(name="trait_add")
    async def npc_trait_add(self, ctx, name: str, *, entry: str):
        """
        Format: !npc trait_add <nama> key=value [--visible]
        """
        parts = entry.split("=")
        if len(parts) < 2:
            return await ctx.send("❌ Format salah. Gunakan: key=value")
        key = parts[0].strip()
        value = parts[1].strip()
        visible = "--visible" in entry
        msg = await npc_service.add_trait(ctx.guild.id, name, key, value, visible, ctx.author.id)
        await ctx.send(msg)

    # === Hapus Trait ===
    @npc.command(name="trait_remove")
    async def npc_trait_remove(self, ctx, name: str, trait_key: str):
        msg = await npc_service.remove_trait(ctx.guild.id, name, trait_key, ctx.author.id)
        await ctx.send(msg)

    # === Reveal Trait ===
    @npc.command(name="reveal")
    async def npc_reveal(self, ctx, name: str, trait_key: str):
        msg = await npc_service.reveal_trait(ctx.guild.id, name, trait_key, ctx.author.id)
        await ctx.send(msg)

    # === Reveal Semua Trait + Info ===
    @npc.command(name="allreveal")
    async def npc_allreveal(self, ctx, *, name: str):
        msg = await npc_service.all_reveal(ctx.guild.id, name, ctx.author.id)
        await ctx.send(msg)

    # === Update Info ===
    @npc.command(name="info")
    async def npc_info(self, ctx, name: str, *, entry: str):
        """
        Format: !npc info <nama> <teks> [--hidden]
        """
        hidden = "--hidden" in entry
        text = entry.replace("--hidden", "").strip()
        msg = await npc_service.set_info(ctx.guild.id, name, text, hidden, ctx.author.id)
        await ctx.send(msg)

    # === Detail NPC (embed cantik) ===
    @npc.command(name="detail")
    async def npc_detail(self, ctx, *, name: str):
        npc = npc_service.get_npc(ctx.guild.id, name)
        if not npc:
            return await ctx.send("❌ NPC tidak ditemukan.")

        embed = discord.Embed(
            title=f"👤 {npc['name']}",
            description=f"Peran: **{npc.get('role','-')}**",
            color=discord.Color.greyple()
        )

        # Status & Affiliation kalau ada
        if npc.get("status"):
            embed.add_field(name="📌 Status", value=npc["status"], inline=True)
        if npc.get("affiliation"):
            embed.add_field(name="🏳️ Affiliation", value=npc["affiliation"], inline=True)

        # Traits
        traits = npc.get("traits")
        if traits:
            try:
                traits = json.loads(traits)
                visible = []
                for k, v in traits.items():
                    if isinstance(v, dict):
                        if v.get("visible"):
                            visible.append(f"- {k}: {v['value']}")
                        else:
                            visible.append(f"- {k}: ???")
                    else:
                        visible.append(f"- {k}: {v}")
                embed.add_field(name="👁️ Traits", value="\n".join(visible) or "-", inline=False)
            except Exception:
                embed.add_field(name="👁️ Traits", value="-", inline=False)
        else:
            embed.add_field(name="👁️ Traits", value="-", inline=False)

        # Info (bisa hidden)
        info = npc.get("info")
        if info:
            try:
                info_data = json.loads(info)
                if isinstance(info_data, dict) and not info_data.get("visible", True):
                    embed.add_field(name="📖 Info", value="???", inline=False)
                else:
                    text = info_data["value"] if isinstance(info_data, dict) else str(info_data)
                    embed.add_field(name="📖 Info", value=text, inline=False)
            except Exception:
                embed.add_field(name="📖 Info", value=str(info), inline=False)
        else:
            embed.add_field(name="📖 Info", value="-", inline=False)

        await ctx.send(embed=embed)

    # === Sinkronkan NPC dari lore (wiki kategori npc) ===
    @npc.command(name="sync")
    async def npc_sync(self, ctx):
        msg = await npc_service.sync_from_wiki(ctx.guild.id, ctx.author.id)
        await ctx.send(msg)

    # === Hapus NPC ===
    @npc.command(name="remove")
    async def npc_remove(self, ctx, *, name: str):
        msg = await npc_service.remove_npc(ctx.guild.id, ctx.author.id, name)
        await ctx.send(msg)

    # === GM Show (lihat semua trait & info tanpa hidden) ===
    @npc.command(name="gmshow")
    async def npc_gmshow(self, ctx, *, name: str):
        npc = npc_service.get_npc(ctx.guild.id, name)
        if not npc:
            return await ctx.send("❌ NPC tidak ditemukan.")

        embed = discord.Embed(
            title=f"👁️ GM View: {npc['name']}",
            description=f"Peran: **{npc.get('role','-')}**",
            color=discord.Color.dark_gold()
        )

        # Status & Affiliation
        if npc.get("status"):
            embed.add_field(name="📌 Status", value=npc["status"], inline=True)
        if npc.get("affiliation"):
            embed.add_field(name="🏳️ Affiliation", value=npc["affiliation"], inline=True)

        # Semua Traits (termasuk hidden)
        traits = npc.get("traits")
        if traits:
            try:
                traits = json.loads(traits)
                lines = []
                for k, v in traits.items():
                    if isinstance(v, dict):
                        val = v.get("value", "-")
                        visible = v.get("visible", False)
                        lines.append(f"- {k}: {val} {'(hidden)' if not visible else ''}")
                    else:
                        lines.append(f"- {k}: {v}")
                embed.add_field(name="🧬 All Traits", value="\n".join(lines) or "-", inline=False)
            except Exception:
                embed.add_field(name="🧬 All Traits", value="-", inline=False)
        else:
            embed.add_field(name="🧬 All Traits", value="-", inline=False)

        # Info (lihat semua)
        info = npc.get("info")
        if info:
            try:
                info_data = json.loads(info)
                val = info_data.get("value", info_data) if isinstance(info_data, dict) else info
                embed.add_field(name="📖 Info", value=val, inline=False)
            except Exception:
                embed.add_field(name="📖 Info", value=str(info), inline=False)
        else:
            embed.add_field(name="📖 Info", value="-", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NPC(bot))
