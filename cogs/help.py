def embed_quick(prefix: str) -> discord.Embed:
    e = discord.Embed(
        title="⚡ Quick Commands & Utility",
        description="Alias singkat & utilitas untuk mempercepat command yang sering dipakai.",
        color=COLOR_QUICK,
        timestamp=datetime.datetime.utcnow()
    )
    e.add_field(
        name="🔹 Status",
        value=(
            f"- `{prefix}dmg <Nama> <jumlah>` = `{prefix}status dmg`\n"
            f"- `{prefix}heal <Nama> <jumlah>` = `{prefix}status heal`\n"
            f"- `{prefix}stat <Nama>` = `{prefix}status show <Nama>`\n"
            f"- `{prefix}party` = `{prefix}status show` (semua karakter)"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Initiative",
        value=(
            f"- `{prefix}next` atau `{prefix}n` = `{prefix}init next`\n"
            f"- `{prefix}order` = `{prefix}init show`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Dice",
        value=(
            f"- `{prefix}r` = `{prefix}roll`\n"
            f"Contoh: `{prefix}r 1d20 +str`"
        ),
        inline=False
    )
    e.add_field(
        name="🔹 Utility",
        value=(
            f"- `{prefix}multi` → jalankan beberapa command sekaligus.\n"
            "  Contoh:\n"
            "  ```txt\n"
            f"  {prefix}multi\n"
            "  status set Alice 20 5 3\n"
            "  status setcore Alice 10 12 14 8 13 9\n"
            "  enemy set Goblin 15 2 4\n"
            "  enemy setcore Goblin 8 14 12 6 10 7\n"
            "  ```\n"
            f"- `{prefix}undo` → batalkan aksi terakhir (HP/Energy/Stamina karakter atau musuh)"
        ),
        inline=False
    )
    e.set_footer(text="Quick & Utility = shortcut dan helper → hasil sama seperti command panjangnya.")
    return e
