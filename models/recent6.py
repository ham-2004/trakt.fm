import discord
from discord.ext import commands
import os
import json

from tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster
from trakt_api import get_recent_history
from utils.image_grid import create_titled_image_grid
from utils.trakt_utils import save_recent_trakt_data
from database.database import count_total_scrobbles

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


class Recent6Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="t6")
    async def trakt_six_recent(self, ctx):
        """Show 6 recent movies in a grid image with overlaid titles"""
        users = load_users()
        user_id = str(ctx.author.id)

        if user_id not in users:
            embed = discord.Embed(
                title="📌 Trakt Account Not Registered",
                description=(
                    "You haven't linked your Trakt account yet.\n\n"
                    "**Register:** Use `/tset <username>` to link your account.\n"
                    "**Need an account?** [Sign up here](https://trakt.tv/signup)"
                ),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        username = users[user_id]
        history = get_recent_history(username, media_type="movies", per_page=100)

        if not history:
            await ctx.send("❌ No recent activity found.")
            return

        save_recent_trakt_data(username, history)

        # Gather up to 6 recent movies
        movies = [entry for entry in history if 'movie' in entry][:6]

        if not movies:
            await ctx.send("❌ No recent movies found.")
            return

        # Prepare poster URLs and titles
        grid_data = []
        for entry in movies:
            item = entry["movie"]
            title = item.get("title", "Unknown")
            year = item.get("year", "Unknown")
            full_title = f"{title} ({year})"
            poster_url = item.get("images", {}).get("poster", [None])[0]

            if not poster_url:
                poster_url = get_tmdb_movie_poster(title, year)

            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, full_title))

        # Create grid image
        image_bytes = await create_titled_image_grid(grid_data)

        if not image_bytes:
            await ctx.send("❌ Failed to generate grid image.")
            return

        # Count total scrobbles
        movie_scrobbles, show_scrobbles = count_total_scrobbles(username)
        total_scrobbles = movie_scrobbles + show_scrobbles

        embed = discord.Embed(
            title=f"🎬 Recent Movies for {ctx.author.display_name}",
            color=0x2F3136,
            url=f"https://trakt.tv/users/{username}"
        )
        embed.set_image(url="attachment://grid.webp")
        embed.set_footer(text=f"🎬 Movies: {movie_scrobbles} | 📺 Shows: {show_scrobbles} | 📊 Total: {total_scrobbles}")

        file = discord.File(image_bytes, filename="grid.webp")
        await ctx.send(embed=embed, file=file)


class Recent6CogShow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="t6s")
    async def trakt_six_recent(self, ctx):
        """Show 6 recent shows in a grid image with overlaid titles"""
        users = load_users()
        user_id = str(ctx.author.id)

        if user_id not in users:
            embed = discord.Embed(
                title="📌 Trakt Account Not Registered",
                description=(
                    "You haven't linked your Trakt account yet.\n\n"
                    "**Register:** Use `tset <username>` to link your account.\n"
                    "**Need an account?** [Sign up here](https://trakt.tv/signup)"
                ),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        username = users[user_id]
        history = get_recent_history(username, media_type="shows", per_page=100)

        if not history:
            await ctx.send("❌ No recent activity found.")
            return

        save_recent_trakt_data(username, history)

        # Gather up to 6 recent shows
        seen_titles = set()
        shows = []

        for entry in history:
            if 'show' in entry:
                show = entry['show']
                title = show.get('title')
                year = show.get('year')
                key = f"{title}_{year}"

                if key not in seen_titles:
                    seen_titles.add(key)
                    shows.append(show)

                if len(shows) == 6:
                    break

        if not shows:
            await ctx.send("❌ No recent shows found.")
            return

        # Prepare poster URLs and titles
        grid_data = []
        for show in shows:
            title = show.get("title", "Unknown")
            year = show.get("year", "Unknown")
            full_title = f"{title} ({year})"
            poster_url = show.get("images", {}).get("poster", [None])[0]

            if not poster_url:
                poster_url = get_tmdb_show_poster(title, year)
            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, full_title))

        # Create grid image
        image_bytes = await create_titled_image_grid(grid_data)

        if not image_bytes:
            await ctx.send("❌ Failed to generate grid image.")
            return

        # Count total scrobbles
        movie_scrobbles, show_scrobbles = count_total_scrobbles(username)
        total_scrobbles = movie_scrobbles + show_scrobbles

        embed = discord.Embed(
            title=f"🎬 Recent Shows for {ctx.author.display_name}",
            color=0x2F3136,
            url=f"https://trakt.tv/users/{username}"
        )
        embed.set_image(url="attachment://grid.webp")
        embed.set_footer(text=f"🎬 Movies: {movie_scrobbles} | 📺 Shows: {show_scrobbles} | 📊 Total: {total_scrobbles}")


        file = discord.File(image_bytes, filename="grid.webp")
        await ctx.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Recent6Cog(bot))
    await bot.add_cog(Recent6CogShow(bot))