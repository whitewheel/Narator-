
import discord
from discord.ext import commands
import asyncio
import random
import re
import json

from memory import save_memory, get_recent
from cogs.world.timeline import log_event  # ✅ timeline hook

def _key(ctx):
    """Key unik per-guild per-channel."""
    return (ctx.guild.id if ctx.guild else 0, ctx.channel.id)


def save_initiative_to_memory(guild_id, channel_id, user_id, data):
    save_memory(guild_id, channel_id, user_id, "initiative", json.dumps(data))


def load_initiative_from_memory(guild_id, channel_id):
    rows = get_recent(guild_id, channel_id, "initiative", 1)
    for (_id, cat, content, meta, ts) in rows:
        try:
            return json.loads(content)
        except Exception:
            continue
    return None


class InitiativeMemory(commands.Cog):
    """
    Initiative tracker in-memory (tanpa DB).
    Data hilang saat restart/redeploy.
    Per channel: simpan list [(name, score)], pointer giliran, dan round.
    """
    def __init__(self, bot):
        self.bot = bot
        self.state = {}

    # ===== helpers =====
    def _ensure(self, ctx):
        k = _key(ctx)
        if k not in self.state:
            self.state[k] = {"order": [], "ptr": 0, "round": 1}
        return self.state[k]

    def _sorted(self, arr):
        return sorted(arr, key=lambda x: (-x[1], x[0].lower()))

    def _persist(self, ctx):
        """Simpan state initiative channel ini ke LTM."""
        k = _key(ctx)
        s = self._ensure(ctx)
        data = {"order": s["order"], "ptr": s["ptr"], "round": s["round"]}
        gid = str(ctx.guild.id) if ctx.guild else "0"
        cid = str(ctx.channel.id)
        uid = str(getattr(ctx.author, "id", 0))
        save_initiative_to_memory(gid, cid, uid, data)

    def _make_embed(self, ctx, title: str, s: dict, highlight: bool = True):
        order = s["order"]
        ptr = s["ptr"]
        rnd = s["round"]

        embed = discord.Embed(
            title=title,
            description=f"📜 Round {rnd} • Channel: **{ctx.channel.name}**",
            color=discord.Color.red()
        )

        if not order:
            embed.add_field(name="Initiative Order", value="(kosong)", inline=False)
            return embed

        lines = []
        for i, (name, score) in enumerate(order):
            marker = "👉" if highlight and i == ptr else "  "
            lines.append(f"{marker} {i+1}. {name} ({score})")

        embed.add_field(name="Initiative Order", value="\n".join(lines), inline=False)
        embed.set_footer(text="Gunakan !init next atau !next untuk lanjut giliran.")
        return embed

    # ===== command group =====
    @commands.group(name="init", invoke_without_command=True)
    async def init_group(self, ctx):
        await ctx.send(
            "```txt\n"
            "Initiative Commands:\n"
            "!init add <Nama> <Skor>\n"
            "!init addmany \"Alice 18, Goblin 12, Borin 14\"  (juga bisa multi-line)\n"
            "!init show            (atau: !order)\n"
            "!init next            (atau: !next / !n)\n"
            "!init setptr <index>  (mulai dari 1)\n"
            "!init remove <Nama>\n"
            "!init clear\n"
            "!init shuffle         (acak pointer awal)\n"
            "!init round           (lihat round) / !init round <angka> (set)\n"
            "```"
        )

    @init_group.command(name="add")
    async def init_add(self, ctx, name: str, score: int):
        s = self._ensure(ctx)
        existing = {n: sc for (n, sc) in s["order"]}
        existing[name] = score
        s["order"] = self._sorted(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
        self._persist(ctx)
        await ctx.send(f"✅ Ditambahkan/diupdate: **{name}** = {score}")

    @init_group.command(name="addmany")
    async def init_addmany(self, ctx, *, entries: str = None):
        """
        Tambah banyak peserta sekaligus.
        Pemisah: koma (,), titik koma (;), pipe (|), atau baris baru.
        Format tiap item: <Nama> <Skor>
        Contoh:
          !init addmany Alice 18, Goblin 12
          !init addmany "Sir Alice" 18; Orc 12 | Mage 16
          !init addmany
          Alice 18
          Bob 14
        """
        # Jika user kirim multi-line tanpa argumen setelah command, ambil dari raw message.
        if entries is None:
            raw = ctx.message.content
            idx = raw.lower().find("addmany")
            entries = raw[idx + len("addmany"):].strip() if idx != -1 else ""

        if not entries:
            return await ctx.send("⚠️ Format: `!init addmany Alice 18, Goblin 12` atau tulis daftar di baris berikutnya.")

        s = self._ensure(ctx)
        existing = {n: sc for (n, sc) in s["order"]}

        # Pecah menjadi item per peserta
        chunks = [c.strip() for c in re.split(r'[,\n;|]+', entries) if c.strip()]

        added = 0
        skipped = []

        for ch in chunks:
            # Cocokkan: <Nama...> <Skor>
            m = re.match(r'^(?P<name>.+?)\s+(?P<score>-?\d+)\s*$', ch)
            if not m:
                skipped.append(ch)
                continue
            name = m.group('name').strip()
            score = int(m.group('score'))
            existing[name] = score
            added += 1

        s["order"] = self._sorted(list(existing.items()))
        s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0

        msg = f"✅ Ditambahkan/diupdate **{added}** peserta."
        if skipped:
            preview = ", ".join(skipped[:5])
            if len(skipped) > 5:
                preview += ", ..."
            msg += f" (di-skip: {preview})"
        self._persist(ctx)
        await ctx.send(msg)

    @init_group.command(name="remove")
    async def init_remove(self, ctx, name: str):
        s = self._ensure(ctx)
        before = len(s["order"])
        s["order"] = [(n, sc) for (n, sc) in s["order"] if n != name]
        if len(s["order"]) < before:
            s["ptr"] = s["ptr"] % len(s["order"]) if s["order"] else 0
            self._persist(ctx)
            await ctx.send(f"🗑️ Hapus **{name}**")
        else:
            await ctx.send("⚠️ Nama tidak ditemukan.")

    @init_group.command(name="show")
    async def init_show(self, ctx):
        s = self._ensure(ctx)
        self._persist(ctx)
        embed = self._make_embed(ctx, "⚔️ Initiative Order", s)
        await ctx.send(embed=embed)
        # 🔎 log timeline: encounter_start
        try:
            code = f"E{len(get_recent(str(ctx.guild.id), str(ctx.channel.id), 'timeline', 9999)):03d}"
            names = [n for (n, _sc) in s.get("order", [])]
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=code,
                      title="Encounter dimulai",
                      details=f"Order: {", ".join(names)}",
                      etype="encounter_start",
                      actors=names,
                      tags=["combat","encounter","start"])
        except Exception:
            pass

    @init_group.command(name="next")
    async def init_next(self, ctx):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta. Tambah dengan `!init add <Nama> <Skor>`")

        s["ptr"] = (s["ptr"] + 1) % len(s["order"])
        if s["ptr"] == 0:
            s["round"] += 1
            await ctx.send(f"🔄 **Round {s['round']} dimulai!**")

        self._persist(ctx)
        embed = self._make_embed(ctx, "⏭️ Initiative Next", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran", value=f"✨ **{current}**", inline=False)
        await ctx.send(embed=embed)
        # 🔎 log timeline: turn advance
        try:
            current = s["order"][s["ptr"]][0]
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title=f"Turn: {current}",
                      details=f"Round {s.get('round',1)}",
                      etype="turn",
                      actors=[current],
                      tags=["combat","turn"])
        except Exception:
            pass

    @init_group.command(name="setptr")
    async def init_setptr(self, ctx, index: int):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        idx = max(1, min(index, len(s["order"]))) - 1
        s["ptr"] = idx
        self._persist(ctx)
        embed = self._make_embed(ctx, "📌 Pointer Diset Manual", s)
        await ctx.send(embed=embed)

    @init_group.command(name="clear")
    async def init_clear(self, ctx):
        k = _key(ctx)
        self.state.pop(k, None)
        self._persist(ctx)
        await ctx.send("🧹 Initiative channel ini direset.")
        # 🔎 log timeline: init cleared
        try:
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title="Initiative cleared",
                      details="--",
                      etype="init_clear",
                      tags=["combat","init"])
        except Exception:
            pass

    @init_group.command(name="round")
    async def init_round(self, ctx, value: int = None):
        s = self._ensure(ctx)
        if value is None:
            return await ctx.send(f"📜 Round saat ini: **{s['round']}**")
        s["round"] = max(1, value)
        self._persist(ctx)
        await ctx.send(f"📜 Round diset ke **{s['round']}**")
        # 🔎 log timeline: round set
        try:
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title=f"Round set: {s['round']}",
                      details="--",
                      etype="round",
                      tags=["combat","round"])
        except Exception:
            pass

    @init_group.command(name="shuffle")
    async def init_shuffle(self, ctx):
        """
        Acak pointer giliran awal.
        Tidak mengubah urutan initiative, hanya siapa yang jalan dulu.
        """
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada peserta.")
        s["ptr"] = random.randint(0, len(s["order"]) - 1)
        self._persist(ctx)
        embed = self._make_embed(ctx, "🎲 Shuffle Giliran", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    # ===== engage (dramatis start) =====
    @commands.command(name="engage", aliases=["start", "begin"])
    async def engage(self, ctx):
        s = self._ensure(ctx)
        if not s["order"]:
            return await ctx.send("⚠️ Belum ada data initiative. Tambahkan dulu dengan `!init add <Nama> <Skor>`.")

        drum = await ctx.send("🥁 Mengocok urutan giliran...")
        await asyncio.sleep(2)
        try:
            await drum.delete()
        except Exception:
            pass

        self._persist(ctx)
        embed = self._make_embed(ctx, "⚔️ Encounter Dimulai!", s)
        current = s["order"][s["ptr"]][0]
        embed.add_field(name="Giliran Pertama", value=f"👉 **{current}**", inline=False)
        await ctx.send(embed=embed)

    # ===== Akhiri encounter / Victory =====
    @commands.command(name="victory", aliases=["end", "finish", "win"])
    async def victory(self, ctx, *flags):
        """
        Akhiri encounter.
        Opsi:
          keep  - akhiri tanpa hapus daftar musuh
          clear - akhiri dan hapus daftar musuh (default)
          force - paksa selesai walau masih ada musuh > 0 HP
        """
        flags = {f.lower() for f in flags}
        keep_enemies = "keep" in flags
        force_end = "force" in flags

        # ambil state initiative
        k = _key(ctx)
        s = self._ensure(ctx)
        order = s.get("order", [])
        ptr = s.get("ptr", 0)
        rnd = s.get("round", 1)
        current_turn = order[ptr][0] if order else "-"

        # ambil data musuh (kalau ada)
        alive = defeated = total = 0
        enemy_cog = self.bot.get_cog("EnemyStatus")
        if enemy_cog:
            enemies = enemy_cog.state.get(k, {})
            total = len(enemies)
            for v in enemies.values():
                try:
                    hp = int(str(v.get("hp", 0)).strip())
                except Exception:
                    hp = 0
                if hp > 0:
                    alive += 1
                else:
                    defeated += 1

            if alive > 0 and not force_end:
                return await ctx.send(
                    f"⚠️ Masih ada **{alive}** musuh hidup. "
                    "Gunakan `!victory force` untuk memaksa, atau `!victory keep` bila tidak ingin menghapus musuh."
                )

        # buat embed ringkasan
        embed = discord.Embed(
            title="🎉 Victory!",
            description=f"Channel: **{ctx.channel.name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Rangkuman Musuh", value=f"Total: {total} • Alive: {alive} • Defeated: {defeated}", inline=False)
        embed.add_field(name="Round Terakhir", value=str(rnd), inline=True)
        embed.add_field(name="Giliran Terakhir", value=current_turn, inline=True)

        # reset initiative
        self.state[k] = {"order": [], "ptr": 0, "round": 1}

        # clear atau keep musuh
        if enemy_cog and not keep_enemies:
            enemy_cog.state.pop(k, None)

        await ctx.send(embed=embed)
        # 🔎 log timeline: encounter_end
        try:
            log_event(str(ctx.guild.id), str(ctx.channel.id), ctx.author.id,
                      code=None,
                      title="Encounter berakhir",
                      details="Victory",
                      etype="encounter_end",
                      tags=["combat","encounter","end"])
        except Exception:
            pass

    # ===== Aliases global =====
    @commands.command(name="next", aliases=["n"])
    async def alias_next(self, ctx):
        await self.init_next(ctx)

    @commands.command(name="order")
    async def alias_order(self, ctx):
        await self.init_show(ctx)


async def setup(bot):
    cog = InitiativeMemory(bot)
    await bot.add_cog(cog)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                restored = load_initiative_from_memory(str(guild.id), str(channel.id))
                if restored:
                    cog.state[(guild.id, channel.id)] = restored
            except Exception:
                pass
