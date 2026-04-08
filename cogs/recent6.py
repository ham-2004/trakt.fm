import discord
from discord.ext import commands

# 1. Cleaned up imports
from config import FALLBACK_POSTER
from utils.embeds import error_embed, loading_embed
from database.database import get_user, count_total_scrobbles

# Make sure these are being imported from your correct files!
from api.tmbd_api import get_tmdb_movie_poster, get_tmdb_show_poster
from api.trakt_api import get_recent_history
from utils.image_grid import create_titled_image_grid


class Recent6Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 2. Converted to Hybrid Command & applied Cooldown
    @commands.hybrid_command(name="t6", description="Show 6 recent movies in a grid image")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def trakt_six_recent(self, ctx):
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

        # 3. Send a loading message (Image grids take a few seconds to build!)
        loading_msg = await ctx.send(embed=loading_embed("Fetching movies and generating grid..."))

        history = await get_recent_history(username, media_type="movies", per_page=100)

        if not history:
            await loading_msg.edit(embed=error_embed("No recent activity found."))
            return

        # Gather up to 6 recent movies
        movies = [entry for entry in history if 'movie' in entry][:6]

        if not movies:
            await loading_msg.edit(embed=error_embed("No recent movies found."))
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
                # 4. Awaiting TMDB if you've updated it to async!
                poster_url = await get_tmdb_movie_poster(title, year)

            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, full_title))

        # Create grid image
        image_bytes = await create_titled_image_grid(grid_data)

        if not image_bytes:
            await loading_msg.edit(embed=error_embed("Failed to generate grid image."))
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

        # 5. Delete the loading message and send the real grid!
        await loading_msg.delete()
        await ctx.send(embed=embed, file=file)


class Recent6CogShow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 6. Converted to Hybrid Command & applied Cooldown
    @commands.hybrid_command(name="t6s", description="Show 6 recent shows in a grid image")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def trakt_six_recent_shows(self, ctx):

        # 7. Replaced load_users() JSON logic with the new database logic
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

        loading_msg = await ctx.send(embed=loading_embed("Fetching shows and generating grid..."))

        # 8. Added 'await' to the history fetch
        history = await get_recent_history(username, media_type="shows", per_page=100)

        if not history:
            await loading_msg.edit(embed=error_embed("No recent activity found."))
            return

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
            await loading_msg.edit(embed=error_embed("No recent shows found."))
            return

        # Prepare poster URLs and titles
        grid_data = []
        for show in shows:
            title = show.get("title", "Unknown")
            year = show.get("year", "Unknown")
            full_title = f"{title} ({year})"
            poster_url = show.get("images", {}).get("poster", [None])[0]

            if not poster_url:
                poster_url = await get_tmdb_show_poster(title, year)
            if not poster_url:
                poster_url = FALLBACK_POSTER
            elif not poster_url.startswith("http"):
                poster_url = "https://" + poster_url

            grid_data.append((poster_url, full_title))

        # Create grid image
        image_bytes = await create_titled_image_grid(grid_data)

        if not image_bytes:
            await loading_msg.edit(embed=error_embed("Failed to generate grid image."))
            return

        # Count total scrobbles
        movie_scrobbles, show_scrobbles = count_total_scrobbles(username)
        total_scrobbles = movie_scrobbles + show_scrobbles

        embed = discord.Embed(
            title=f"📺 Recent Shows for {ctx.author.display_name}",
            color=0x2F3136,
            url=f"https://trakt.tv/users/{username}"
        )
        embed.set_image(url="attachment://grid.webp")
        embed.set_footer(text=f"🎬 Movies: {movie_scrobbles} | 📺 Shows: {show_scrobbles} | 📊 Total: {total_scrobbles}")

        file = discord.File(image_bytes, filename="grid.webp")

        await loading_msg.delete()
        await ctx.send(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(Recent6Cog(bot))
    await bot.add_cog(Recent6CogShow(bot))