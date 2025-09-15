import discord

# ===== Embed Templates =====
def info_embed(title: str, desc: str):
    """Embed biru dengan ikon ℹ️ → untuk informasi/help."""
    return discord.Embed(
        title=f"ℹ️ {title}",
        description=desc,
        color=discord.Color.blue()
    )

def error_embed(title: str, desc: str):
    """Embed merah dengan ikon ❌ → untuk error/peringatan."""
    return discord.Embed(
        title=f"❌ {title}",
        description=desc,
        color=discord.Color.red()
    )

def ok_embed(title: str, desc: str):
    """Embed hijau dengan ikon ✅ → untuk konfirmasi/sukses."""
    return discord.Embed(
        title=f"✅ {title}",
        description=desc,
        color=discord.Color.green()
    )

def warn_embed(title: str, desc: str):
    """Embed kuning dengan ikon ⚠️ → untuk warning/peringatan ringan."""
    return discord.Embed(
        title=f"⚠️ {title}",
        description=desc,
        color=discord.Color.gold()
    )

def book_embed(title: str, desc: str):
    """Embed ungu dengan ikon 📚 → khusus untuk Wiki/Lore."""
    return discord.Embed(
        title=f"📚 {title}",
        description=desc,
        color=discord.Color.purple()
    )
