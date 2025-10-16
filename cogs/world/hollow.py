# cogs/world/hollow.py
import discord
from discord.ext import commands
from services import hollow_service
import json
from datetime import datetime

class Hollow(commands.Cog):
    """🌀 Technonesia Hollow System — Node, Vendor, Visitor, Event & Daily Cycle"""

    def __init__(self, bot):
        self.bot = bot

    # ======================================================
    # 🧭 BASE GROUP
    # ======================================================
    @commands.group(name="hollow", invoke_without_command=True)
    async def hollow(self, ctx):
        """Daftar perintah Hollow (GM Only)"""
        embed = discord.Embed(
            title="🌀 Technonesia Hollow System (GM)",
            color=discord.Color.teal(),
            description=(
                "⚙️ **Node Control**\n"
                "`!hollow addnode <nama> <zona> [type]`\n"
                "`!hollow list`, `!hollow info <node>`, `!hollow edit <node> field=value`,\n"
                "`!hollow clone <src> <target>`, `!hollow remove <node>`, `!hollow reset <node>`\n\n"
                "🎲 **Daily Cycle**\n"
                "`!hollow roll <node>` | `!hollow daily_roll <node>` | `!hollow announce <node>` | `!hollow sync`\n"
                "`!hollow slot_roll <node> <morning/evening/night>`\n\n"
                "🧍‍♂️ **Vendor Control**\n"
                "`!hollow addnpc <nama> <node> [chance] [rarity]`\n"
                "`!hollow removenpc <nama> <node>` | `!hollow listnpc <node>`\n\n"
                "👁 **Visitors**\n"
                "`!hollow addvisitor <nama>` | `!hollow removevisitor <nama>` | `!hollow editvisitor <nama> field=value`\n"
                "`!hollow listvisitor`\n\n"
                "🎯 **Events**\n"
                "`!hollow addevent <nama>` | `!hollow removeevent <nama>` | `!hollow editevent <nama> field=value`\n"
                "`!hollow listevent` | `!hollow assign <event> <node>` | `!hollow clearevent <node>`\n\n"
                "🧩 **Traits & Types**\n"
                "`!hollow trait add/remove <node> <trait>` | `!hollow type add/remove <node> <type>`"
            )
        )
        embed.set_footer(text="Technonesia 2145 • Hollow Command Index")
        await ctx.send(embed=embed)

    # ======================================================
    # 🏙 NODE CONTROL
    # ======================================================
    @hollow.command(name="addnode")
    @commands.has_permissions(administrator=True)
    async def addnode(self, ctx, name: str, zone: str, node_type: str = "market"):
        msg = hollow_service.add_node(ctx.guild.id, name, zone, node_type)
        await ctx.send(msg)

    @hollow.command(name="list")
    async def list_nodes(self, ctx):
        rows = hollow_service.list_nodes(ctx.guild.id)
        if not rows:
            return await ctx.send("📭 Belum ada node Hollow terdaftar.")
        embed = discord.Embed(title="📍 Hollow Network Map", color=discord.Color.blue())
        for r in rows:
            npcs = len(json.loads(r.get("npcs", "[]")))
            visitors = len(json.loads(r.get("visitors", "[]")))
            events = len(json.loads(r.get("events", "[]")))
            embed.add_field(
                name=f"{r['name']} ({r['zone']})",
                value=f"🏷 Type: `{r['type']}`\n💰 NPC: {npcs} | 👁 Visitors: {visitors} | 🎯 Events: {events}",
                inline=False
            )
        embed.set_footer(text="Technonesia Hollow Nodes Overview")
        await ctx.send(embed=embed)

    @hollow.command(name="info")
    async def node_info(self, ctx, node_name: str):
        node = hollow_service.get_node(ctx.guild.id, node_name)
        if not node:
            return await ctx.send("❌ Node tidak ditemukan.")
        embed = hollow_service.make_node_embed(node)
        await ctx.send(embed=embed)

    @hollow.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def edit_node(self, ctx, node_name: str, *, entry: str):
        msg = hollow_service.edit_node(ctx.guild.id, node_name, entry)
        await ctx.send(msg)

    @hollow.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_node(self, ctx, *, node_name: str):
        msg = hollow_service.remove_node(ctx.guild.id, node_name)
        await ctx.send(msg)

    @hollow.command(name="clone")
    @commands.has_permissions(administrator=True)
    async def clone_node(self, ctx, source: str, target: str):
        msg = hollow_service.clone_node(ctx.guild.id, source, target)
        await ctx.send(msg)

    @hollow.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_node(self, ctx, *, node_name: str):
        msg = hollow_service.reset_node(ctx.guild.id, node_name)
        await ctx.send(msg)

    @hollow.command(name="log")
    async def show_log(self, ctx, node_name: str, n: int = 5):
        logs = hollow_service.get_logs(ctx.guild.id, node_name, n)
        if not logs:
            return await ctx.send("📭 Belum ada histori untuk node itu.")
        embed = discord.Embed(title=f"🧾 Hollow Log — {node_name}", color=discord.Color.dark_teal())
        for l in logs:
            date = l["created_at"]
            ev = l.get("event") or "-"
            embed.add_field(
                name=f"{date}",
                value=f"🎯 {ev}\n💰 {', '.join(json.loads(l['vendors'] or '[]'))}\n👁 {', '.join(json.loads(l['visitors'] or '[]'))}",
                inline=False
            )
        await ctx.send(embed=embed)

    # ======================================================
    # 🎲 DAILY & SLOT ROLL
    # ======================================================
    @hollow.command(name="roll")
    @commands.has_permissions(administrator=True)
    async def roll_node(self, ctx, node_name: str):
        embed = hollow_service.roll_daily(ctx.guild.id, node_name)
        await ctx.send(embed=embed)

    @hollow.command(name="daily_roll")
    @commands.has_permissions(administrator=True)
    async def daily_roll(self, ctx, node_name: str):
        embed = hollow_service.roll_daily(ctx.guild.id, node_name, full_cycle=True)
        await ctx.send(embed=embed)

    @hollow.command(name="slot_roll")
    @commands.has_permissions(administrator=True)
    async def slot_roll(self, ctx, node_name: str, slot: str):
        embed = hollow_service.roll_slot(ctx.guild.id, node_name, slot)
        await ctx.send(embed=embed)

    @hollow.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce_node(self, ctx, node_name: str):
        embed = hollow_service.make_announcement(ctx.guild.id, node_name)
        if not embed:
            return await ctx.send("📭 Tidak ada hasil roll terakhir untuk node itu.")
        await ctx.send(embed=embed)

    @hollow.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_all(self, ctx):
        embeds = hollow_service.sync_all(ctx.guild.id)
        for e in embeds:
            await ctx.send(embed=e)
        await ctx.send("✅ Semua node Hollow telah di-roll ulang.")

    # ======================================================
    # 🧍‍♂️ NPC MANAGEMENT (dengan chance & rarity)
    # ======================================================
    @hollow.command(name="addnpc")
    @commands.has_permissions(administrator=True)
    async def addnpc(self, ctx, npc_name: str, node_name: str, chance: int = 50, rarity: str = "common"):
        msg = hollow_service.add_npc(ctx.guild.id, node_name, npc_name, chance, rarity)
        await ctx.send(msg)

    @hollow.command(name="removenpc")
    @commands.has_permissions(administrator=True)
    async def removenpc(self, ctx, npc_name: str, node_name: str):
        msg = hollow_service.remove_npc(ctx.guild.id, node_name, npc_name)
        await ctx.send(msg)

    @hollow.command(name="listnpc")
    async def listnpc(self, ctx, node_name: str):
        npcs = hollow_service.list_npc(ctx.guild.id, node_name)
        if not npcs:
            return await ctx.send("📭 Tidak ada NPC di node itu.")
        embed = discord.Embed(
            title=f"💰 Vendor & NPC — {node_name}",
            color=discord.Color.gold()
        )
        for npc in npcs:
            embed.add_field(
                name=f"{npc['name']}",
                value=f"🎯 Chance: {npc['chance']}% | 🏷 Rarity: {npc['rarity'].capitalize()}",
                inline=False
            )
        embed.set_footer(text="Technonesia Hollow Vendors")
        await ctx.send(embed=embed)

    # ======================================================
    # 👁 VISITOR MANAGEMENT
    # ======================================================
    @hollow.command(name="addvisitor")
    @commands.has_permissions(administrator=True)
    async def addvisitor(self, ctx, *, visitor_name: str):
        msg = hollow_service.add_visitor(ctx.guild.id, visitor_name)
        await ctx.send(msg)

    @hollow.command(name="removevisitor")
    @commands.has_permissions(administrator=True)
    async def removevisitor(self, ctx, *, visitor_name: str):
        msg = hollow_service.remove_visitor(ctx.guild.id, visitor_name)
        await ctx.send(msg)

    @hollow.command(name="editvisitor")
    @commands.has_permissions(administrator=True)
    async def editvisitor(self, ctx, visitor_name: str, *, entry: str):
        msg = hollow_service.edit_visitor(ctx.guild.id, visitor_name, entry)
        await ctx.send(msg)

    @hollow.command(name="listvisitor")
    async def listvisitor(self, ctx):
        visitors = hollow_service.list_visitors(ctx.guild.id)
        if not visitors:
            return await ctx.send("📭 Belum ada visitor global.")
        embed = hollow_service.make_visitor_list_embed(visitors)
        await ctx.send(embed=embed)

    # ======================================================
    # 🎯 EVENT MANAGEMENT
    # ======================================================
    @hollow.command(name="addevent")
    @commands.has_permissions(administrator=True)
    async def addevent(self, ctx, *, event_name: str):
        msg = hollow_service.add_event(ctx.guild.id, event_name)
        await ctx.send(msg)

    @hollow.command(name="removeevent")
    @commands.has_permissions(administrator=True)
    async def removeevent(self, ctx, *, event_name: str):
        msg = hollow_service.remove_event(ctx.guild.id, event_name)
        await ctx.send(msg)

    @hollow.command(name="editevent")
    @commands.has_permissions(administrator=True)
    async def editevent(self, ctx, event_name: str, *, entry: str):
        msg = hollow_service.edit_event(ctx.guild.id, event_name, entry)
        await ctx.send(msg)

    @hollow.command(name="listevent")
    async def listevent(self, ctx):
        events = hollow_service.list_events(ctx.guild.id)
        if not events:
            return await ctx.send("📭 Tidak ada event global.")
        embed = hollow_service.make_event_list_embed(events)
        await ctx.send(embed=embed)

    @hollow.command(name="assign")
    @commands.has_permissions(administrator=True)
    async def assign_event(self, ctx, event_name: str, node_name: str):
        msg = hollow_service.assign_event(ctx.guild.id, event_name, node_name)
        await ctx.send(msg)

    @hollow.command(name="clearevent")
    @commands.has_permissions(administrator=True)
    async def clear_event(self, ctx, node_name: str):
        msg = hollow_service.clear_event(ctx.guild.id, node_name)
        await ctx.send(msg)

    # ======================================================
    # ⚙ TRAITS & TYPES
    # ======================================================
    @hollow.group(name="trait")
    @commands.has_permissions(administrator=True)
    async def trait_group(self, ctx):
        pass

    @trait_group.command(name="add")
    async def add_trait(self, ctx, node_name: str, *, trait: str):
        msg = hollow_service.add_trait(ctx.guild.id, node_name, trait)
        await ctx.send(msg)

    @trait_group.command(name="remove")
    async def remove_trait(self, ctx, node_name: str, *, trait: str):
        msg = hollow_service.remove_trait(ctx.guild.id, node_name, trait)
        await ctx.send(msg)

    @trait_group.command(name="list")
    async def list_trait(self, ctx, node_name: str):
        traits = hollow_service.list_traits(ctx.guild.id, node_name)
        embed = discord.Embed(
            title=f"🧩 Traits — {node_name}",
            description="\n".join(traits) if traits else "Tidak ada trait aktif.",
            color=discord.Color.teal()
        )
        await ctx.send(embed=embed)

    @hollow.group(name="type")
    @commands.has_permissions(administrator=True)
    async def type_group(self, ctx):
        pass

    @type_group.command(name="add")
    async def add_type(self, ctx, node_name: str, *, t: str):
        msg = hollow_service.add_type(ctx.guild.id, node_name, t)
        await ctx.send(msg)

    @type_group.command(name="remove")
    async def remove_type(self, ctx, node_name: str, *, t: str):
        msg = hollow_service.remove_type(ctx.guild.id, node_name, t)
        await ctx.send(msg)

    @type_group.command(name="list")
    async def list_type(self, ctx, node_name: str):
        types = hollow_service.list_types(ctx.guild.id, node_name)
        embed = discord.Embed(
            title=f"💠 Types — {node_name}",
            description="\n".join(types) if types else "Tidak ada type aktif.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

# ======================================================
# ✅ SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Hollow(bot))
