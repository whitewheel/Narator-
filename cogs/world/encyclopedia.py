import discord
from discord.ext import commands

# =====================
#  LIBRARY DATA
# =====================

RACES = {
    "Race1": {
        "name": "Race1",
        "title": "TODO",
        "lore": "TODO: asal-usul, posisi di dunia.",
        "culture": "TODO: kehidupan sosial & tradisi.",
        "appearance": ["TODO"],
        "augment": "TODO",
        "stat_bonus": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},
        "traits": [],
        "resist": [],
        "speed": 30,
        "languages": ["Common"],
        "vision": "Normal",
        "relations": {},
        "faction_bias": {}
    },
    # Tambahkan Race2–Race11 di sini
}

CLASSES = {
    "Class1": {
        "name": "Class1",
        "title": "TODO",
        "lore": "TODO: asal mula class, filosofi, gaya bertarung.",
        "role": "TODO: Tank / DPS / Support / Hybrid",
        "hit_die": "d8",
        "hp_bonus": 0,
        "stat_bonus": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},
        "proficiency": {
            "weapons": [],
            "armor": [],
            "skills": [],
            "saving_throws": []
        },
        "features": {
            1: ["TODO: fitur level 1"],
            2: ["TODO: fitur level 2"],
            5: ["TODO: fitur level 5"],
        },
        "passives": [],
        "actives": [],
        "starting_equipment": [],
        "resource_pool": "TODO"
    },
    # Tambahkan Class2–Class15 di sini
}

# =====================
#  COG
# =====================

class Encyclopedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="raceinfo")
    async def raceinfo(self, ctx, *, race_name: str):
        """Tampilkan informasi detail tentang sebuah ras."""
        race = RACES.get(race_name)
        if not race:
            return await ctx.send("❌ Race tidak ditemukan.")

        embed = discord.Embed(
            title=f"🌱 {race['name']} – {race['title']}",
            description=race["lore"],
            color=discord.Color.green()
        )
        embed.add_field(name="Culture", value=race["culture"], inline=False)
        embed.add_field(name="Appearance", value=", ".join(race["appearance"]) or "-", inline=False)
        embed.add_field(name="Augment", value=race["augment"], inline=False)
        embed.add_field(name="Stat Bonus", value=str(race["stat_bonus"]), inline=False)
        embed.add_field(name="Traits", value="\n".join(race["traits"]) or "-", inline=False)
        embed.add_field(name="Resist", value=", ".join(race["resist"]) or "-", inline=False)
        embed.add_field(name="Speed", value=str(race["speed"]), inline=True)
        embed.add_field(name="Languages", value=", ".join(race["languages"]), inline=True)
        embed.add_field(name="Vision", value=race["vision"], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="classinfo")
    async def classinfo(self, ctx, *, class_name: str):
        """Tampilkan informasi detail tentang sebuah class."""
        cls = CLASSES.get(class_name)
        if not cls:
            return await ctx.send("❌ Class tidak ditemukan.")

        embed = discord.Embed(
            title=f"⚔️ {cls['name']} – {cls['title']}",
            description=cls["lore"],
            color=discord.Color.blue()
        )
        embed.add_field(name="Role", value=cls["role"], inline=False)
        embed.add_field(name="Hit Die", value=cls["hit_die"], inline=True)
        embed.add_field(name="Stat Bonus", value=str(cls["stat_bonus"]), inline=False)

        profs = []
        for k, v in cls["proficiency"].items():
            if v:
                profs.append(f"**{k.capitalize()}**: {', '.join(v)}")
        embed.add_field(name="Proficiency", value="\n".join(profs) or "-", inline=False)

        features_text = "\n".join([f"Lv{lvl}: {', '.join(feats)}" for lvl, feats in cls["features"].items()])
        embed.add_field(name="Features", value=features_text or "-", inline=False)

        embed.add_field(name="Resource", value=cls["resource_pool"], inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Encyclopedia(bot))
