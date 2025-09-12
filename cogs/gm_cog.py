# cogs/gm_cog.py
import os, random, json, re
import discord
from discord.ext import commands
from memory import (
    init_db, save_memory, get_recent, get_latest_summary, write_summary, mark_archived,
    export_all_json, wipe_channel, count_rows, category_icon, peek_related
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("GM_MODEL", "gpt-4o-mini")

try:
    from openai import OpenAI
    oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    oai = None

ICON = {"narration":"🟣", "dialogue":"🗨️"}
COLOR = 0x00B3FF

# GM netral: tidak tahu lore, hanya pakai memori
GM_HINT = (
    "Kamu adalah GM/Narator NETRAL yang tidak mengetahui dunia/plot di awal. "
    "Hanya gunakan informasi dari KONTEKS & FAKTA TERKAIT (memori). "
    "Jika tidak ada catatan, katakan singkat 'Belum ada catatan' dan tawarkan: "
    "bertanya klarifikasi atau menambahkan entri baru (setelah pemain setuju). "
    "Hindari membuat nama/entitas baru tanpa konfirmasi. Gaya singkat dan responsif."
)

QUESTION_WORDS = (
    "apa","siapa","kapan","dimana","di mana","bagaimana","mengapa","kenapa",
    "berapa","bisakah","bolehkah","mungkinkah","gimana","kenap"
)

def detect_intent(text: str) -> str:
    """qa | dialogue | action | ooc"""
    if not text: return "action"
    t = text.lower().strip()
    if t.startswith("((") and t.endswith("))"): return "ooc"
    if t.startswith("?") or t.endswith("?") or any(re.search(rf"\b{w}\b", t) for w in QUESTION_WORDS):
        return "qa"
    if re.search(r"[\"“].+?[\"”]", t) or any(k in t for k in ["kataku","katanya","aku berkata","dia berkata","ujar","tanya"]):
        return "dialogue"
    return "action"

class GM(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()
        self.gm_channels: set[tuple[str,str]] = set()
        # per-channel: length auto|short|medium|long, freedom low|normal|high, battle bool, canon strict|soft
        self.settings: dict[tuple[str,str], dict] = {}

    # --------- Utils ----------
    def _key(self, g, ch): return (str(g), str(ch))
    def _get_setting(self, key, name, default):
        return self.settings.get(key, {}).get(name, default)
    def _set_setting(self, key, name, value):
        self.settings.setdefault(key, {})[name] = value
        save_memory(key[0], key[1], "system", "gm_settings", f"set {name}={value}", {})

    def _length_hint(self, user_text: str | None) -> str:
        if not user_text: return "medium"
        t = user_text.lower().strip()
        if len(t) <= 18 or any(k in t for k in ["ok","oke","ya","lanjut","ke bar","ke market","pergi"]):
            return "short"
        if any(k in t for k in ["jelaskan","detail","investigasi","lihat sekitar","terangkan"]):
            return "long"
        return "medium"

    def _is_ooc(self, text:str)->bool:
        t = text.strip()
        return t.startswith("((") and t.endswith("))")

    def _render_embed(self, data: dict) -> discord.Embed:
        typ = data.get("type", "narration")
        speaker = data.get("speaker", "Narrator")
        icon = "❓" if speaker=="GM" and typ=="dialogue" else ICON.get(typ,"🟣")
        title = f"{icon} {speaker} • {'Dialog' if typ=='dialogue' else 'Narasi'}"
        desc = data.get("text", "")
        embed = discord.Embed(title=title, description=desc, color=COLOR)
        # choices
        chs = data.get("choices") or []
        if chs:
            embed.add_field(name="Pilihan", value="\n".join(f"• {c}" for c in chs), inline=False)
        # tags footer
        tags = data.get("tags") or {}
        bits = []
        if tags.get("location"): bits.append(f"📍 {tags['location']}")
        if tags.get("npcs"): bits.append(f"👤 {', '.join(tags['npcs'])}")
        if tags.get("quest_hook"): bits.append("🪧 Hook misi")
        if bits: embed.set_footer(text=" | ".join(bits))
        return embed

    async def _ask_json(self, prompt:str, length:str, freedom:str, ooc:bool, intent:str, canon:str) -> dict | None:
        # fallback lokal
        if not oai:
            if intent == "qa" or ooc:
                return {"type":"dialogue","speaker":"GM","length":"short","text":"(Belum ada catatan. Mau tambah entri atau klarifikasi?)","choices":[],"tags":{}}
            return {"type":"narration","speaker":"Narrator","length":"short","text":"Ambient generik: lampu redup dan hujan halus.","choices":["Lihat sekitar"],"tags":{}}

        temp = 0.7 if freedom=="normal" else (0.4 if freedom=="low" else 0.95)
        if intent == "qa" or ooc:
            temp = min(temp, 0.5)  # deterministik untuk jawaban langsung

        schema = (
          "Keluarkan JSON SAJA: "
          '{"type":"narration|dialogue","speaker":"Narrator atau nama NPC",'
          '"length":"short|medium|long","text":"...",'
          '"choices":["opsi1","opsi2"],'
          '"tags":{"location":"...", "npcs":["..."], "quest_hook": true}}.'
        )

        # === Kebijakan pengetahuan & canon ===
        base_knowledge = (
            "Kamu TIDAK mengetahui dunia/plot di luar yang ada di KONTEKS & FAKTA TERKAIT. "
            "Jika sesuatu tidak ada di memori, jawab: 'Belum ada catatan.' lalu tawarkan klarifikasi atau penambahan entri (setelah pemain setuju). "
            "Jangan bertentangan dengan fakta yang sudah tersimpan."
        )
        if ooc:
            sys = "Kamu GM/Narator (bot) yang menjawab meta singkat dan jelas."
        elif intent == "qa":
            sys = "Kamu GM. Jawab pertanyaan pemain langsung, ringkas, tanpa memajukan cerita."
        else:
            sys = "Kamu GM/Narator. Efisien, imersif, tidak bertele-tele."

        if canon == "strict":
            canon_rules = (
                "Canon STRICT: dilarang memperkenalkan proper noun/entitas baru tanpa persetujuan pemain. "
                "Jika butuh warna, gunakan ambient generik tanpa nama khusus."
            )
        else:
            canon_rules = (
                "Canon SOFT: boleh menambah warna kecil generik (tanpa proper noun), "
                "tetap tidak boleh kontradiksi dan jangan memajukan lore besar tanpa konfirmasi."
            )

        sys_full = f"{sys} {base_knowledge} {canon_rules}"

        rsp = oai.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type":"json_object"},
            temperature=temp,
            max_tokens= 220 if length=="short" else (340 if length=="medium" else 520),
            messages=[
                {"role":"system","content": sys_full},
                {"role":"user","content": schema + " Patuhi mode QA/OOC & Canon."},
                {"role":"user","content": prompt},
            ],
        )
        try:
            return json.loads(rsp.choices[0].message.content)
        except Exception:
            return None

    # --------- Commands ----------
    @commands.group(name="gm", invoke_without_command=True)
    async def gm(self, ctx:commands.Context):
        await ctx.send(
            "Gunakan: `!gm on`, `!gm off`, `!gm next`, "
            "`!gm style <auto|short|medium|long>`, `!gm freedom <low|normal|high>`, "
            "`!gm canon <strict|soft>`, `!gm battle <on|off>`, `!gm status`, "
            "`!gm reset_memory SAYA_MENGERTI_AKAN_MENGHAPUS_SEMUA_DATA`"
        )

    @gm.command(name="on")
    async def gm_on(self, ctx:commands.Context):
        key = self._key(ctx.guild.id, ctx.channel.id)
        self.gm_channels.add(key)
        self._set_setting(key,"length","auto")
        self._set_setting(key,"freedom","normal")
        self._set_setting(key,"battle",False)
        self._set_setting(key,"canon","strict")  # default anti-ngarang
        save_memory(ctx.guild.id, ctx.channel.id, ctx.author.id, "system", "GM ON", {})
        await ctx.send("✅ **GM mode ON** untuk channel ini. Tulis natural tanpa `!`.")

    @gm.command(name="off")
    async def gm_off(self, ctx:commands.Context):
        key = self._key(ctx.guild.id, ctx.channel.id)
        self.gm_channels.discard(key)
        save_memory(ctx.guild.id, ctx.channel.id, ctx.author.id, "system", "GM OFF", {})
        await ctx.send("🛑 **GM mode OFF** untuk channel ini.")

    @gm.command(name="style")
    async def gm_style(self, ctx:commands.Context, mode:str):
        mode = mode.lower().strip()
        if mode not in {"auto","short","medium","long"}:
            return await ctx.send("❌ Pilih: `auto|short|medium|long`")
        key = self._key(ctx.guild.id, ctx.channel.id)
        self._set_setting(key,"length",mode)
        await ctx.send(f"✨ Style panjang respons: **{mode}**")

    @gm.command(name="freedom")
    async def gm_freedom(self, ctx:commands.Context, level:str):
        level = level.lower().strip()
        if level not in {"low","normal","high"}:
            return await ctx.send("❌ Pilih: `low|normal|high`")
        key = self._key(ctx.guild.id, ctx.channel.id)
        self._set_setting(key,"freedom",level)
        await ctx.send(f"🧠 Kreativitas GM: **{level}**")

    @gm.command(name="canon")
    async def gm_canon(self, ctx: commands.Context, mode: str):
        mode = mode.lower().strip()
        if mode not in {"strict","soft"}:
            return await ctx.send("❌ Pilih: `strict|soft`")
        key = self._key(ctx.guild.id, ctx.channel.id)
        self._set_setting(key, "canon", mode)
        await ctx.send(f"📚 Canon mode: **{mode}** "
                       f"({'tanpa proper noun baru' if mode=='strict' else 'warna kecil boleh, tanpa kontradiksi'})")

    @gm.command(name="battle")
    async def gm_battle(self, ctx:commands.Context, mode:str):
        mode = mode.lower().strip()
        if mode not in {"on","off"}:
            return await ctx.send("❌ Pilih: `on|off`")
        key = self._key(ctx.guild.id, ctx.channel.id)
        self._set_setting(key,"battle", mode=="on")
        await ctx.send(f"⚔️ Battle mode: **{mode.upper()}** (narasi lebih ringkas & fokus aksi)")

    @gm.command(name="status")
    async def gm_status(self, ctx:commands.Context):
        key = self._key(ctx.guild.id, ctx.channel.id)
        state = "ON" if key in self.gm_channels else "OFF"
        total = count_rows(ctx.guild.id, ctx.channel.id)
        s = self.settings.get(key, {})
        await ctx.send(f"📊 GM: **{state}** | rows: **{total}** | "
                       f"style: {s.get('length','auto')} | freedom: {s.get('freedom','normal')} | "
                       f"battle: {s.get('battle',False)} | canon: {s.get('canon','strict')}")

    @gm.command(name="next")
    async def gm_next(self, ctx:commands.Context):
        await self._narrate(ctx.channel, None, False, "action")

    @gm.command(name="reset_memory")
    async def gm_reset_mem(self, ctx:commands.Context, confirm:str=None):
        phrase = "SAYA_MENGERTI_AKAN_MENGHAPUS_SEMUA_DATA"
        if confirm != phrase:
            return await ctx.send(f"⚠️ Ini akan MENGHAPUS SEMUA data channel ini.\nKetik: `!gm reset_memory {phrase}` untuk konfirmasi.")
        path = export_all_json("/data/memory_export.json")
        wipe_channel(ctx.guild.id, ctx.channel.id)
        await ctx.send(f"🧹 Memori channel ini sudah dihapus. Backup: `{path}`")

    # --------- Listener (percakapan natural) ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.content.strip().startswith("!"):
            return
        key = self._key(message.guild.id, message.channel.id)
        if key not in self.gm_channels:
            return

        content = message.content.strip()
        is_ooc = self._is_ooc(content)
        if is_ooc:
            content = content[2:-2].strip()

        # simpan ke history
        save_memory(message.guild.id, message.channel.id, message.author.id, "history", content,
                    {"author": message.author.display_name, "ooc": is_ooc})

        intent = detect_intent(content)
        await self._narrate(message.channel, content, is_ooc, intent)

    # --------- Narasi utama ----------
    async def _narrate(self, channel: discord.TextChannel, player_text: str | None,
                       is_ooc: bool=False, intent: str="action"):
        g, ch = channel.guild.id, channel.id
        key = self._key(g, ch)

        # 1) Tarik konteks
        summary = get_latest_summary(g, ch) or "(Belum ada rekap.)"
        recent = get_recent(g, ch, None, 10)
        ctx_text = "\n".join(f"[{cat}] {content}" for (_id,cat,content,meta,ts) in reversed(recent[-10:]))

        # 1b) Fakta terkait dari memori (baca sebelum menjawab)
        terms = []
        if player_text:
            terms = [w for w in re.findall(r"[A-Za-zÀ-ÿ0-9_-]{4,}", player_text)]
        facts = peek_related(g, ch, terms)[:6]
        facts_text = ("\n".join(f"- {f}" for f in facts)) if facts else "(tidak ada fakta khusus)"

        # 2) Panjang & kreativitas
        style = self._get_setting(key, "length", "auto")
        hint = self._length_hint(player_text) if style=="auto" else style
        freedom = self._get_setting(key, "freedom", "normal")
        battle_mode = self._get_setting(key, "battle", False)
        canon = self._get_setting(key, "canon", "strict")

        # 3) Twist ringan (disabled untuk QA/OOC)
        d20 = None
        twist = None
        if not (is_ooc or intent == "qa"):
            d20 = random.randint(1,20)
            twist = ("Encounter kecil" if d20<=5 else "NPC relevan" if d20<=10 else "Benih quest" if d20<=15 else "Ambient/world event")

        # RULES
        rules = [
            "Selalu prioritaskan fakta dari memori (Fakta terkait).",
            "Jika fakta tidak memadai, sampaikan 'Belum ada catatan' lalu tawarkan klarifikasi/penambahan entri.",
            f"Target length: {hint} (short=1-3 kalimat, medium=3-5, long=5-8).",
            "Hindari bertele-tele; langsung aksi/dialog."
        ]
        if intent == "qa":
            rules += [
                "MODE: QA. Jawab pertanyaan pemain secara langsung sebagai GM.",
                "Jangan menambah event/encounter/NPC/quest baru.",
                "Jangan memajukan timeline cerita.",
                "Output JSON: type='dialogue', speaker='GM', choices=[], tags={}.",
            ]
        else:
            rules += [
                "Respons bisa Narasi atau Dialog NPC.",
                "Jangan drop quest resmi; beri hook dulu.",
                "Berikan 1–3 pilihan jika relevan."
            ]
            if battle_mode:
                rules += ["Mode pertempuran aktif: fokus pada aksi singkat, hit/miss, kondisi ringkas."]

        prompt = f"""{GM_HINT}

# KONTEKS
Rekap:
{summary}

Riwayat (lama→baru, ringkas):
{ctx_text}

Fakta terkait:
{facts_text}

{'' if not twist else f'D20 twist: {twist}'}

Aturan:
- """ + "\n- ".join(rules) + f"""

Input pemain (opsional):
{player_text or '(none)'}
"""

        # 4) Typing + spinner
        async with channel.typing():
            spinner = await channel.send("⌛ Narator merender…")
            try:
                data = await self._ask_json(prompt, hint, freedom, is_ooc, intent, canon)
            finally:
                try: await spinner.delete()
                except: pass

        if not data:
            data = {"type":"dialogue" if (intent=="qa" or is_ooc) else "narration",
                    "speaker":"GM" if (intent=="qa" or is_ooc) else "Narrator",
                    "length":"short","text":"(Singkat.)","choices":[],"tags":{}}

        # Paksa patuh QA/OOC
        if intent == "qa" or is_ooc:
            data["type"] = "dialogue"
            data["speaker"] = "GM"
            data["choices"] = []
            data["tags"] = {}
            if data.get("length") == "long":
                data["length"] = "short"

        # lead-in bila panjang
        if data.get("length") == "long":
            await channel.send("…")

        embed = self._render_embed(data)
        await channel.send(embed=embed)

        # simpan jawaban GM
        save_memory(g, ch, "gm", "history", data.get("text",""),
                    {"role":"gm","len":data.get("length"),"d20":d20, "battle":battle_mode, "intent":intent, "canon":canon})

        # Ringkas otomatis sederhana (arsipkan di luar 40 terbaru)
        active_hist = get_recent(g, ch, category="history", limit=60)
        if len(active_hist) >= 40:
            ids = [row[0] for row in active_hist][40:]
            if ids:
                snippet = "\n".join(f"- {r[2][:120]}" for r in reversed(active_hist[40:50]))
                summary_text = "Ringkasan sesi (otomatis)."
                if oai:
                    try:
                        r = oai.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[{"role":"system","content":"Ringkas 5–7 kalimat, fokus kronologi & tokoh."},
                                      {"role":"user","content": snippet}],
                            temperature=0.4, max_tokens=220
                        )
                        summary_text = r.choices[0].message.content.strip()
                    except Exception:
                        pass
                write_summary(g, ch, summary_text, {"archived_ids": ids})
                mark_archived(g, ch, ids)

async def setup(bot: commands.Bot):
    await bot.add_cog(GM(bot))
