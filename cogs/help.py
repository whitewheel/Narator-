import discord
from discord.ext import commands

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ganti help default
        bot.remove_command("help")

    @commands.command(name="help")
    async def help(self, ctx, *, topic: str = None):
        """Custom help command"""

        if not topic:
            embed = discord.Embed(
                title="📖 Bantuan Bot",
                description="Gunakan `!help <command>` untuk detail.\nContoh: `!help init`",
                color=discord.Color.blue()
            )
            embed.add_field(name="🎲 Dice Roller", value="`!roll <XdY+Z>`", inline=False)
            embed.add_field(name="📊 Polling", value="`!poll \"Judul\" opsi1 opsi2 ...`", inline=False)
            embed.add_field(name="🧠 GPT", value="`!ask`, `!define`, `!summarize`, `!story`", inline=False)
            embed.add_field(name="⚔️ Initiative", value="`!init add/show/next/remove/clear/setptr`", inline=False)
            await ctx.send(embed=embed)
            return

        # Detail khusus
        topic = topic.lower()
        if topic == "init":
            text = (
                "**⚔️ Initiative Tracker**\n\n"
                "`!init add <Nama> <Skor>` → Tambah/ubah peserta\n"
                "`!init show` → Tampilkan urutan & giliran saat ini\n"
                "`!init next` → Pindah ke giliran berikutnya\n"
                "`!init setptr <nomor>` → Set giliran manual (mulai 1)\n"
                "`!init remove <Nama>` → Hapus peserta\n"
                "`!init clear` → Reset seluruh tracker\n\n"
                "ℹ️ Data hanya tersimpan sementara (hilang saat bot restart)."
            )
            await ctx.send(embed=discord.Embed(title="!help init", description=text, color=discord.Color.green()))

        elif topic == "roll":
            await ctx.send("🎲 **Dice Roller**\n`!roll 2d6+3` → lempar 2 d6 dengan +3 modifier.")

        elif topic == "poll":
            await ctx.send("📊 **Polling**\n`!poll \"Makan apa?\" Nasi Mie Roti` → bikin polling dengan reaction.")

        elif topic in ("ask", "define", "summarize", "story", "gpt"):
            await ctx.send(
                "🧠 **GPT Commands**\n"
                "`!ask <pertanyaan>` → tanya GPT\n"
                "`!define <kata>` → definisi singkat\n"
                "`!summarize <teks>` → ringkas teks\n"
                "`!story <prompt>` → cerita pendek imersif"
            )
        else:
            await ctx.send("❓ Tidak ada topik itu. Coba `!help` untuk daftar command.")

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
