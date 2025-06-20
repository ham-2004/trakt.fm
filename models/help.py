import discord
from discord.ext import commands
import os

class HelpCog(commands.Cog):  # Optional: rename class too
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):  # Renamed for clarity
        prefix = os.getenv("BOT_PREFIX", "!")
        embed = discord.Embed(
            title="🎬 trakt.fm Bot Commands",
            description=(
                f"`{prefix}help` — Show this help message"
                f"`{prefix}tset <username>` — Link your Trakt username\n"
                f"`{prefix}tr` — Show your most recently watched item\n"
                f"`{prefix}t6` — Show your six recently watched movies\n"
                f"`{prefix}t6s` — Show your six recently watched shows\n"
                f"`{prefix}tw` — Show your Trakt watchlist\n"
            ),
            color=0x1DB954
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
