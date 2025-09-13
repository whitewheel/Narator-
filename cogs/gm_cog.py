
import discord
from discord.ext import commands
from openai import OpenAI
from typing import List, Dict, Any, Optional
from datetime import datetime
from memory import save_memory, get_recent

client = OpenAI()

def _key(ctx):
    return (str(ctx.guild.id), str(ctx.channel.id))

START_WORDS = ["start", "mulai", "gas", "lanjut"]
STYLE_PRESETS = ["noir","anime","cyberpunk","high-fantasy","dark-fantasy","epic-saga","slice-of-life","surreal-horror","technonesia"]
DEPTH_LEVELS = ["short","medium","long"]

def _style_hint(style: str) -> str:
    style = (style or "default").lower()
    mapping = {
        "noir": "Gaya noir detektif gelap, sinis, penuh bayangan.",
        "anime": "Gaya anime dramatis, emosional, penuh ekspresi heroik.",
        "cyberpunk": "Gaya cyberpunk neon-dystopia, korporasi, teknologi usang.",
        "high-fantasy": "Gaya high fantasy epik, magis, metafora indah.",
        "dark-fantasy": "Gaya dark fantasy grimdark, brutal, suram.",
        "epic-saga": "Gaya legenda epik, skala besar, heroik.",
        "slice-of-life": "Gaya ringan, hangat, keseharian, fokus interaksi.",
        "surreal-horror": "Gaya horor surealis, aneh, mengganggu, eldritch.",
        "technonesia": "Campuran cyberpunk + mistik Nusantara; neon, klenik, doa & data."
    }
    return mapping.get(style, "Gaya narasi netral sinematik.")

def _depth_hint(depth: str) -> str:
    if depth == "short":
        return "Batasi ke 2-3 kalimat ringkas."
    if depth == "long":
        return "Buat 6-10 kalimat detail, sinematik."
    return "Buat 3-5 kalimat seimbang."

def _auto_style_from_scene(scene_text: str) -> str:
    s = (scene_text or "").lower()
    if any(k in s for k in ["arcology","neon","corp","artha","dyne"]):
        return "cyberpunk"
    if any(k in s for k in ["keris","ritual","kemenyan","kuil","candi","hutan"]):
        return "technonesia"
    if any(k in s for k in ["crypt","catacomb","dungeon","undead","curse"]):
        return "dark-fantasy"
    if any(k in s for k in ["boss","legend","ancient","prophecy"]):
        return "epic-saga"
    return "slice-of-life"

class GMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled: Dict[Any,bool] = {}
        self.mode: Dict[Any,str] = {}         # auto / narrator / assistant / dual
        self.started: Dict[Any,bool] = {}     # story started or not
        self.styles: Dict[Any,str] = {}
        self.depths: Dict[Any,str] = {}       # short/medium/long

    # ---------- helpers ----------
    def _is_on(self, ctx): return self.enabled.get(_key(ctx), False)
    def _get_mode(self, ctx): return self.mode.get(_key(ctx), "auto")
    def _style(self, ctx): return self.styles.get(_key(ctx), "default")
    def _depth(self, ctx): return self.depths.get(_key(ctx), "medium")

    def _save_internal(self, ctx, role: str, text: str, kind: str = "assistant"):
        g,c = _key(ctx)
        meta = {"kind": kind, "style": self._style(ctx), "depth": self._depth(ctx)}
        save_memory(g, c, ctx.author.id if ctx and ctx.author else 0, "gm_internal", f"{role.upper()}: {text}", meta)

    def _latest_scene_text(self, ctx) -> str:
        g,c = _key(ctx)
        rows = get_recent(g, c, "scene", 10)
        for (_id, cat, content, meta, ts) in rows:
            if cat == "scene":
                return content or ""
        return ""

    async def _narrate(self, ctx, topic: str, extra: Optional[str] = None, force_style: Optional[str] = None):
        """Call GPT to produce narration according to style/depth, log internally, post to chat."""
        style = (force_style or self._style(ctx) or "default").lower()
        if style == "default":
            auto_style = _auto_style_from_scene(self._latest_scene_text(ctx))
            style = auto_style
        depth = self._depth(ctx)

        sys = f"Kamu adalah Narator AI. { _style_hint(style) } { _depth_hint(depth) } Tulis dalam bahasa Indonesia."
        user = f"Narasikan: {topic}."
        if extra:
            user += f" Konteks: {extra}."
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":sys},{"role":"user","content":user}],
                max_tokens=300, temperature=0.8
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            text = f"(narator terbatuk sejenak...) {topic}"

        self._save_internal(ctx, "narrator", text, kind="narrator")
        await ctx.send(text)

    async def _assistant_reply(self, ctx, message: str):
        """Assistant reply (meta/helper), logged internally."""
        sys = "Kamu adalah Assistant GM (OOC). Jawab ringkas dan jelas, berikan status/opsi yang relevan."
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":sys},{"role":"user","content":message}],
                max_tokens=180, temperature=0.5
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            text = "(…)"

        self._save_internal(ctx, "assistant", f"Q:{message} | A:{text}", kind="assistant")
        await ctx.send(text)

    # ---------- base commands ----------
    @commands.group(name="gm", invoke_without_command=True)
    async def gm(self, ctx):
        await ctx.send("Gunakan: `!gm on`, `!gm off`, `!gm mode <auto|narrator|assistant|dual>`, `!gm depth <short|medium|long>`, `!gm quest suggest`, `!gm npc suggest`, `!gm item suggest`, `!gm encounter suggest|apply`, `!style <nama>`")

    @gm.command(name="on")
    async def gm_on(self, ctx):
        k = _key(ctx)
        self.enabled[k] = True
        self.mode[k] = "auto"
        self.started[k] = False
        self.depths[k] = "medium"
        await ctx.send("🎙️ GM aktif (Assistant dulu). Ngobrol/briefing dulu boleh. Ketik **start/mulai/gas** kalau mau mulai cerita.")

    @gm.command(name="off")
    async def gm_off(self, ctx):
        k = _key(ctx)
        self.enabled[k] = False
        await ctx.send("🎙️ GM **OFF**.")

    @gm.command(name="mode")
    async def gm_mode(self, ctx, *, mode: str):
        k = _key(ctx); mode = mode.lower()
        if mode not in ["auto","narrator","assistant","dual"]:
            return await ctx.send("Mode tidak valid. Gunakan: auto | narrator | assistant | dual")
        self.mode[k] = mode
        await ctx.send(f"⚙️ GM mode: **{mode}**")

    @gm.command(name="depth")
    async def gm_depth(self, ctx, *, level: str):
        k = _key(ctx); level = level.lower()
        if level not in DEPTH_LEVELS:
            return await ctx.send("Depth tidak valid. Gunakan: short | medium | long")
        self.depths[k] = level
        await ctx.send(f"📏 Depth narasi: **{level}**")

    @gm.command(name="force")
    async def gm_force_start(self, ctx):
        k = _key(ctx)
        if not self.enabled.get(k, False):
            return await ctx.send("❌ GM tidak aktif.")
        self.started[k] = True
        await ctx.send("📖 Force start → Narator mode berjalan.")

    @commands.command(name="style")
    async def style(self, ctx, *, style: str):
        st = style.lower()
        if st not in STYLE_PRESETS and st != "default":
            return await ctx.send(f"Style tidak dikenal. Preset: {', '.join(STYLE_PRESETS)} atau 'default'.")
        self.styles[_key(ctx)] = st
        await ctx.send(f"🎨 Style: **{st}**")

    # ---------- suggestions / generators ----------
    @gm.command(name="quest")
    async def gm_quest(self, ctx, subcmd: str = None):
        if subcmd and subcmd.lower() == "suggest":
            g,c = _key(ctx)
            rows = get_recent(g, c, None, 30)
            context = []
            for (_id, cat, content, meta, ts) in rows:
                context.append(f"[{cat}] {content[:200]}")
            prompt = "Buat 1 ide quest (judul, deskripsi, hook singkat) dari konteks: \n" + "\n".join(context[-12:])
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"system","content":"Kamu Game Master AI."},{"role":"user","content":prompt}],
                    max_tokens=240, temperature=0.8
                )
                text = resp.choices[0].message.content.strip()
            except Exception as e:
                text = "(gagal membuat saran quest)"
            self._save_internal(ctx, "assistant", f"QuestSuggest: {text}")
            embed = discord.Embed(title="💡 Quest Suggestion", description=text, color=discord.Color.gold())
            await ctx.send(embed=embed)

    @gm.command(name="npc")
    async def gm_npc(self, ctx, subcmd: str = None):
        if subcmd and subcmd.lower() == "suggest":
            g,c = _key(ctx)
            scene = self._latest_scene_text(ctx)
            prompt = f"Buat 1 NPC yang cocok dengan scene berikut: {scene}. Sertakan: Nama, Peran, Kepribadian, Rahasia singkat."
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"system","content":"Kamu pembuat NPC ringkas."},{"role":"user","content":prompt}],
                    max_tokens=220, temperature=0.9
                )
                text = resp.choices[0].message.content.strip()
            except Exception as e:
                text = "(gagal membuat NPC)"
            self._save_internal(ctx, "assistant", f"NPCSuggest: {text}")
            await ctx.send(embed=discord.Embed(title="🧩 NPC Suggestion", description=text, color=discord.Color.blurple()))

    @gm.command(name="item")
    async def gm_item(self, ctx, subcmd: str = None):
        if subcmd and subcmd.lower() == "suggest":
            g,c = _key(ctx)
            scene = self._latest_scene_text(ctx)
            prompt = f"Buat 1 item menarik terkait scene '{scene}'. Sertakan: Nama, Rarity, Efek (singkat), Flavor."
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"system","content":"Kamu pembuat item ringkas."},{"role":"user","content":prompt}],
                    max_tokens=200, temperature=0.9
                )
                text = resp.choices[0].message.content.strip()
            except Exception as e:
                text = "(gagal membuat item)"
            self._save_internal(ctx, "assistant", f"ItemSuggest: {text}")
            await ctx.send(embed=discord.Embed(title="🎁 Item Suggestion", description=text, color=discord.Color.green()))

    @gm.command(name="encounter")
    async def gm_encounter(self, ctx, subcmd: str = None):
        g,c = _key(ctx)
        if subcmd and subcmd.lower() == "suggest":
            scene = self._latest_scene_text(ctx)
            prompt = f"Buat 1 rancangan encounter (ringkas): enemy list + role, loot, dan quest hook singkat. Scene: {scene}."
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"system","content":"Kamu perancang encounter ringkas."},{"role":"user","content":prompt}],
                    max_tokens=260, temperature=0.9
                )
                text = resp.choices[0].message.content.strip()
            except Exception as e:
                text = "(gagal membuat encounter)"
            self._save_internal(ctx, "assistant", f"EncounterSuggest: {text}")
            await ctx.send(embed=discord.Embed(title="⚔️ Encounter Suggestion", description=text, color=discord.Color.red()))
        elif subcmd and subcmd.lower() == "apply":
            # Minimal implementation: store a marker so other cogs (enemy_status) can read/apply manually.
            rows = get_recent(g, c, "gm_internal", 20)
            plan = None
            for (_id, cat, content, meta, ts) in rows:
                if "EncounterSuggest:" in content:
                    plan = content.split("EncounterSuggest:",1)[-1].strip()
            if not plan:
                return await ctx.send("Tidak ada saran encounter terbaru untuk di-apply.")
            save_memory(g, c, ctx.author.id, "encounter_plan", plan, {"applied": True, "ts": datetime.utcnow().isoformat()})
            await ctx.send("✅ Encounter plan disimpan. (Spawn musuh/loot sesuai rencana via perintah enemy/loot)")
        else:
            await ctx.send("Gunakan: `!gm encounter suggest` atau `!gm encounter apply`")

    # ---------- cutscenes / immersion ----------
    @commands.command(name="cutscene")
    async def cutscene(self, ctx, *, topic: str):
        """Manual trigger cutscene pendek sesuai style/depth."""
        await self._narrate(ctx, topic)

    @commands.command(name="victory")
    async def victory(self, ctx):
        """Epilog singkat setelah menang."""
        await self._narrate(ctx, "Kemenangan party dan suasana sesudah pertempuran", extra=self._latest_scene_text(ctx))

    @commands.command(name="levelup")
    async def levelup(self, ctx, *, name: str):
        """Cutscene level up untuk karakter bernama 'name'."""
        await self._narrate(ctx, f"Proses level up yang dialami {name}", extra="Berikan nuansa heroik.")

    # ---------- listener: auto-switch chat ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if not ctx or not ctx.guild:
            return
        k = _key(ctx)
        if not self.enabled.get(k, False):
            return

        content = message.content.strip()
        if content.startswith("!"):   # let commands flow
            return

        # pre-start: look for start words once
        if not self.started.get(k, False):
            if any(w in content.lower() for w in START_WORDS):
                self.started[k] = True
                await message.channel.send("📖 Cerita dimulai! (Narator mode ON)")
                return
            # assistant small talk
            await self._assistant_reply(ctx, content)
            return

        # after started → auto mode or overrides
        mode = self._get_mode(ctx)
        if mode == "assistant":
            await self._assistant_reply(ctx, content)
        elif mode == "narrator":
            await self._narrate(ctx, f"Aksi/ucapan pemain: {content}")
        elif mode == "dual":
            await self._narrate(ctx, f"Aksi/ucapan pemain: {content}")
            await self._assistant_reply(ctx, f"Ringkas info terkait '{content}'")
        else:  # auto
            # heuristic: if question/meta words → assistant else narrator
            meta_words = ["status","quest","berapa","dimana","siapa","apa","bagaimana","gimana","hp","xp","gold","inventory","favor","scene"]
            if any(w in content.lower() for w in meta_words) or content.endswith("?"):
                await self._assistant_reply(ctx, content)
            else:
                await self._narrate(ctx, f"Aksi/ucapan pemain: {content}")

async def setup(bot):
    await bot.add_cog(GMCog(bot))
