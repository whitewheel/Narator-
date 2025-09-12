# cogs/gm_cog.py
import os, random, json, re
import discord
from discord.ext import commands
from memory import (
    init_db, save_memory, get_recent, get_latest_summary, write_summary, mark_archived,
    export_all_json, wipe_channel, count_rows, category_icon
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
try:
    from openai import OpenAI
    oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    oai = None

ICON = {"narration":"🟣", "dialogue":"🗨️"}
COLOR = 0x00B3FF

# GM hint dipersingkat (sesuai permintaanmu)
GM_HINT = (
    "Kamu Game Master/Narator Technonesia. Gaya sinematik, padat, responsif. "
    "Bisa berbicara sebagai NPC bila relevan. Tunda quest resmi sampai pemain menerima."
)

class GM(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()
        self.gm_channels: set[tuple[str,str]] = set()
        self.settings: dict[tuple[str,str], dict] = {}  # per-channel: {"length":"auto|short|medium|long","freedom":"low|normal|high","battle":bool}

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
        title = f"{ICON.get(typ,'🟣')} {speaker} • {'Dialog' if typ=='dialogue' else 'Narasi'}"
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

    async def _ask_json(self, prompt:str, length:str, freedom:str, ooc:bool) -> dict | None:
        if not oai:
            # fallback lokal
            return {
                "type":"narration" if not ooc else "dialogue",
                "speaker":"Narrator" if not ooc else "GM",
                "length":"short",
                "text":"Neon memantul di genangan; drone patroli melintas.",
                "choices":["Lihat sekitar","Cari NPC"] if not ooc else [],
                "tags":{"location":"Java Arcology"} if not ooc else {}
            }
        temp = 0.7 if freedom=="normal" else (0.4 if freedom=="low" else 0.95)
        schema = (
          "Keluarkan JSON SAJA dgn schema: "
          '{"type":"narration|dialogue","speaker":"Narrator atau nama NPC",'
          '"length":"short|medium|long","text":"...",'
          '"choices":["opsi1","opsi2"],'
          '"tags":{"location":"...", "npcs":["..."], "quest_hook": true}}. '
          f'Batas kalimat sesuai length="{length}".'
        )
        sys = "Kamu GM/Narator Technonesia. Efisien, imersif, tidak bertele-tele."
        if ooc:
            sys = "Kamu GM/Narator yang sadar diri (bot). Jawab meta singkat dan jelas, bukan narasi panjang."
        rsp = oai.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type":"json_object"},
            temperature=temp,
            max_tokens= 240 if length=="short" else (360 if length=="medium" else 520),
            messages=[
                {"role":"system","content": sys},
                {"role":"user","content": schema},
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
            "`!gm battle <on|off>`, `!gm status`, "
            "`!gm reset_memory SAYA_MENGERTI_AKAN_MENGHAPUS_SEMUA_DATA`"
        )

    @gm.command(name="on")
    async def gm_on(self, ctx:commands.Context):
        key = self._key(ctx.guild.id, ctx.channel.id)
        self.gm_channels.add(key)
        self._set_setting(key,"length","auto")
        self._set_setting(key,"freedom","normal")
        self._set_setting(key,"battle",False)
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
        await ctx.send(f"📊 GM: **{state}** | rows: **{total}** | style: {s.get('length','auto')} | freedom: {s.get('freedom','normal')} | battle: {s.get('battle',False)}")

    @gm.command(name="next")
    async def gm_next(self, ctx:commands.Context):
        await self._narrate(ctx.channel, None)

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

        # deteksi OOC (( ... ))
        content = message.content.strip()
        is_ooc = self._is_ooc(content)
        if is_ooc:
            content = content[2:-2].strip()  # hilangkan (( ))

        # simpan ke history
        save_memory(message.guild.id, message.channel.id, message.author.id, "history", content,
                    {"author": message.author.display_name, "ooc": is_ooc})

        await self._narrate(message.channel, content, is_ooc)

    # --------- Narasi utama ----------
    async def _narrate(self, channel: discord.TextChannel, player_text: str | None, is_ooc: bool=False):
        g, ch = channel.guild.id, channel.id
        key = self._key(g, ch)

        # 1) tarik konteks
        summary = get_latest_summary(g, ch) or "(Belum ada rekap.)"
        recent = get_recent(g, ch, None, 10)
        ctx_text = "\n".join(f"[{cat}] {content}" for (_id,cat,content,meta,ts) in reversed(recent[-10:]))

        # 2) panjang & kreativitas
        style = self._get_setting(key, "length", "auto")
        hint = self._length_hint(player_text) if style=="auto" else style
        freedom = self._get_setting(key, "freedom", "normal")
        battle_mode = self._get_setting(key, "battle", False)

        # 3) twist ringan
        d20 = random.randint(1,20)
        twist = ("Encounter kecil" if d20<=5 else "NPC relevan" if d20<=10 else "Benih quest" if d20<=15 else "Ambient/world event")

        rules = [
            f"Target length: {hint} (short=1-3 kalimat, medium=3-5, long=5-8).",
            "Hindari bertele-tele; langsung aksi/dialog.",
            "Respons bisa Narasi atau Dialog NPC.",
            "Jangan drop quest resmi; beri hook dulu.",
            "Berikan 1–3 pilihan jika relevan."
        ]
        if battle_mode:
            rules += ["Mode pertempuran aktif: fokus pada aksi singkat, hasil (hit/miss), kondisi ringkas."]

        prompt = f"""{GM_HINT}

# KONTEKS
Rekap: {summary}

Riwayat (lama→baru, singkat):
{ctx_text}

D20={d20}: {twist}

Aturan:
- """ + "\n- ".join(rules) + f"""

Input pemain (opsional):
{player_text or '(none)'}
"""

        # 4) typing indicator + spinner
        async with channel.typing():
            spinner = await channel.send("⌛ Narator merender…")
            data = await self._ask_json(prompt, hint, freedom, is_ooc)
            await spinner.delete()

        if not data:
            data = {"type":"narration","speaker":"Narrator","length":"short",
                    "text":"Lampu neon memantul di genangan; kota tetap gelisah.", "choices":[], "tags":{}}

        # Opsional "lead-in" untuk jawaban panjang
        if data.get("length") == "long":
            await channel.send("…")

        embed = self._render_embed(data)
        await channel.send(embed=embed)

        # simpan jawaban GM ke history
        save_memory(g, ch, "gm", "history", data.get("text",""), {"role":"gm","len":data.get("length"),"d20":d20, "battle":battle_mode})

        # Ringkas otomatis sederhana (arsipkan di luar 40 terbaru)
        active_hist = get_recent(g, ch, category="history", limit=60)
        if len(active_hist) >= 40:
            ids = [row[0] for row in active_hist][40:]
            if ids:
                snippet = "\n".join(f"- {r[2][:120]}" for r in reversed(active_hist[40:50]))
                # minta ringkasan singkat (gunakan format biasa, tidak perlu JSON)
                if oai:
                    try:
                        r = oai.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role":"system","content":"Ringkas 5–7 kalimat, fokus kronologi & tokoh."},
                                      {"role":"user","content": snippet}],
                            temperature=0.4, max_tokens=220
                        )
                        summary_text = r.choices[0].message.content.strip()
                    except Exception:
                        summary_text = "Ringkasan sesi (otomatis)."
                else:
                    summary_text = "Ringkasan sesi (otomatis)."
                write_summary(g, ch, summary_text, {"archived_ids": ids})
                mark_archived(g, ch, ids)

async def setup(bot: commands.Bot):
    await bot.add_cog(GM(bot))
