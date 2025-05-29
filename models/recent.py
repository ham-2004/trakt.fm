import discord
import json
import os
from discord.ext import commands
from datetime import datetime

today_str = datetime.now().date().isoformat()

from tmbd_api import get_tmdb_movie_poster
from trakt_api import get_recent_activity

USER_DATA_FILE = "users.json"
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
FALLBACK_POSTER = "https://i.imgur.com/Z2MYNbj.png"
IMAGE_CACHE_DIR = "image_cache"

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

class RecentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tr")
    async def trakt_recent(self, ctx):
        users = load_users()
        user_id = str(ctx.author.id)
        if user_id not in users:
            await ctx.send("❌ Please register first using `trakt_register <username>`")
            return

        username = users[user_id]
        history = get_recent_activity(username)
        if not history:
            await ctx.send("❌ No recent activity found.")
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

            binge_count = sum(1 for e in history if 'show' in e and e.get('watched_at', '').startswith(today_str))
            if binge_count > 1:
                embed.set_footer(text=f"🔥 {binge_count} episodes watched today — binge mode!")

        embed.set_thumbnail(url=poster_url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RecentCog(bot))
