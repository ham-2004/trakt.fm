import discord
from discord.ext import commands
from discord import app_commands  # <-- 1. Added the correct import!
from datetime import datetime, timezone

from config import TRAKT_API_KEY, FALLBACK_POSTER, IMAGE_CACHE_DIR
from utils.embeds import error_embed
from api.tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster
from api.trakt_api import get_recent_activity
from database.database import get_user


class RecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tr", description="Show your recent Trakt activity")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trakt_recent(self, ctx):

        username = get_user(ctx.author.id)

        if not username:
            await ctx.send(embed=error_embed(
                title="Trakt Account Not Registered",
                description=(
                    "You haven't linked your Trakt account yet.\n\n"
                    "**Register:** Use `/tset <username>` to link your account.\n"
                    "**Need an account?** [Sign up here](https://trakt.tv/signup)"
                )
            ))
            return

        history = await get_recent_activity(username)
        if not history:
            await ctx.send(embed=error_embed("No recent activity found."))
            return

        first_entry = history[0]
        item = first_entry.get('movie') or first_entry.get('show')
        is_movie = 'movie' in first_entry
        images = item.get('images', {})
        poster_url = images.get("poster", [None])[0]

        if not poster_url:
            title = item.get('title', 'Unknown')
            year = item.get('year', 'Unknown')

            if is_movie:
                poster_url = await get_tmdb_movie_poster(title, year)
            else:
                poster_url = await get_tmdb_show_poster(title, year)

        if not poster_url:
            poster_url = FALLBACK_POSTER
        else:
            if not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

        title = item.get('title', 'Unknown')
        year = item.get('year', 'Unknown')
        date = first_entry.get('watched_at', '').split('T')[0]

        embed = discord.Embed(
            title=f"📽️ Recent activity by {ctx.author.display_name}",
            url=f"https://trakt.tv/users/{username}",
            color=0xED1C24
        )

        if is_movie:
            embed.add_field(
                name=f"{title} ({year})",
                value=f"🎬 Watched on {date}",
                inline=False
            )
        else:
            episode = first_entry.get('episode', {})
            season = episode.get('season', 0)
            number = episode.get('number', 0)
            ep_title = episode.get('title', 'Unknown Episode')

            embed.add_field(
                name=f"{title} ({year})",
                value=f"🎞️ {ep_title} — S{season:02}E{number:02}\n📅 Watched on {date}",
                inline=False
            )

            today = datetime.now(timezone.utc).date()
            binge_count = sum(
                1 for e in history
                if 'show' in e and
                datetime.fromisoformat(e.get('watched_at', '').replace('Z', '+00:00')).date() == today
            )
            if binge_count > 1:
                embed.set_footer(text=f"🔥 {binge_count} episodes watched today — binge mode!")

        embed.set_thumbnail(url=poster_url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RecentCog(bot))