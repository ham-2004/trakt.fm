import discord
from discord.ext import commands
from datetime import datetime

from config import TRAKT_API_KEY, FALLBACK_POSTER, IMAGE_CACHE_DIR
from utils.embeds import error_embed
from api.tmbd_api import get_tmdb_movie_poster
from api.trakt_api import get_recent_activity
from database.database import get_user

class RecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 2. Renamed back to "tr" since this code only fetches 1 item, not 6
    @commands.hybrid_command(name="tr", description="Show your most recently watched item")
    async def trakt_recent(self, ctx):

        # 3. Clean database lookup
        username = get_user(ctx.author.id)

        if not username:
            # 4. Using our new standardized error embed!
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

        # fallback to TMDb if Trakt doesn't return one
        if not poster_url:
            title = item.get('title', 'Unknown')
            year = item.get('year', 'Unknown')
            # Warning: If you update tmbd_api.py to be async, remember to add 'await' here!
            poster_url = get_tmdb_movie_poster(title, year)

        # fallback to static image if all else fails
        if not poster_url:
            poster_url = FALLBACK_POSTER
        else:
            # Ensure full URL format
            if not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

        title = item.get('title', 'Unknown')
        year = item.get('year', 'Unknown')
        date = first_entry.get('watched_at', '').split('T')[0]

        embed = discord.Embed(
            title=f"📽️ Recent activity by {ctx.author.display_name}",
            url=f"https://trakt.tv/users/{username}",
            color=0x1DB954
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

            today = datetime.utcnow().date()
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