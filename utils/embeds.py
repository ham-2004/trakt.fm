import discord

def error_embed(description: str, title: str = "Error") -> discord.Embed:
    """Returns a standardized red error embed."""
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red()
    )

def success_embed(description: str, title: str = "Success") -> discord.Embed:
    """Returns a standardized green success embed."""
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x1DB954  # Trakt/Spotify Green
    )

def loading_embed(description: str) -> discord.Embed:
    """Returns a standardized loading embed."""
    return discord.Embed(
        title="🔄 Please Wait...",
        description=description,
        color=discord.Color.gold()
    )